// Botão "Auditoria de validade" (favorito do Chrome). Fonte legível; o favorito é gerado por
// scripts/gerar_botao.py, que troca __URL__ e __CHAVE__ e compacta este arquivo numa linha "javascript:".
//
// O que faz, com o Belle aberto e logado:
// 1. pede à planilha-ponte (Apps Script) os próximos planos da fila;
// 2. para cada plano, consulta a mesma Auditoria da tela Venda de Planos > plano > Auditoria,
//    usando a sessão de quem clicou (o token fica no próprio navegador e não é enviado para fora do Belle);
// 3. guarda só as operações que falam de validade ("Alterou Validade") e manda para a planilha-ponte.
(async () => {
  const URL_PONTE = '__URL__';
  const CHAVE = '__CHAVE__';
  const LOTE_ENVIO = 40;

  if (!/(^|\.)bellesoftware\.com\.br$/.test(location.hostname)) {
    alert('Abra o Belle (app.bellesoftware.com.br), faça login e clique no favorito de novo.');
    return;
  }
  const cookie = document.cookie.split(';').map((c) => c.trim()).find((c) => c.startsWith('token_0='));
  if (!cookie) {
    alert('Não achei a sessão do Belle. Faça login e clique no favorito de novo.');
    return;
  }
  const token = decodeURIComponent(cookie.slice('token_0='.length));

  const painel = document.createElement('div');
  painel.style.cssText = 'position:fixed;z-index:2147483647;right:16px;bottom:16px;max-width:340px;padding:14px 16px;' +
    'background:#12343b;color:#fff;font:14px/1.4 system-ui,sans-serif;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.3)';
  const msg = (t) => { painel.textContent = t; };
  document.body.appendChild(painel);
  msg('Auditoria de validade: buscando a fila…');

  const hoje = new Date();
  const amanha = new Date(hoje.getTime() + 86400000);
  const dia = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  const consultadoEm = dia(hoje);

  let fila;
  try {
    const r = await fetch(`${URL_PONTE}?acao=pendentes&k=${encodeURIComponent(CHAVE)}`);
    const j = await r.json();
    if (j.erro) throw new Error(j.erro);
    fila = j.pendentes || [];
  } catch (e) {
    msg(`Não consegui ler a fila (${e.message}). Tente de novo mais tarde.`);
    return;
  }
  if (!fila.length) {
    msg('Auditoria de validade: nada na fila hoje. Obrigado!');
    setTimeout(() => painel.remove(), 6000);
    return;
  }

  // Acha o campo pelo nome, sem depender da grafia exata (a tela usa dt, hora, usu, acao e detalhes).
  const campo = (o, ...nomes) => {
    for (const n of nomes) if (o[n] != null && o[n] !== '') return String(o[n]);
    const k = Object.keys(o).find((k) => nomes.some((n) => k.toLowerCase().includes(n)));
    return k ? String(o[k]) : '';
  };

  const enviar = async (consultas) => {
    const corpo = JSON.stringify({k: CHAVE, acao: 'respostas', consultas});
    try {
      await fetch(URL_PONTE, {method: 'POST', body: corpo});
    } catch (e) {
      await fetch(URL_PONTE, {method: 'POST', body: corpo, mode: 'no-cors'});
    }
  };

  let pendentesEnvio = [];
  let comAlteracao = 0;
  let erros = 0;
  let parou = false;
  for (let i = 0; i < fila.length; i++) {
    const p = fila[i];
    msg(`Auditoria de validade: consultando ${i + 1} de ${fila.length} planos… (não feche esta aba)`);
    const q = new URLSearchParams({
      codOrcamento: p.plano, dataIni: `${p.venda}T03:00:00.000Z`, dataFim: `${dia(amanha)}T03:00:00.000Z`,
      limit: '', offset: '0', estabGeral: p.estab,
    });
    try {
      const r = await fetch(`/api/release/controller/Plano/v1.0/listar_auditoria_venda_plano?${q}`,
                            {headers: {authorization: token}});
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      const regs = Array.isArray(j) ? j : (j.dados || j.data || j.registros || j.result || []);
      const ops = regs
        .filter((o) => /validade/i.test(`${campo(o, 'acao', 'operacao')} ${campo(o, 'detalhes', 'descricao')}`))
        .map((o) => {
          const {ip, ...semIp} = o;
          return {
            data: campo(o, 'dt', 'data'), hora: campo(o, 'hora', 'hr'), usuario: campo(o, 'usu', 'usuario', 'nome'),
            acao: campo(o, 'acao', 'operacao'), detalhes: campo(o, 'detalhes', 'descricao'), bruto: JSON.stringify(semIp),
          };
        });
      if (ops.length) comAlteracao++;
      pendentesEnvio.push({plano: p.plano, estab: p.estab, consultado_em: consultadoEm, operacoes: ops});
    } catch (e) {
      erros++;
      if (erros >= 5 && erros > i / 2) {
        parou = true;
        msg(`O Belle recusou as consultas (${e.message}). Confira se está logado e tente de novo.`);
        break;
      }
    }
    if (pendentesEnvio.length >= LOTE_ENVIO) {
      await enviar(pendentesEnvio);
      pendentesEnvio = [];
    }
    await new Promise((ok) => setTimeout(ok, 150));
  }
  if (pendentesEnvio.length) await enviar(pendentesEnvio);
  if (parou) return;
  msg(`Auditoria de validade: pronto. ${fila.length - erros} planos consultados, ${comAlteracao} com alteração de validade` +
      (erros ? `, ${erros} com erro (ficam para a próxima)` : '') + '. O painel atualiza na próxima rotina diária.');
  setTimeout(() => painel.remove(), 15000);
})();
