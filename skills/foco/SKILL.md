---
name: foco
description: Esta skill deve ser usada no início de qualquer pedido com mais de um item ou que mexa em vários arquivos, e quando o usuário disser "foco", "não saia do escopo", "só o que eu pedi", "sem inventar" ou "termine tudo o que pedi". This skill should be used at the start of any request with more than one item or touching several files, and when the user says "focus", "stay in scope", "only what I asked" or "finish everything I asked".
---

# Foco na demanda

Objetivo: fazer **tudo** o que foi pedido e **só** o que foi pedido. Ideias boas que fogem do pedido não são executadas: são anotadas e mostradas no final.

O script fica em `scripts/foco.py`, ao lado deste SKILL.md. Use o caminho absoluto e rode-o na pasta do projeto.

## Modo foco: `/foco on` e `/foco off`

Se a skill foi chamada com `on` ou `off`, o usuário está ligando ou desligando o **modo foco** desta sessão. O hook já aplicou a troca: rode `foco.py modo` e diga ao usuário em que estado ficou. Não registre demanda nesse pedido. Se `on` não tiver pegado, rode `foco.py ligar`.

Com o modo ligado, **todo** pedido da sessão segue esta skill: registre a demanda antes de agir, mesmo com um item só.

O modo foco **só o usuário desliga**, digitando `/foco off`. Você não desliga: não há comando para isso, não mexa em `~/.claude/foco` e não peça para desligar só porque o trabalho ficou difícil.

## 1. Registrar a demanda

Antes de agir, transforme o pedido numa lista de itens e registre:

```
python3 <pasta desta skill>/scripts/foco.py definir "item 1" "item 2" --titulo "<resumo do pedido>" [--escopo "src/api/**" "tests/**"]
```

- Cada item é algo que o usuário **pediu**, com as palavras dele sempre que possível. Não acrescente itens que ele não pediu, como refatorar, atualizar dependências, melhorar nomes ou criar testes extras.
- Itens implícitos e necessários contam, por exemplo "rodar os testes" quando o pedido muda código testado. Na dúvida, pergunte.
- Use `--escopo` quando o pedido deixa claro quais arquivos ou pastas mudam. Sem escopo, não há aviso por arquivo.
- Se o pedido for ambíguo, pergunte **antes** de registrar.

## 2. Trabalhar

- Siga os itens na ordem. Ao concluir e conferir um item, marque: `foco.py feito N`.
- Viu algo que valeria fazer, mas ninguém pediu (um bug ao lado, um nome ruim, uma melhoria)? **Não faça.** Anote: `foco.py fora "descrição"`.
- Um item não pode ser feito agora (falta acesso, depende do usuário, bloqueado)? `foco.py adiar N "motivo"`.
- Se o hook avisar que um arquivo está fora do escopo, desfaça a mudança ou pergunte ao usuário se o escopo deve crescer.
- O usuário mudou o pedido no meio? Registre de novo com `definir`.

## 3. Encerrar

Antes da resposta final, rode `foco.py mostrar` e confira cada item. Na resposta:

- o que foi feito, item por item;
- o que foi adiado e por quê;
- a lista do que ficou **fora do escopo**, como sugestão para o usuário decidir.

Se houver item pendente, o hook de encerramento pede para concluir, adiar ou perguntar ao usuário.

## Outros comandos

- `foco.py mostrar`: lista a demanda e o estado de cada item.
- `foco.py retomar`: assume a demanda pendente deixada por outra sessão neste projeto.
- `foco.py limpar`: apaga a demanda do projeto.
