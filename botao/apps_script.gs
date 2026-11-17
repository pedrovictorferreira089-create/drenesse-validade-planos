/**
 * Auditoria de validade — ponte entre o botão do Belle e o painel.
 *
 * Fica numa planilha do Google (Extensões > Apps Script) e é publicado como App da Web.
 * - A rotina diária (nuvem) grava aqui a FILA de planos a consultar na Auditoria do Belle.
 * - O botão de favoritos, clicado no Belle por alguém da gerência, lê a fila, consulta a Auditoria
 *   de cada plano e grava aqui as RESPOSTAS (quem alterou a validade, quando, de/para).
 * - A rotina diária lê as respostas novas e atualiza o painel.
 *
 * A chave abaixo precisa ser a mesma do arquivo dados/monitor/config.json do repositório.
 */
const CHAVE = '__CHAVE__';
const ABA_FILA = 'Fila';
const ABA_RESP = 'Respostas';
const COLS_FILA = ['plano', 'estab', 'unidade', 'venda', 'prioridade', 'motivo'];
const COLS_RESP = ['recebido_em', 'plano', 'estab', 'consultado_em', 'data', 'hora', 'usuario', 'acao', 'detalhes', 'bruto'];

function aba_(nome, cols) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(nome);
  if (!sh) {
    sh = ss.insertSheet(nome);
    sh.getRange(1, 1, 1, cols.length).setValues([cols]).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  return sh;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  const p = e.parameter || {};
  if (p.k !== CHAVE) return json_({erro: 'chave inválida'});
  if (p.acao === 'pendentes') return json_({pendentes: pendentes_(Number(p.limite || 250))});
  if (p.acao === 'respostas') return json_(respostas_(Number(p.desde || 0)));
  return json_({ok: true});
}

function doPost(e) {
  let corpo;
  try { corpo = JSON.parse(e.postData.contents); } catch (err) { return json_({erro: 'corpo inválido'}); }
  if (corpo.k !== CHAVE) return json_({erro: 'chave inválida'});
  const trava = LockService.getScriptLock();
  trava.waitLock(30000);
  try {
    if (corpo.acao === 'fila') return json_({ok: true, n: gravarFila_(corpo.linhas || [])});
    if (corpo.acao === 'respostas') return json_({ok: true, n: gravarRespostas_(corpo.consultas || [])});
    return json_({erro: 'ação desconhecida'});
  } finally {
    trava.releaseLock();
  }
}

/** A rotina diária troca a fila inteira. */
function gravarFila_(linhas) {
  const sh = aba_(ABA_FILA, COLS_FILA);
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, COLS_FILA.length).clearContent();
  if (linhas.length) sh.getRange(2, 1, linhas.length, COLS_FILA.length).setValues(linhas.map(l => COLS_FILA.map(c => l[c] ?? '')));
  PropertiesService.getScriptProperties().setProperty('fila_em', new Date().toISOString());
  return linhas.length;
}

/** Próximos planos da fila, sem os que já foram respondidos depois da última troca da fila. */
function pendentes_(limite) {
  const fila = aba_(ABA_FILA, COLS_FILA);
  const resp = aba_(ABA_RESP, COLS_RESP);
  const filaEm = PropertiesService.getScriptProperties().getProperty('fila_em') || '';
  const feitos = new Set();
  if (resp.getLastRow() > 1) {
    resp.getRange(2, 1, resp.getLastRow() - 1, 2).getValues().forEach(([quando, plano]) => {
      if (String(quando) >= filaEm) feitos.add(String(plano));
    });
  }
  if (fila.getLastRow() < 2) return [];
  return fila.getRange(2, 1, fila.getLastRow() - 1, COLS_FILA.length).getValues()
    .map(r => Object.fromEntries(COLS_FILA.map((c, i) => [c, r[i] instanceof Date ? Utilities.formatDate(r[i], 'UTC', 'yyyy-MM-dd') : String(r[i])])))
    .filter(r => r.plano && !feitos.has(r.plano))
    .slice(0, limite);
}

/** Uma linha por operação de validade; plano consultado sem nenhuma vira uma linha "sem alteração de validade". */
function gravarRespostas_(consultas) {
  const sh = aba_(ABA_RESP, COLS_RESP);
  const agora = new Date().toISOString();
  const linhas = [];
  consultas.forEach(c => {
    const ops = c.operacoes || [];
    if (!ops.length) linhas.push([agora, c.plano, c.estab, c.consultado_em, '', '', '', 'SEM ALTERAÇÃO DE VALIDADE', '', '']);
    ops.forEach(o => linhas.push([agora, c.plano, c.estab, c.consultado_em, o.data || '', o.hora || '', o.usuario || '',
                                  o.acao || '', o.detalhes || '', String(o.bruto || '').slice(0, 1000)]));
  });
  if (linhas.length) sh.getRange(sh.getLastRow() + 1, 1, linhas.length, COLS_RESP.length).setNumberFormat('@').setValues(linhas);
  return linhas.length;
}

/** Respostas a partir da linha `desde` (contagem sem o cabeçalho), para a rotina diária. */
function respostas_(desde) {
  const sh = aba_(ABA_RESP, COLS_RESP);
  const total = Math.max(sh.getLastRow() - 1, 0);
  if (total <= desde) return {total, linhas: []};
  const vals = sh.getRange(2 + desde, 1, total - desde, COLS_RESP.length).getDisplayValues();
  return {total, linhas: vals.map(r => Object.fromEntries(COLS_RESP.map((c, i) => [c, r[i]])))};
}
