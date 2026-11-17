// Botão "Auditoria de validade" (favorito do Chrome). Fonte legível; o favorito é gerado por
// scripts/gerar_botao.py, que troca __URL__ e __CHAVE__ e compacta este arquivo numa linha "javascript:".
//
// O que faz, com o Belle aberto e logado:
// 1. pede à planilha-ponte (Apps Script) os próximos planos da fila;
// 2. para cada plano, consulta a mesma Auditoria da tela Venda de Planos > plano > Auditoria,
//    usando a sessão de quem clicou (o token fica no próprio navegador e não é enviado para fora do Belle);
// 3. guarda só as operações que falam de validade ("Alterou Validade") e manda para a planilha-ponte.
// Na primeira consulta testa as formas de chamar a Auditoria (limite, unidade) e segue com a que o Belle aceitar.
(async () => {
  const URL_PONTE = '__URL__';
  const CHAVE = '__CHAVE__';
  const LOTE_ENVIO = 40;
  const UNIDADES = {1: 'Petrópolis', 2: 'Lagoa Nova', 3: 'Capim Macio', 6: 'Norte Shopping'};

  if (!/(^|\.)bellesoftware\.com\.br$/.test(location.hostname)) {
    alert('Abra o Belle (app.bellesoftware.com.br), faça login e clique no favorito de novo.');
    return;
  }
  // Sessão aberta nesta aba: /u/<n>/... usa o cookie token_<n> e a unidade guardada em sessao_<n>.
  const sessao = (location.pathname.match(/\/u\/(\d+)/) || [])[1] || '0';
  const cookie = document.cookie.split(';').map((c) => c.trim()).find((c) => c.startsWith(`token_${sessao}=`));
  if (!cookie) {
    alert('Não achei a sessão do Belle. Faça login e clique no favorito de novo.');
    return;
  }
  const token = decodeURIComponent(cookie.slice(`token_${sessao}=`.length));
  let estabSessao = '';
  try {
    const s = localStorage.getItem(`sessao_${sessao}`);
    const o = s && s.trim().startsWith('{') ? JSON.parse(s) : null;
    estabSessao = String((o && (o.codEstab ?? o.value?.codEstab)) || '');
  } catch (e) { /* segue sem a unidade da sessão */ }

  const painel = document.createElement('div');
  painel.style.cssText = 'position:fixed;z-index:2147483647;right:16px;bottom:16px;max-width:420px;padding:14px 16px;' +
    'background:#12343b;color:#fff;font:14px/1.4 system-ui,sans-serif;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.3);' +
    'white-space:pre-wrap;word-break:break-word;max-height:70vh;overflow:auto';
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

  // A data da venda chega como AAAA-MM-DD; se a planilha tiver convertido em data, normaliza.
  const diaVenda = (v) => {
    const m = String(v).match(/^'?(\d{4}-\d{2}-\d{2})/);
    if (m) return m[1];
    const d = new Date(v);
    return isNaN(d) ? '' : dia(d);
  };
  // Acha o campo pelo nome, sem depender da grafia exata (a tela usa dt, hora, usu, acao e detalhes).
  const campo = (o, ...nomes) => {
    for (const n of nomes) if (o[n] != null && o[n] !== '') return String(o[n]);
    const k = Object.keys(o).find((k) => nomes.some((n) => k.toLowerCase().includes(n)));
    return k ? String(o[k]) : '';
  };

  // Formas de chamar a Auditoria, da mais provável para a menos.
  const formas = [
    {nome: 'limite 100, unidade do plano', limite: '100', estab: (p) => p.estab},
    {nome: 'limite 100, unidade da sessão', limite: '100', estab: () => estabSessao},
    {nome: 'limite vazio, unidade do plano', limite: '', estab: (p) => p.estab},
    {nome: 'limite 100, sem unidade', limite: '100', estab: () => null},
    {nome: 'limite 10, unidade da sessão', limite: '10', estab: () => estabSessao},
  ];
  const consultar = async (p, f) => {
    const q = new URLSearchParams({
      codOrcamento: p.plano, dataIni: `${p.venda}T03:00:00.000Z`, dataFim: `${dia(amanha)}T03:00:00.000Z`,
      limit: f.limite, offset: '0',
    });
    const estab = f.estab(p);
    if (estab) q.set('estabGeral', estab);
    const r = await fetch(`/api/release/controller/Plano/v1.0/listar_auditoria_venda_plano?${q}`,
                          {headers: {authorization: token, 'X-Belle-Pagina': '/venda-planos'}});
    const texto = await r.text();
    if (!r.ok) {
      const limpo = texto.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 120);
      const e = new Error(`HTTP ${r.status}${limpo ? `: ${limpo}` : ''}`);
      e.status = r.status;
      throw e;
    }
    const j = JSON.parse(texto);
    const regs = Array.isArray(j) ? j : (j.dados || j.data || j.registros || j.result || j.ret || []);
    return {regs: Array.isArray(regs) ? regs : [], estabUsada: estab};
  };

  // Instabilidade do Belle (erro 5xx ou queda de rede): espera e tenta de novo, até 4 vezes.
  const espera = (ms) => new Promise((ok) => setTimeout(ok, ms));
  const consultarComCalma = async (p, f, i, total) => {
    const pausas = [3000, 8000, 20000, 45000];
    for (let t = 0; ; t++) {
      try {
        return await consultar(p, f);
      } catch (e) {
        const instavel = !e.status || e.status >= 500 || e.status === 429;
        if (!instavel || t >= pausas.length) throw e;
        msg(`Auditoria de validade: o Belle está instável (${e.message.slice(0, 40)}). ` +
            `Tentando de novo em ${pausas[t] / 1000} s… (plano ${i + 1} de ${total}, não feche esta aba)`);
        await espera(pausas[t]);
      }
    }
  };

  const enviar = async (consultas) => {
    const corpo = JSON.stringify({k: CHAVE, acao: 'respostas', consultas});
    try {
      await fetch(URL_PONTE, {method: 'POST', body: corpo});
    } catch (e) {
      await fetch(URL_PONTE, {method: 'POST', body: corpo, mode: 'no-cors'});
    }
  };

  let forma = null;
  let pendentesEnvio = [];
  let consultados = 0;
  let comAlteracao = 0;
  let erros = 0;
  let seguidos = 0;
  const outraUnidade = {};
  for (let i = 0; i < fila.length; i++) {
    const p = fila[i];
    p.venda = diaVenda(p.venda);
    if (!p.venda) { erros++; continue; }
    msg(`Auditoria de validade: consultando ${i + 1} de ${fila.length} planos… (não feche esta aba)`);
    let res = null;
    if (!forma) {
      // Primeira consulta: testa as formas até o Belle aceitar uma.
      const tentativas = [];
      for (const f of formas) {
        if (f.estab(p) === '' ) continue;
        try {
          res = await consultarComCalma(p, f, i, fila.length);
          forma = f;
          break;
        } catch (e) {
          tentativas.push(`• ${f.nome}: ${e.message}`);
        }
      }
      if (!forma) {
        msg('O Belle recusou todas as formas de consultar a Auditoria. Mande um print desta caixa para o Claude:\n\n' +
            `Plano ${p.plano} (unidade ${p.estab}), sessão ${sessao}, unidade da sessão ${estabSessao || '?'}\n` +
            tentativas.join('\n'));
        return;
      }
    } else {
      try {
        res = await consultarComCalma(p, forma, i, fila.length);
        seguidos = 0;
      } catch (e) {
        erros++;
        seguidos++;
        if (seguidos >= 5) {
          if (pendentesEnvio.length) await enviar(pendentesEnvio);
          msg(`O Belle não está respondendo agora (${e.message}). ${consultados} planos já foram enviados; ` +
              'os outros continuam na fila. Tente de novo mais tarde (se o erro for 401, faça login de novo).');
          return;
        }
        continue;
      }
    }
    const ops = res.regs
      .filter((o) => /validade/i.test(`${campo(o, 'acao', 'operacao')} ${campo(o, 'detalhes', 'descricao')}`))
      .map((o) => {
        const {ip, ...semIp} = o;
        return {
          data: campo(o, 'dt', 'data'), hora: campo(o, 'hora', 'hr'), usuario: campo(o, 'usu', 'usuario', 'nome'),
          acao: campo(o, 'acao', 'operacao'), detalhes: campo(o, 'detalhes', 'descricao'), bruto: JSON.stringify(semIp),
        };
      });
    // Consulta feita com a unidade da sessão e sem nenhum registro: pode ser plano de outra unidade. Não conta como consultado.
    if (!res.regs.length && res.estabUsada && String(res.estabUsada) !== String(p.estab)) {
      outraUnidade[p.estab] = (outraUnidade[p.estab] || 0) + 1;
      continue;
    }
    consultados++;
    if (ops.length) comAlteracao++;
    pendentesEnvio.push({plano: p.plano, estab: p.estab, consultado_em: consultadoEm, operacoes: ops});
    if (pendentesEnvio.length >= LOTE_ENVIO) {
      await enviar(pendentesEnvio);
      pendentesEnvio = [];
    }
    await new Promise((ok) => setTimeout(ok, 150));
  }
  if (pendentesEnvio.length) await enviar(pendentesEnvio);
  const faltam = Object.entries(outraUnidade).map(([e, n]) => `${n} de ${UNIDADES[e] || e}`).join(', ');
  msg(`Auditoria de validade: pronto. ${consultados} planos consultados, ${comAlteracao} com alteração de validade` +
      (erros ? `, ${erros} com erro (ficam para a próxima)` : '') + '.' +
      (faltam ? `\nFicaram de fora planos de outras unidades (${faltam}): troque a unidade no Belle e clique de novo.` : '') +
      '\nO painel atualiza na próxima rotina diária.');
  setTimeout(() => painel.remove(), faltam ? 60000 : 15000);
})();
