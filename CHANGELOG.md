# Changelog

## 1.0.0 — 10/11/2026

- Skill `foco`: registra a demanda como lista de itens fiel ao pedido, com escopo de arquivos opcional, e anota ideias fora do escopo para o final.
- `scripts/foco.py`: `definir`, `feito`, `adiar`, `fora`, `mostrar`, `retomar` e `limpar`; estado por projeto em `~/.claude/foco/`.
- Hooks:
  - `UserPromptSubmit`: lembra os itens pendentes a cada pedido;
  - `PostToolUse`: avisa edição fora do escopo declarado;
  - `Stop`: não deixa encerrar com item pendente (bloqueia uma vez).
- Testes e CI.
