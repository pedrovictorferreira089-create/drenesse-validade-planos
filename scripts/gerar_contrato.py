import sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

LOGO, OUT = sys.argv[1], sys.argv[2]
FONT = "Arial"
doc = Document()
st = doc.styles["Normal"]
st.font.name = FONT; st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
st.paragraph_format.space_after = Pt(0); st.paragraph_format.space_before = Pt(0)
st.paragraph_format.line_spacing = 1.0
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(1.5)
sec.top_margin, sec.bottom_margin = Cm(3.6), Cm(3.4)
sec.header_distance, sec.footer_distance = Cm(0.6), Cm(0.6)

def field(run, code):
    for t, txt in (("begin", None), (None, code), ("separate", None), (None, "1"), ("end", None)):
        if t:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t); run._r.append(e)
        elif txt == code:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = code; run._r.append(e)
        else:
            e = OxmlElement("w:t"); e.text = txt; run._r.append(e)

def borders(tbl, sides=("top", "left", "bottom", "right", "insideH", "insideV"), sz=6):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for s in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{s}")
        if s in sides:
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), "000000")
        else:
            e.set(qn("w:val"), "nil")
        b.append(e)
    tblPr.append(b)

def cell_border(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for s, v in kw.items():
        e = OxmlElement(f"w:{s}"); e.set(qn("w:val"), v); e.set(qn("w:sz"), "6"); e.set(qn("w:color"), "999999"); b.append(e)
    tcPr.append(b)

def run(p, text, size=None, bold=False, italic=False, color=None):
    r = p.add_run(text); r.font.name = FONT; r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    return r

def widths(tbl, cms):
    tbl.autofit = False
    tblPr = tbl._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    for gc, w in zip(tbl._tbl.tblGrid.findall(qn("w:gridCol")), cms):
        gc.set(qn("w:w"), str(int(w * 567)))
    for row in tbl.rows:
        trPr = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)
        for c, w in zip(row.cells, cms):
            c.width = Cm(w)

# ---------- cabeçalho ----------
h = sec.header
hp = h.paragraphs[0]
ht = h.add_table(rows=1, cols=3, width=Cm(18))
borders(ht, sides=("top", "left", "bottom", "right"))
widths(ht, [2.6, 12.4, 3.0])
c0, c1, c2 = ht.rows[0].cells
p = c0.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(4)
p.add_run().add_picture(LOGO, width=Cm(2.2))
p = c1.paragraphs[0]; p.paragraph_format.space_before = Pt(4)
run(p, "DRENESSE LAGOA NOVA - 62.240.447/0001-95 - Telefone: (84)2020-7722 | Contato: (84)2020-7722", 7)
p = c1.add_paragraph(); run(p, "AVENIDA AMINTAS BARROS, 3130 - Natal/RN -  59063-350 - E-mail: sac@drenesse.com.br", 7)
p = c1.add_paragraph(); p.paragraph_format.space_after = Pt(14)
p = c2.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; p.paragraph_format.space_before = Pt(4)
run(p, "Página: ", 7); field(run(p, "", 7), "PAGE"); run(p, " / ", 7); field(run(p, "", 7), "NUMPAGES")
p = c2.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; p.paragraph_format.space_before = Pt(6)
run(p, "Belle Software", 7, bold=True)
hp._p.getparent().remove(hp._p)  # tira o parágrafo vazio antes da tabela
h.add_paragraph()

# ---------- rodapé: assinatura eletrônica + página ----------
f = sec.footer
fp = f.paragraphs[0]
ft = f.add_table(rows=1, cols=2, width=Cm(18))
borders(ft, sides=())
widths(ft, [8.5, 9.5])
a, b = ft.rows[0].cells
p = a.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; p.paragraph_format.space_before = Pt(18)
run(p, "Assinatura Eletrônica capturada digitalmente pelo Sistema Belle Software, através do IP: [IP] no dia [DATA] às [HORA]", 8, italic=True)
p = b.paragraphs[0]; p.paragraph_format.space_before = Pt(28)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "______________________________________________", 8, color="999999")
p = b.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(p, "[NOME DO CONTRATANTE]", 8, italic=True)
p = b.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(p, "contratante", 8, italic=True)
fp._p.getparent().remove(fp._p)
p = f.add_paragraph(); p.paragraph_format.space_before = Pt(4)
pPr = p._p.get_or_add_pPr(); bd = OxmlElement("w:pBdr"); tp = OxmlElement("w:top")
tp.set(qn("w:val"), "single"); tp.set(qn("w:sz"), "4"); tp.set(qn("w:color"), "000000"); bd.append(tp); pPr.append(bd)
tabs = p.paragraph_format.tab_stops
from docx.enum.text import WD_TAB_ALIGNMENT
tabs.add_tab_stop(Cm(9), WD_TAB_ALIGNMENT.CENTER); tabs.add_tab_stop(Cm(18), WD_TAB_ALIGNMENT.RIGHT)
run(p, "\tPágina: ", 7); field(run(p, "", 7), "PAGE"); run(p, " / ", 7); field(run(p, "", 7), "NUMPAGES")
run(p, "\tEmissão: [DATA DE EMISSÃO]", 7)

# ---------- corpo ----------
def par(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0):
    p = doc.add_paragraph(); p.alignment = align; p.paragraph_format.space_before = Pt(before)
    if text: run(p, text)
    return p

def campos(pares, before=0):
    p = par(align=WD_ALIGN_PARAGRAPH.LEFT, before=before)
    for lab, val in pares:
        run(p, lab, bold=True); run(p, val)
    return p

campos([("CONTRATO Nº: ", "[Nº DO CONTRATO]          "), ("VENDA Nº: ", "[Nº DA VENDA]")])
p = par(); run(p, "CONTRATADA: ", bold=True)
run(p, "CENTRO DE ESTETICA AVANCADA AISI MEDEIROS LTDA, inscrita no CNPJ sob nº62.240.447/0001-95, situada á AVENIDA AMINTAS BARROS LJ A, nº 3130 - Natal/RN.")
campos([("CONTRATANTE:  ", "[NOME DO CONTRATANTE]")])
campos([("CPF: ", "[CPF]    "), ("RG: ", "[RG]")])
campos([("ENDEREÇO:  ", "[ENDEREÇO], [BAIRRO] - [CIDADE] ([UF]) - CEP: [CEP]")])
campos([("CONTATO: ", "Fone: [TELEFONE]                              Cel: [CELULAR]")])
par("Email: [E-MAIL]", align=WD_ALIGN_PARAGRAPH.LEFT)

p = par(align=WD_ALIGN_PARAGRAPH.CENTER, before=14); p.paragraph_format.space_after = Pt(14)
run(p, "CONTRATO DE PRESTAÇÃO DE SERVIÇOS ESTÉTICOS (C)", bold=True)

texto = open(sys.argv[3], encoding="utf-8").read().split("\n")
for ln in texto:
    if ln.startswith("@@"):
        par(before=10)
    else:
        par(ln)

# ---------- plano ----------
par(before=10)
par("A CONTRATANTE adquire o número de sessões e tipos de tratamento abaixo indicados:", align=WD_ALIGN_PARAGRAPH.LEFT)
def tabela(linhas, ws, bolds=(), centers=()):
    t = doc.add_table(rows=len(linhas), cols=len(ws)); borders(t); widths(t, ws)
    for i, l in enumerate(linhas):
        cells = t.rows[i].cells
        j = 0
        for k, v in enumerate(l):
            if v is None: continue
            c = cells[k]
            span = 1
            while k + span < len(l) and l[k + span] is None: span += 1
            if span > 1: c = c.merge(cells[k + span - 1])
            p = c.paragraphs[0]
            if i in centers: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run(p, v, 10, bold=i in bolds)
    return t
tabela([["Plano: [CÓDIGO DO PLANO] - [NOME DO PLANO]", None, None, None, None],
        ["Vendido em: [DATA DA VENDA]", None, "Válido até: [DATA DE VALIDADE]", None, None],
        ["Serviços", None, None, None, None]], [2.6, 2.6, 2.6, 5.1, 5.1], bolds=(0, 1, 2))
t = tabela([["[SERVIÇO]", None, None, None, None],
            ["Nº Sessões", "Valor Unit.", "Valor", "Desconto", "Valor Total"],
            ["[Nº]", "[V. UNIT.]", "[VALOR]", "[DESCONTO]", "[VALOR TOTAL]"]],
           [2.6, 2.6, 2.6, 5.1, 5.1], bolds=(1,), centers=(1,))
for c in t.rows[1].cells: c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
p = par("(um quadro por serviço do plano)", align=WD_ALIGN_PARAGRAPH.LEFT); p.runs[0].font.size = Pt(8); p.runs[0].italic = True; p.runs[0].font.color.rgb = RGBColor(0x88,0x88,0x88)
p = campos([("Valor Bruto: ", "R$ [VALOR BRUTO]")], before=4)
campos([("Valor Contratual: ", "R$ [VALOR CONTRATUAL]      "), ("Desconto Adic.: ", "R$ [DESCONTO ADICIONAL]")], before=4)
campos([("Valor com Desconto: ", "R$ [VALOR COM DESCONTO]")])
par(before=12)
t = tabela([["Parcelas", None, None, None],
            ["Parcela", "Vencimento", "Valor(R$)", "Forma de Pagamento"],
            ["[Nº]", "[VENCIMENTO]", "[VALOR]", "[FORMA DE PAGAMENTO]"]],
           [2.2, 3.8, 3.0, 9.0], bolds=(0, 1), centers=(0, 1))
par(before=6)
t = tabela([["Total", "[TOTAL]"]], [3.8, 3.0], centers=())
t.rows[0].cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
par("[CIDADE] ([UF]), [DATA POR EXTENSO]", align=WD_ALIGN_PARAGRAPH.RIGHT, before=24)

# ---------- assinaturas ----------
doc.add_page_break()
p = par(align=WD_ALIGN_PARAGRAPH.LEFT, before=20)
t = doc.add_table(rows=2, cols=2); borders(t, sides=()); widths(t, [9, 9])
dados = [("[RAZÃO SOCIAL DA CONTRATADA]", "Contratada"), ("[NOME DO CONTRATANTE]", "Contratante"),
         ("", "Testemunha 1"), ("", "Testemunha 2")]
for i, (nome, papel) in enumerate(dados):
    c = t.rows[i // 2].cells[i % 2]
    p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(40)
    run(p, "____________________________________________", 9, color="999999")
    if nome:
        p = c.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(p, nome, 9, italic=True)
    p = c.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; run(p, papel, 9, italic=True)
t.rows[0].cells[0].paragraphs[0].runs[0].text = "____________________________________________"
doc.save(OUT)
print("ok", OUT)
