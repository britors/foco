---
name: setup
description: Configura se as novas sessões começam com o modo foco ligado ou desligado. Use quando o usuário digitar /foco:setup. Configures whether new sessions start with focus mode on or off.
disable-model-invocation: true
---

# Configurar o foco

O script fica em `../foco/scripts/foco.py`, a partir da pasta deste SKILL.md. Use o caminho absoluto.

1. Rode `python3 <script> config` e mostre ao usuário a configuração atual.
2. Se o usuário já passou `on` ou `off` ao chamar `/foco:setup`, use essa resposta. Senão, pergunte (com a ferramenta de perguntas, se houver) se as novas sessões devem começar com o modo foco ligado, em que todo pedido é registrado como demanda e só o usuário desliga, com `/foco off`, ou desligado, em que o usuário liga quando quiser, com `/foco on`.
3. Grave a resposta com `python3 <script> config on` ou `python3 <script> config off` e confirme o que ficou.

A configuração vale para as sessões que começarem depois. Para a sessão atual, o usuário usa `/foco on` ou `/foco off`.
