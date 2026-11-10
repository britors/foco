#!/usr/bin/env python3
"""Mantém o foco na demanda: lista do que foi pedido, escopo de arquivos e ideias fora do escopo.

Comandos para o Claude, rodados na pasta do projeto:
    foco.py definir "item" ["item" ...] [--titulo T] [--escopo GLOB ...]
    foco.py feito N [N ...]
    foco.py adiar N "motivo"
    foco.py fora "ideia que ficou fora do escopo"
    foco.py mostrar
    foco.py retomar        # assume a demanda pendente de outra sessão
    foco.py limpar
    foco.py status         # uma linha para a status line, vazia sem pendentes

Hooks do plugin (lêem o JSON do Claude Code na entrada padrão):
    foco.py hook-lembrete  # UserPromptSubmit: lembra os itens pendentes
    foco.py hook-escopo    # PostToolUse: avisa edição fora do escopo
    foco.py hook-parar     # Stop: não deixa encerrar com item pendente

O estado fica em ~/.claude/foco/, um arquivo por projeto.
"""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PASTA = Path.home() / ".claude" / "foco"
PROJETOS = Path.home() / ".claude" / "projects"
SCRIPT = Path(__file__).resolve()


def raiz(cwd):
    r = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(r.stdout.strip()) if r.returncode == 0 else Path(cwd).resolve()


def chave(projeto):
    return re.sub(r"[^A-Za-z0-9]", "-", str(projeto))


def cwd_inicial(transcricao, padrao):
    """Pasta em que a sessão começou: o primeiro cwd do transcript. O cwd dos hooks segue os `cd` da sessão."""
    try:
        with open(transcricao, encoding="utf-8", errors="replace") as f:
            for linha in f:
                try:
                    cwd = json.loads(linha).get("cwd")
                except (ValueError, AttributeError):
                    continue
                if cwd:
                    return cwd
    except (OSError, TypeError):
        pass
    return padrao


def cwd_da_sessao(cwd):
    """Pasta em que a sessão ativa começou, para os comandos rodados de uma subpasta após `cd`.

    Procura em ~/.claude/projects a pasta atual e as de cima; vence a que tem o transcript mais recente.
    """
    cwd = Path(cwd).resolve()
    melhor = None
    for pasta in (cwd, *cwd.parents):
        for t in (PROJETOS / chave(pasta)).glob("*.jsonl"):
            mt = t.stat().st_mtime
            if melhor is None or mt > melhor[0]:
                melhor = (mt, pasta)
    return melhor[1] if melhor else cwd


def ler(projeto):
    try:
        return json.loads((PASTA / f"{chave(projeto)}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def gravar(projeto, estado):
    PASTA.mkdir(parents=True, exist_ok=True)
    destino = PASTA / f"{chave(projeto)}.json"
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, destino)


def sessao_atual(projeto):
    try:
        return (PASTA / f"{chave(projeto)}.sessao").read_text().strip() or None
    except OSError:
        return None


def pendentes(estado):
    return [(i, it) for i, it in enumerate(estado["itens"], 1) if it["estado"] == "pendente"]


def resumo(estado):
    linhas = [f"Demanda: {estado['titulo']}" if estado.get("titulo") else "Demanda:"]
    marcas = {"pendente": "[ ]", "feito": "[x]", "adiado": "[~]"}
    for i, it in enumerate(estado["itens"], 1):
        motivo = f" (adiado: {it['motivo']})" if it.get("motivo") else ""
        linhas.append(f"{marcas[it['estado']]} {i}. {it['texto']}{motivo}")
    if estado.get("escopo"):
        linhas.append("Escopo de arquivos: " + ", ".join(estado["escopo"]))
    if estado.get("fora"):
        linhas.append("Fora do escopo, para depois:")
        linhas += [f"- {f}" for f in estado["fora"]]
    return "\n".join(linhas)


# Comandos

def cmd(argv):
    ap = argparse.ArgumentParser(prog="foco.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="comando", required=True)
    d = sub.add_parser("definir", help="registra a demanda, um item por argumento")
    d.add_argument("itens", nargs="+")
    d.add_argument("--titulo", default="")
    d.add_argument("--escopo", nargs="*", default=[], help="globs dos arquivos que a demanda pode tocar")
    f = sub.add_parser("feito", help="marca itens como feitos")
    f.add_argument("numeros", nargs="+", type=int)
    a = sub.add_parser("adiar", help="adia um item, com o motivo")
    a.add_argument("numero", type=int)
    a.add_argument("motivo")
    o = sub.add_parser("fora", help="anota uma ideia que ficou fora do escopo")
    o.add_argument("ideia")
    for nome in ("mostrar", "retomar", "limpar", "status"):
        sub.add_parser(nome)
    args = ap.parse_args(argv)

    projeto = raiz(cwd_da_sessao(os.getcwd()))
    estado = ler(projeto)
    if args.comando == "status":
        if estado and pendentes(estado):
            feitos = sum(it["estado"] != "pendente" for it in estado["itens"])
            print(f"foco ativo {feitos}/{len(estado['itens'])}")
        return 0
    if args.comando == "definir":
        estado = {
            "sessao": sessao_atual(projeto),
            "titulo": args.titulo,
            "itens": [{"texto": t, "estado": "pendente"} for t in args.itens],
            "escopo": args.escopo,
            "fora": [],
            "criado_em": int(time.time()),
        }
    elif estado is None:
        sys.exit("Nenhuma demanda registrada neste projeto. Use: foco.py definir \"item\" ...")
    elif args.comando in ("feito", "adiar"):
        numeros = args.numeros if args.comando == "feito" else [args.numero]
        for n in numeros:
            if not 1 <= n <= len(estado["itens"]):
                sys.exit(f"Item {n} não existe; a demanda tem {len(estado['itens'])} itens.")
            estado["itens"][n - 1]["estado"] = "feito" if args.comando == "feito" else "adiado"
            if args.comando == "adiar":
                estado["itens"][n - 1]["motivo"] = args.motivo
    elif args.comando == "fora":
        estado["fora"].append(args.ideia)
    elif args.comando == "retomar":
        estado["sessao"] = sessao_atual(projeto)
    elif args.comando == "limpar":
        (PASTA / f"{chave(projeto)}.json").unlink(missing_ok=True)
        print("Demanda apagada.")
        return 0
    if args.comando != "mostrar":
        gravar(projeto, estado)
    print(resumo(estado))
    if not pendentes(estado):
        print("\nTudo concluído ou adiado. Mostre ao usuário o que foi feito e o que ficou fora do escopo.")
    return 0


# Hooks

def hook(nome):
    try:
        dados = json.load(sys.stdin)
    except ValueError:
        return 0
    projeto = raiz(cwd_inicial(dados.get("transcript_path"), dados.get("cwd") or os.getcwd()))
    sid = dados.get("session_id")
    estado = ler(projeto)

    if nome == "hook-lembrete":
        if sid:
            PASTA.mkdir(parents=True, exist_ok=True)
            (PASTA / f"{chave(projeto)}.sessao").write_text(sid)
        if not estado or not pendentes(estado):
            return 0
        if estado.get("sessao") != sid:
            print(f"[foco] Há uma demanda com {len(pendentes(estado))} itens pendentes de outra sessão neste projeto. "
                  f"Se o pedido atual a continua, rode `python3 {SCRIPT} retomar`; senão, ignore.")
            return 0
        itens = "; ".join(f"{i}) {it['texto']}" for i, it in pendentes(estado))
        print(f"[foco] Pendentes: {itens}. Trabalhe só no que foi pedido; anote outras ideias com "
              f"`python3 {SCRIPT} fora \"...\"` e marque o que concluir com `feito N`.")
        return 0

    if not estado or estado.get("sessao") != sid:
        return 0

    if nome == "hook-escopo":
        arquivo = (dados.get("tool_input") or {}).get("file_path") or (dados.get("tool_input") or {}).get("notebook_path")
        if not arquivo or not estado.get("escopo"):
            return 0
        try:
            relativo = str(Path(arquivo).resolve().relative_to(projeto))
        except ValueError:
            relativo = arquivo
        if any(fnmatch.fnmatch(relativo, g) for g in estado["escopo"]):
            return 0
        print(f"[foco] {relativo} está fora do escopo declarado ({', '.join(estado['escopo'])}). "
              f"Se não faz parte da demanda, desfaça a mudança e anote a ideia com `python3 {SCRIPT} fora \"...\"`; "
              f"se faz, pergunte ao usuário antes de ampliar o escopo.", file=sys.stderr)
        return 2

    if nome == "hook-parar":
        if dados.get("stop_hook_active") or not pendentes(estado):
            return 0
        itens = "; ".join(f"{i}) {it['texto']}" for i, it in pendentes(estado))
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"[foco] Ainda há itens pendentes da demanda: {itens}. Conclua-os e marque com "
                f"`python3 {SCRIPT} feito N`, ou adie com `adiar N \"motivo\"`. Se você só precisa de uma "
                "resposta do usuário, faça a pergunta e encerre de novo."
            ),
        }, ensure_ascii=False))
        return 0
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("hook-"):
        sys.exit(hook(sys.argv[1]))
    sys.exit(cmd(sys.argv[1:]))
