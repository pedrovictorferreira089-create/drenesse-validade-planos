# Botão "Auditoria de validade": como instalar e usar

O painel descobre sozinho, todo dia, **quais** planos tiveram a validade alterada (pela API de integração do Belle).
O **nome de quem alterou** só existe na tela Auditoria do Belle, que o Belle libera apenas para quem está logado.
O botão faz essa consulta no navegador de quem clicou e manda o resultado para o painel.

```
Rotina diária (nuvem) ──fila de planos──▶ Planilha-ponte (Google Apps Script) ◀──lê a fila── Botão no Belle
        ▲                                         │                                  │
        └──────────── lê as respostas ◀───────────┘◀──── grava quem alterou ─────────┘
```

## 1. Planilha-ponte (uma vez, ~5 minutos, quem configura: Pedro) — feito em 17/11/2026

1. Crie uma planilha nova no Google Drive, com o nome **Auditoria de validade – ponte**.
2. Menu **Extensões → Apps Script**. Apague o que estiver no editor e cole o conteúdo de `apps_script_pronto.gs`
   (é o `apps_script.gs` com a chave já preenchida; pedir ao Claude se não tiver).
3. Salve (ícone de disquete).
4. **Implantar → Nova implantação →** engrenagem **→ App da Web**.
   - Descrição: `ponte do botão`
   - Executar como: **Eu**
   - Quem pode acessar: **Qualquer pessoa**
5. **Implantar → Autorizar acesso**, escolha a sua conta. Se aparecer "o Google não verificou este app",
   clique em **Avançado → Acessar (não seguro)**: o app é seu, só mexe nesta planilha.
6. Copie a **URL do app da Web** (termina em `/exec`) e mande para o Claude. Ele grava a URL no
   `dados/monitor/config.json`, gera o favorito e manda a fila para a planilha.

As abas **Fila** e **Respostas** são criadas sozinhas. Não precisa compartilhar a planilha com ninguém.

## 2. Favorito no Chrome (em cada computador de quem vai clicar)

1. Mostre a barra de favoritos: **Ctrl+Shift+B**.
2. Clique com o botão direito na barra → **Adicionar página…**
3. Nome: **Auditoria de validade**. URL: cole o texto inteiro do arquivo `favorito.txt` (começa com `javascript:`).
4. Salvar.

## 3. Uso (gerência, 1 clique)

1. Abra o Belle e faça login normalmente.
2. Clique no favorito **Auditoria de validade**.
3. Uma caixa no canto da tela mostra o andamento ("consultando 12 de 250…"). Não feche a aba até aparecer "pronto".
4. No dia seguinte o painel mostra quem alterou. Cada clique consulta até 250 planos da fila, na ordem:
   1. validades alteradas que a foto diária encontrou;
   2. planos vendidos em 2026 com validade acima de 12 meses;
   3. planos vendidos em 2026 com validade de 7 a 12 meses;
   4. planos vendidos em 2025 com validade acima de 12 meses.

Uma vez por semana basta para manter o dia a dia em dia. Para zerar o atraso inicial (cerca de 1.570 planos),
clique algumas vezes seguidas (cada rodada leva poucos minutos).

## Segurança

- O botão usa a sessão do Belle de quem clicou, dentro do próprio Belle. O token do Belle não sai do navegador.
- Para a planilha-ponte vão só: nº do plano, unidade, data, hora, usuário que alterou, operação e detalhes.
  O IP que o Belle registra é descartado.
- A chave do botão evita gravações de fora, mas quem tiver o favorito consegue gravar respostas: entregue só à gerência.
- Quem pode consultar a Auditoria no Belle continua sendo decidido pelas permissões do próprio Belle.
