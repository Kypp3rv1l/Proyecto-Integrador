"""Genera la versión editable del informe (.docx) con el mismo contenido que el PDF.
Uso, desde informe/:  python a_word.py .. PI_Informe_Tecnico.docx"""
import re, sys, os
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
salida = sys.argv[2]
sys.argv = [sys.argv[0], sys.argv[1], '_tmp.pdf']
import informe as inf
from reportlab.platypus import Paragraph, Table, Image, KeepTogether, PageBreak, Spacer

TINTA, VERDE = RGBColor(0x1B, 0x2A, 0x41), RGBColor(0x2E, 0x8B, 0x6F)
doc = Document()
sec = doc.sections[0]; sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.left_margin = sec.right_margin = Mm(18); sec.top_margin = sec.bottom_margin = Mm(16)
st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(10.5); st.font.color.rgb = TINTA

# número de página abajo a la derecha
pie = sec.footer.paragraphs[0]; pie.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = pie.add_run('Proyecto Integrador · Desarrollo de Soluciones Inteligentes · UBO · 2026_S2      Página '); r.font.size = Pt(8)
for tipo, texto in (('begin', None), (None, 'PAGE'), ('end', None)):
    run = pie.add_run(); run.font.size = Pt(8)
    if tipo:
        fc = OxmlElement('w:fldChar'); fc.set(qn('w:fldCharType'), tipo); run._r.append(fc)
    else:
        it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = texto; run._r.append(it)

def runs(par, html, base_bold=False, size=None, color=None, italic=False):
    html = html.replace('<br/>', '\n').replace('&amp;', '&')
    for trozo in re.split(r'(<[^>]+>)', html):
        if not trozo:
            continue
        if trozo.startswith('<'):
            t = trozo.strip('</>').split()[0] if trozo.strip('</>') else ''
            cierra = trozo.startswith('</')
            estado[t] = not cierra
            continue
        r = par.add_run(trozo)
        r.bold = base_bold or estado.get('b', False); r.italic = italic or estado.get('i', False)
        r.font.superscript = estado.get('super', False); r.font.subscript = estado.get('sub', False)
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color

def parrafo(p):
    global estado; estado = {}
    nom = p.style.name
    if nom == 'h1': h = doc.add_heading(level=1); runs(h, p.text, True, 15, TINTA)
    elif nom == 'h2': h = doc.add_heading(level=2); runs(h, p.text, True, 12, VERDE)
    elif nom == 't': h = doc.add_paragraph(); runs(h, p.text, True, 24, TINTA)
    elif nom == 'ce': h = doc.add_paragraph(); runs(h, p.text, False, 12, VERDE)
    elif nom == 's': h = doc.add_paragraph(); runs(h, p.text, False, 13, RGBColor(0x4A, 0x55, 0x68))
    elif nom == 'cap': h = doc.add_paragraph(); runs(h, p.text, False, 8.5, RGBColor(0x4A, 0x55, 0x68), True)
    else:
        h = doc.add_paragraph(); runs(h, p.text)
        if nom == 'b': h.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if p.style.alignment == 1: h.alignment = WD_ALIGN_PARAGRAPH.CENTER

def tabla(t):
    global estado
    filas = t._cellvalues
    portada_id = filas[0][0].style.name == 'idl'
    tb = doc.add_table(rows=len(filas), cols=len(filas[0])); tb.style = None if portada_id else 'Light Grid Accent 1'
    if portada_id:
        from docx.enum.table import WD_TABLE_ALIGNMENT
        tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, fila in enumerate(filas):
        for j, celda in enumerate(fila):
            c = tb.cell(i, j); c.text = ''; estado = {}
            if portada_id:
                runs(c.paragraphs[0], celda.text, j == 0, 10, VERDE if j == 0 else TINTA)
                if j == 0: c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                runs(c.paragraphs[0], celda.text if hasattr(celda, 'text') else str(celda), i == 0, 8.5)
    doc.add_paragraph()

def imagen(im):
    doc.add_picture(im.filename, width=Mm(im.drawWidth / 2.8346))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

def recorrer(lst):
    for x in lst:
        if isinstance(x, KeepTogether): recorrer(x._content)
        elif isinstance(x, Paragraph): parrafo(x)
        elif isinstance(x, Table): tabla(x)
        elif isinstance(x, Image): imagen(x)
        elif isinstance(x, PageBreak): doc.add_page_break()
        elif isinstance(x, Spacer) and x.height > 40: doc.add_paragraph().paragraph_format.space_after = Pt(x.height * .6)

estado = {}
recorrer(inf.E)
doc.save(salida); print('ok', salida)
