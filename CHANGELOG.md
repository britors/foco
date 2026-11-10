# Changelog

## 1.1.2 — 10/11/2026

- O aviso de edição fora do escopo só vale enquanto a demanda tiver itens pendentes. Antes, o escopo de uma demanda já concluída continuava barrando as edições do pedido seguinte.

## 1.1.1 — 10/11/2026

- A demanda fica presa à pasta em que a sessão começou, mesmo que ela tenha feito `cd` para outro repositório. Antes, os hooks e os comandos rodados após o `cd` procuravam a demanda no repositório de destino e não a achavam.

## 1.1.0 — 10/11/2026

- Status line: `hooks/status.ts` mostra `foco ativo N/M` enquanto a demanda tiver itens pendentes, e some quando tudo é concluído ou adiado.
- `scripts/foco.py status`: a linha da status line, vazia sem pendentes.

## 1.0.0 — 10/11/2026

- Skill `foco`: registra a demanda como lista de itens fiel ao pedido, com escopo de arquivos opcional, e anota ideias fora do escopo para o final.
- `scripts/foco.py`: `definir`, `feito`, `adiar`, `fora`, `mostrar`, `retomar` e `limpar`; estado por projeto em `~/.claude/foco/`.
- Hooks:
  - `UserPromptSubmit`: lembra os itens pendentes a cada pedido;
  - `PostToolUse`: avisa edição fora do escopo declarado;
  - `Stop`: não deixa encerrar com item pendente (bloqueia uma vez).
- Testes e CI.
