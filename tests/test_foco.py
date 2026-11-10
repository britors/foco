"""Testes do foco: comandos e hooks, com HOME e projeto temporários."""

import json
import os
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

    def test_item_inexistente(self):
        self.definir("item")
        r = self.rodar("feito", "5")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Item 5 não existe", r.stderr)


if __name__ == "__main__":
    unittest.main()
