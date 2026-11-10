import type { EngineInterface, Register } from 'claude-code'

// Mostra "foco ativo N/M" na status line enquanto a demanda tiver itens pendentes.
async function atualizar($: EngineInterface) {
  try {
    const { stdout } = await $.process.run(
      ['python3', `${$.plugin.root}/skills/foco/scripts/foco.py`, 'status'],
      { timeoutMs: 5000 },
    )
    $.ui.status(stdout.trim() || undefined)
  } catch {
    $.ui.status(undefined)
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    await atualizar($)
    return r
  })

  on('prompt.submit', async ($, e, next) => {
    const r = await next(e)
    await atualizar($)
    return r
  }).catch(($, e, next) => next(e))

  // definir, feito, adiar e limpar rodam pelo Bash
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const r = await next(e)
    if (e.command.includes('foco.py')) await atualizar($)
    return r
  }).catch(($, e, next) => next(e))
}
