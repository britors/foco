"""Testes do foco: comandos e hooks, com HOME e projeto temporários."""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "foco" / "scripts" / "foco.py"


class Foco(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()
        self.proj = Path(self.tmp.name) / "proj"
        (self.proj / "src").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.proj)], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def rodar(self, *args, entrada=None, cwd=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], input=entrada, capture_output=True, text=True,
            cwd=cwd or self.proj, env={**os.environ, "HOME": str(self.home)},
        )

    def hook(self, nome, sessao="s1", **kv):
        return self.rodar(nome, entrada=json.dumps({"session_id": sessao, "cwd": str(self.proj), **kv}))

    def definir(self, *itens, escopo=()):
        self.hook("hook-lembrete")  # grava a sessão atual, como o Claude Code faz a cada pedido
        args = ["definir", *itens, "--titulo", "pedido"]
        if escopo:
            args += ["--escopo", *escopo]
        r = self.rodar(*args)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_sem_demanda_os_hooks_ficam_quietos(self):
        for nome in ("hook-lembrete", "hook-escopo", "hook-parar"):
            r = self.hook(nome, tool_input={"file_path": str(self.proj / "x.py")})
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""), nome)

    def test_status(self):
        self.assertEqual(self.rodar("status").stdout, "")
        self.definir("corrigir login", "atualizar README")
        self.assertEqual(self.rodar("status").stdout, "foco ativo 0/2\n")
        self.rodar("feito", "1")
        self.assertEqual(self.rodar("status").stdout, "foco ativo 1/2\n")
        self.rodar("adiar", "2", "depois")
        self.assertEqual(self.rodar("status").stdout, "")

    def test_fluxo_completo(self):
        self.definir("corrigir login", "atualizar README")
        r = self.hook("hook-lembrete")
        self.assertIn("1) corrigir login; 2) atualizar README", r.stdout)

        self.rodar("feito", "1")
        self.rodar("fora", "renomear variáveis do módulo de pagamento")
        r = self.rodar("mostrar")
        self.assertIn("[x] 1. corrigir login", r.stdout)
        self.assertIn("[ ] 2. atualizar README", r.stdout)
        self.assertIn("- renomear variáveis do módulo de pagamento", r.stdout)

        r = self.hook("hook-parar")
        self.assertEqual(json.loads(r.stdout)["decision"], "block")
        self.assertIn("2) atualizar README", r.stdout)

        r = self.rodar("adiar", "2", "aguardando o texto do usuário")
        self.assertIn("Tudo concluído ou adiado", r.stdout)
        self.assertEqual(self.hook("hook-parar").stdout, "")
        self.assertEqual(self.hook("hook-lembrete").stdout, "")

    def test_parar_nao_bloqueia_duas_vezes(self):
        self.definir("item")
        r = self.hook("hook-parar", stop_hook_active=True)
        self.assertEqual(r.stdout, "")

    def test_escopo(self):
        self.definir("mexer na api", escopo=["src/*"])
        dentro = self.hook("hook-escopo", tool_input={"file_path": str(self.proj / "src" / "api.py")})
        self.assertEqual(dentro.returncode, 0)
        fora = self.hook("hook-escopo", tool_input={"file_path": str(self.proj / "docs" / "x.md")})
        self.assertEqual(fora.returncode, 2)
        self.assertIn("docs/x.md está fora do escopo", fora.stderr)

    def test_escopo_some_com_a_demanda_concluida(self):
        self.definir("mexer na api", escopo=["src/*"])
        self.rodar("feito", "1")
        r = self.hook("hook-escopo", tool_input={"file_path": str(self.proj / "docs" / "x.md")})
        self.assertEqual((r.returncode, r.stderr), (0, ""))

    def test_sem_escopo_nao_avisa(self):
        self.definir("item")
        r = self.hook("hook-escopo", tool_input={"file_path": str(self.proj / "qualquer.py")})
        self.assertEqual(r.returncode, 0)

    def test_outra_sessao(self):
        self.definir("item antigo")
        r = self.hook("hook-lembrete", sessao="s2")
        self.assertIn("outra sessão", r.stdout)
        self.assertEqual(self.hook("hook-parar", sessao="s2").stdout, "")
        self.rodar("retomar")
        self.assertIn("1) item antigo", self.hook("hook-lembrete", sessao="s2").stdout)

    def test_subpasta_usa_a_raiz_do_projeto(self):
        self.definir("item")
        r = self.rodar("mostrar", cwd=self.proj / "src")
        self.assertIn("1. item", r.stdout)

    def test_cd_para_subrepo_nao_muda_o_projeto(self):
        # Sessão aberta numa pasta sem git que fez `cd` para um repositório dentro dela.
        ws = Path(self.tmp.name) / "ws"
        sub = ws / "sub"
        sub.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(sub)], check=True)
        transcricao = self.home / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(ws)) / "s1.jsonl"
        transcricao.parent.mkdir(parents=True)
        transcricao.write_text(json.dumps({"type": "user", "cwd": str(ws)}) + "\n")
        dados = json.dumps({"session_id": "s1", "cwd": str(sub), "transcript_path": str(transcricao)})
        self.rodar("hook-lembrete", entrada=dados, cwd=sub)
        self.assertEqual(self.rodar("definir", "item", "--escopo", "sub/**", cwd=sub).returncode, 0)
        self.assertIn("1) item", self.rodar("hook-lembrete", entrada=dados, cwd=sub).stdout)
        self.assertIn("1. item", self.rodar("mostrar", cwd=ws).stdout)
        self.assertEqual(self.rodar("feito", "1", cwd=sub).returncode, 0)
        self.assertNotIn("Nenhuma demanda", self.rodar("mostrar", cwd=sub).stdout)
        self.assertFalse((self.home / ".claude" / "foco" / f"{re.sub(r'[^A-Za-z0-9]', '-', str(sub))}.json").exists())

    def test_modo_liga_e_desliga_pelo_pedido_do_usuario(self):
        self.hook("hook-inicio")
        self.assertNotIn("Modo foco ligado", self.hook("hook-lembrete").stdout)
        self.assertIn("Modo foco ligado", self.hook("hook-lembrete", prompt="/foco on").stdout)
        self.assertIn("Modo foco ligado", self.hook("hook-lembrete", prompt="corrija o login").stdout)
        self.assertEqual(self.rodar("status").stdout, "foco ligado\n")
        self.assertIn("ligado", self.rodar("modo").stdout)
        r = self.hook("hook-lembrete", prompt="/foco:foco off")
        self.assertIn("desligou", r.stdout)
        self.assertNotIn("Modo foco ligado", self.hook("hook-lembrete", prompt="outra coisa").stdout)
        self.assertEqual(self.rodar("status").stdout, "")

    def test_cli_nao_desliga_o_modo(self):
        self.hook("hook-lembrete", prompt="/foco on")
        self.assertNotEqual(self.rodar("desligar").returncode, 0)
        # Texto que só menciona o comando não troca o modo.
        self.hook("hook-lembrete", prompt="explique o /foco off")
        self.assertIn("ligado", self.rodar("modo").stdout)
        for entrada in ({"command": "rm -rf ~/.claude/foco"},
                        {"file_path": str(self.home / ".claude" / "foco" / "sessoes" / "s1")}):
            r = self.hook("hook-guarda", tool_input=entrada)
            self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.hook("hook-guarda", tool_input={"command": "ls"}).stdout, "")
        self.hook("hook-lembrete", prompt="/foco off")
        self.assertEqual(self.hook("hook-guarda", tool_input={"command": "rm -rf ~/.claude/foco"}).stdout, "")

    def test_config_define_o_modo_das_sessoes_novas(self):
        self.assertIn("desligado", self.rodar("config").stdout)
        self.assertEqual(self.hook("hook-inicio", sessao="a").stdout, "")
        self.assertIn("ligado", self.rodar("config", "on").stdout)
        self.assertIn("Modo foco ligado", self.hook("hook-inicio", sessao="b").stdout)
        # A sessão que já existia mantém o modo dela.
        self.assertEqual(self.hook("hook-inicio", sessao="a").stdout, "")
        self.hook("hook-lembrete", sessao="b", prompt="/foco off")
        self.assertEqual(self.hook("hook-inicio", sessao="b").stdout, "")

    def test_item_inexistente(self):
        self.definir("item")
        r = self.rodar("feito", "5")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Item 5 não existe", r.stderr)


if __name__ == "__main__":
    unittest.main()
