<p align="center">
  <img src=".claude-plugin/icon.svg" alt="Ícone do foco: um alvo" width="128">
</p>

# foco

[Português](#português) · [English](#english)

## Português

Plugin do [Claude Code](https://claude.com/claude-code) que mantém o Claude **no que foi pedido**: faz tudo o que você pediu, só o que você pediu, e deixa as outras ideias anotadas para você decidir depois.

### O que ele faz

- **Registra a demanda** como uma lista de itens fiel ao pedido, sem itens inventados. Opcionalmente, registra também o escopo de arquivos (`src/api/**`).
- **Lembra os pendentes** a cada pedido seu, numa linha curta (de 50 a 150 tokens).
- **Avisa quando o Claude edita fora do escopo** declarado e pede que ele desfaça a mudança ou pergunte a você.
- **Anota as ideias fora do escopo** (um bug ao lado, uma refatoração tentadora) em vez de executá-las, e mostra a lista no final.
- **Mostra `foco ativo N/M` na status line** enquanto a demanda tiver itens pendentes (N concluídos ou adiados de M).
- **Não deixa encerrar com item pendente:** o Claude conclui o item, adia com motivo ou pergunta a você. Ele bloqueia uma vez só, para não prender a sessão.

Os hooks só agem depois que uma demanda é registrada no projeto ou que o modo foco é ligado. Sem demanda, não fazem nada e não gastam tokens.

### Instalação

No Claude Code 2.1.275 ou mais novo, dentro de uma sessão:

```
/plugin install foco --marketplace britors/foco
```

Em versões anteriores:

```
/plugin marketplace add britors/foco
/plugin install foco@foco
```

Precisa de `python3` no PATH.

### Uso

A skill entra sozinha em pedidos com vários itens, ou quando você diz "foco", "não saia do escopo" ou "só o que eu pedi". O Claude registra a demanda e mostra a lista:

```
Demanda: corrigir o login e documentar
[x] 1. corrigir o erro 500 no login
[ ] 2. atualizar o README com o novo fluxo
Escopo de arquivos: src/auth/*, README.md
Fora do escopo, para depois:
- o módulo de pagamento repete a mesma validação
```

#### Modo foco

`/foco on` liga o modo foco na sessão: a partir daí, **todo** pedido é registrado como demanda antes de o Claude agir, e a status line mostra `foco ligado`. Só você desliga, com `/foco off`; o Claude não tem como desligar o modo, nem mexendo nos arquivos de estado.

`/foco:setup` define se as novas sessões já começam com o modo foco ligado ou desligado. A configuração fica em `~/.claude/foco/config.json`.

Comandos que o Claude usa: `definir`, `feito N`, `adiar N "motivo"`, `fora "ideia"`, `mostrar`, `retomar` (assume a demanda deixada por outra sessão), `limpar`, `status` (a linha da status line), `modo`, `ligar` e `config`. O estado fica em `~/.claude/foco/`, um arquivo por projeto.

### Estrutura

```
.claude-plugin/plugin.json       manifesto
.claude-plugin/marketplace.json  marketplace de um plugin só
skills/foco/SKILL.md             como registrar, trabalhar e encerrar
skills/foco/scripts/foco.py      comandos e hooks
skills/setup/SKILL.md            /foco:setup, o modo das sessões novas
hooks/hooks.json                 SessionStart, UserPromptSubmit, PreToolUse, PostToolUse e Stop
hooks/status.ts                  "foco ativo" na status line
tests/test_foco.py               testes
```

Para rodar os testes: `python3 -m unittest discover -s tests`.

## English

[Claude Code](https://claude.com/claude-code) plugin that keeps Claude **on what you asked**: all of it and only it. Other ideas are written down for you to decide later.

- Records the request as a checklist that stays faithful to it, with an optional file scope.
- Reminds Claude of pending items on each prompt in one short line.
- Warns when Claude edits a file outside the declared scope.
- Logs out-of-scope ideas instead of acting on them, and lists them at the end.
- Shows `foco ativo N/M` in the status line while items are pending.
- Blocks stopping while items are pending, but only once.
- Focus mode: `/foco on` makes every request in the session go through the checklist; only you can turn it off, with `/foco off`. `/foco:setup` sets whether new sessions start with it on.

The hooks do nothing until a request is recorded.

Install:

```
/plugin install foco --marketplace britors/foco
```

On older versions, run `/plugin marketplace add britors/foco` and then `/plugin install foco@foco`.

Usage: say "foco" or "só o que eu pedi" (the skill also starts on its own on requests with several items). Claude records the checklist, marks items as done and lists the out-of-scope ideas at the end.

## Licença / License

[GPL-3.0](LICENSE)
