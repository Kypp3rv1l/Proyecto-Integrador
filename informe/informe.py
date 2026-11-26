"""Genera el informe técnico desde evidencia/. Uso, desde informe/: python figuras.py .. . && python informe.py .. PI_Informe_Tecnico.pdf"""
import json, sys, os, pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
REPO = sys.argv[1]; EV = REPO + '/evidencia/'; OUT = sys.argv[2]
REF = ParagraphStyle('ref', fontName='Helvetica', fontSize=9, leading=12.4, textColor=colors.HexColor('#1B2A41'), spaceAfter=5)
R = json.load(open(EV + 'resumen_evidencia.json', encoding='utf-8')); ESC = json.load(open(EV + 'resumen_escenarios.json', encoding='utf-8'))
MET = pd.read_csv(EV + 'metricas_continuidad.csv', index_col=0); CUP = pd.read_csv(EV + 'cupos_backtest_todas.csv', index_col=0)
VT = pd.read_csv(EV + 'validacion_temporal.csv'); CM = pd.read_csv(EV + 'comparacion_modelos.csv', index_col=0).sort_values('MAE_medio')
AL = pd.read_csv(EV + 'alcance_por_tipo.csv'); TAM = pd.read_csv(EV + 'error_por_tamano_cohorte.csv').set_index('tramo_n_t').loc[['5–9', '10–19', '20–49', '50 o más']]
HP = pd.read_csv(EV + 'comparacion_hiperparametros.csv'); ROB = pd.read_csv(EV + 'robustez.csv'); BIT = pd.read_csv(EV + 'bitacora_pruebas.csv'); ADV = pd.read_csv(EV + 'pruebas_adversarias.csv')
CONTRATO = json.load(open(REPO + '/contrato_modelo.json', encoding='utf-8'))
f = lambda x, d=3: f'{x:.{d}f}'.replace('.', ',')
miles = lambda n: f'{n:,}'.replace(',', '.')
TINTA = colors.HexColor('#1B2A41'); VERDE = colors.HexColor('#2E8B6F'); SUAVE = colors.HexColor('#EEF2F0'); LINEA = colors.HexColor('#C9D1CC')
B = ParagraphStyle('b', fontName='Helvetica', fontSize=9.6, leading=13.4, textColor=TINTA, spaceAfter=5, alignment=4)
H1 = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=13.5, leading=17, textColor=TINTA, spaceBefore=10, spaceAfter=5, keepWithNext=1)
H2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=10.5, leading=14, textColor=VERDE, spaceBefore=6, spaceAfter=3, keepWithNext=1)
CAP = ParagraphStyle('cap', fontName='Helvetica-Oblique', fontSize=8.4, leading=11, textColor=colors.HexColor('#4A5568'), spaceAfter=8)
TC = ParagraphStyle('tc', fontName='Helvetica', fontSize=8.4, leading=10.6, textColor=TINTA)
TH = ParagraphStyle('th', parent=TC, fontName='Helvetica-Bold', textColor=colors.white)
P = lambda t, s=B: Paragraph(t, s)
def tabla(filas, anchos, cap=None):
    d = [[Paragraph(str(c), TH if i == 0 else TC) for c in fila] for i, fila in enumerate(filas)]
    t = Table(d, colWidths=[a * mm for a in anchos], repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), TINTA), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, SUAVE]),
                           ('LINEBELOW', (0, 0), (-1, -1), .3, LINEA), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    return KeepTogether([t] + ([P(cap, CAP)] if cap else [Spacer(1, 6)]))
def fig(n, ancho, cap):
    im = Image(f'{n}.png'); r = im.imageHeight / im.imageWidth; im.drawWidth = ancho * mm; im.drawHeight = ancho * mm * r
    return KeepTogether([im, P(cap, CAP)])
def portada(c, d):
    # franja de color al pie de la portada, sin número de página
    c.saveState(); c.setFillColor(TINTA); c.rect(0, 0, A4[0], 14 * mm, stroke=0, fill=1)
    c.setFillColor(VERDE); c.rect(0, 14 * mm, A4[0], 1.6 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor('#EEF2EE')); c.setFont('Helvetica', 9)
    c.drawCentredString(A4[0] / 2, 5.5 * mm, "Universidad Bernardo O'Higgins · Ingeniería Civil en Computación · 2026"); c.restoreState()
def pie(c, d):
    c.saveState(); c.setFont('Helvetica', 7.5); c.setFillColor(colors.HexColor('#6B7280'))
    c.drawString(18 * mm, 10 * mm, "Proyecto Integrador · Desarrollo de Soluciones Inteligentes · UBO · 2026_S2"); c.drawRightString(192 * mm, 10 * mm, f'Página {d.page}'); c.restoreState()

m = MET.loc['Random Forest (modelo)']; br = MET.loc['Base: retención del año previo']; bm = MET.loc['Base: media de entrenamiento']
cm_, cr = CUP.loc['Modelo'], CUP.loc['Base: retención del año previo']
datos = R['datos']; integ = R['integracion']
cft25 = AL[(AL.anio_t == 2025) & (AL.tipo_inst_1 == 'Centros de Formación Técnica')].iloc[0]; cft24 = AL[(AL.anio_t == 2024) & (AL.tipo_inst_1 == 'Centros de Formación Técnica')].iloc[0]; cft23 = AL[(AL.anio_t == 2023) & (AL.tipo_inst_1 == 'Centros de Formación Técnica')].iloc[0]
u25 = AL[(AL.anio_t == 2025) & (AL.tipo_inst_1 == 'Universidades')].iloc[0]
E = []
# 1. portada
from reportlab.platypus import HRFlowable
CEN = lambda nom, **kw: ParagraphStyle(nom, alignment=1, **{'textColor': TINTA, **kw})
logo = Image('logo_ubo.png', width=82 * mm, height=82 * mm * 465 / 955, hAlign='CENTER')
E += [Spacer(1, 22 * mm), logo, Spacer(1, 30 * mm),
      P('Informe técnico · Proyecto Integrador', CEN('ce', fontName='Helvetica', fontSize=12, leading=16, textColor=VERDE)), Spacer(1, 5 * mm),
      P('Anticipación de la demanda de cupos<br/>universitarios por programa<br/>y año de estudio', CEN('t', fontName='Helvetica-Bold', fontSize=24, leading=30)),
      Spacer(1, 7 * mm), HRFlowable(width=40 * mm, thickness=2.5, color=VERDE, hAlign='CENTER'), Spacer(1, 7 * mm),
      P('Desarrollo de Soluciones Inteligentes · 02DSI243061', CEN('s', fontName='Helvetica', fontSize=13, leading=17, textColor=colors.HexColor('#4A5568'))),
      Spacer(1, 34 * mm)]
ident = [['Integrantes', 'Ivan Oliva y Bastian Gonzalez · Paralelo 2'], ['Docente', 'Enrique Pastene Aceituno'],
         ['Entrega', 'EVAL-02 · 27 de noviembre de 2026'], ['Prototipo', 'github.com/Kypp3rv1l/Proyecto-Integrador']]
ID_L = ParagraphStyle('idl', fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=VERDE, alignment=2)
ID_R = ParagraphStyle('idr', fontName='Helvetica', fontSize=9.5, leading=13, textColor=TINTA)
tid = Table([[Paragraph(k, ID_L), Paragraph(v, ID_R)] for k, v in ident], colWidths=[48 * mm, 92 * mm], hAlign='CENTER')
tid.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5), ('LEFTPADDING', (1, 0), (1, -1), 10)]))
E.append(tid)
E.append(PageBreak())
# 2. resumen
E += [P('1. Resumen ejecutivo', H1), P(
    f"<b>Problema.</b> Para dimensionar secciones, docentes y salas de los años superiores, la planificación académica necesita saber cuántos estudiantes de cada cohorte seguirán el próximo año en su programa. "
    f"<b>Solución.</b> Un prototipo local que recibe cohortes universitarias (programa × año de ingreso), valida los datos, aplica un modelo Random Forest entrenado con la matrícula pública del Mineduc (muestra del 4% de los programas, 2017–2026) y entrega la continuidad estimada, los estudiantes esperados y los cupos por programa y año de estudio. "
    f"<b>Resultado principal.</b> En la prueba 2025 (objetivo construido con la matrícula 2026) el error absoluto medio de la continuidad es {f(m.MAE)} (unos {round(m.MAE*100)} puntos porcentuales), menor que repetir la retención del año previo ({f(br.MAE)}) y que usar la media ({f(bm.MAE)}); el modelo también gana en los cortes 2022, 2023 y 2024. "
    f"En estudiantes, el error es de {f(cm_.MAE_est_por_cohorte, 2)} por cohorte frente a {f(cr.MAE_est_por_cohorte, 2)} de la mejor línea base. "
    f"<b>Alcance.</b> Solo universidades y cupos por año de estudio (no por asignatura). Tras la entrega 1 se excluyeron CFT e IP, se cambió Ridge por Random Forest según el criterio de selección fijado y se corrigió la suma de cupos del modo lote.")]
# 3. contexto
E += [P('2. Contexto, problema, usuarios y objetivos', H1), P(
    "<b>Contexto.</b> La matrícula universitaria se organiza en programas cuyas cohortes avanzan año a año. Si una cohorte pierde estudiantes, los cupos de los años superiores quedan sobredimensionados; si retiene más de lo previsto, faltan. La deserción es un proceso que se extiende más allá del ingreso y depende de factores del estudiante y de la institución (Tinto, 1975). En Chile, el SIES publica cada año la retención de 1.er año, entendida como la permanencia en la misma institución y en la cohorte original al año siguiente; en la cohorte 2017 fue 78,7% en universidades, 70,9% en IP y 68,7% en CFT (SIES, 2018). Ese indicador mira solo el primer año y no se desagrega para planificar años superiores; este proyecto mide la continuidad en el mismo programa para todos los años de estudio. "
    "<b>Usuarios.</b> Equipos de planificación académica o direcciones de escuela que deciden la oferta de secciones y recursos para el año siguiente. "
    "<b>Objetivo general.</b> Anticipar con datos públicos la continuidad de cada cohorte para estimar la demanda de cupos del año siguiente. "
    "<b>Objetivos específicos.</b> (1) Construir una tabla de cohortes con un objetivo medible. (2) Comparar técnicas y seleccionar una con un criterio fijado antes de ver los resultados. (3) Integrar el modelo en un flujo con validación de entradas y una interfaz demostrable. (4) Validar con datos reales, en varios cortes temporales, con casos límite y análisis de errores. "
    "<b>Fuera de alcance.</b> Centros de formación técnica e institutos profesionales, cupos por asignatura (la base no trae asignaturas), decisiones sobre personas y la estimación del ingreso nuevo.")]
# 4. datos
E += [P('3. Datos', H1), P(
    f"<b>Origen.</b> Ministerio de Educación de Chile, «Matrícula en Educación Superior», bases públicas anuales con MRUN anonimizado, publicadas en el portal de datos abiertos (datosabiertos.mineduc.cl/matricula-en-educacion-superior; página consultada el 21-11-2026). El curso entregó una muestra del 4% de los programas para 2017–2026, un CSV por año (huella SHA-256 del zip: {datos['sha256_zip'][:16]}…). "
    "<b>Condición de uso.</b> La página de descarga no declara una licencia ni términos de uso; se trata de datos públicos y anonimizados que se usan con fines académicos y citando la fuente. El repositorio no redistribuye las bases originales, solo cohortes agregadas."),
    P(f"<b>Preparación.</b> Pregrado, estudiantes con MRUN y un registro por (año, programa, estudiante). La unidad de análisis es la cohorte: programa (<i>codigo_unico</i>) × año de ingreso (<i>anio_ing_carr_act</i>) observada en el año t. El objetivo <i>y</i> es la proporción de la cohorte de t que figura en t+1 en el mismo programa; titularse, cambiarse, pausar o abandonar cuentan como «no continúa». Se conservan cohortes universitarias de al menos 5 estudiantes que aún no cursan su último año nominal. Predictores: tamaño de la cohorte y del año previo, retención previa, total del programa, arancel, proporción de mujeres, edad media, año de estudio, duración, años restantes y nueve atributos del programa."),
    P(f"<b>Calidad y decisiones.</b> (a) El año de ingreso viene vacío en la mayoría de las filas de 2017, que solo se usa como diagnóstico. (b) <i>formato_valores</i> está vacío en 2017–2021: un arancel menor a 10.000 se interpreta como UF, regla que coincide con el campo declarado en 2022–2026; el arancel en UF queda como faltante. (c) Se eliminan registros duplicados. (d) 2020–2021 (pandemia) se mantienen. "
      f"(e) <b>Alcance universitario:</b> en 2025, el {f(cft25.pct_codigo_desaparece, 1)}% de las cohortes de CFT pertenecen a programas cuyo código no existe en 2026 (contra {f(cft23.pct_codigo_desaparece, 1)}% en 2023, {f(cft24.pct_codigo_desaparece, 1)}% en 2024 y {f(u25.pct_codigo_desaparece, 1)}% en universidades en 2025). La base no distingue un cierre de un cambio de código, por lo que en CFT el objetivo mide en parte cambios administrativos. "
      f"<b>Partición temporal</b> (no aleatoria, porque se pronostica el año siguiente): entrenamiento con cohortes observadas en 2019–2024 ({miles(datos['cohortes_entrenamiento'])}) y prueba en 2025 ({datos['cohortes_prueba']} cohortes, {datos['programas_prueba']} programas). Todo el preprocesamiento se ajusta solo con entrenamiento, dentro del mismo pipeline. "
      "<b>Privacidad.</b> El prototipo trabaja con agregados por cohorte y no exporta MRUN, fechas de nacimiento ni registros individuales.")]
E.append(fig('fig_alcance', 140, 'Figura 1. Porcentaje de cohortes cuyo código de programa desaparece al año siguiente, por tipo de institución (evidencia/alcance_por_tipo.csv).'))
# 5. metodología
filas = [['Alternativa', '2022', '2023', '2024', 'MAE medio']] + [[i, f(r[str(2022)]), f(r[str(2023)]), f(r[str(2024)]), f'<b>{f(r.MAE_medio)}</b>'] for i, r in CM.iterrows()]
E += [P('4. Metodología y técnica de inteligencia artificial', H1), P(
    "<b>Tarea.</b> Regresión: el objetivo es una proporción entre 0 y 1, no una clase. <b>Alternativas.</b> Constante (mediana de entrenamiento), persistencia (repetir la retención del año previo), Ridge (alpha = 1) y Random Forest (300 árboles, profundidad máxima 5), todas con el mismo preprocesamiento. En la persistencia, las cohortes de primer año (sin retención previa) se completan con la mediana de entrenamiento en la Tabla 1 y con la media en la Tabla 3; por eso sus cifras difieren algo. "
    "<b>Validación para elegir.</b> Ventana móvil con años de prueba 2022, 2023 y 2024, entrenando cada vez con los años anteriores; 2025 queda reservado y no se usa para elegir. <b>Criterio fijado antes de comparar</b> (PI-02): gana el menor MAE medio; si la diferencia es menor a 0,002 se elige el más simple, y un modelo solo se justifica si supera a la mejor línea base."),
    tabla(filas, [62, 24, 24, 24, 30], 'Tabla 1. MAE por año de validación con cohortes universitarias (evidencia/comparacion_modelos.csv). La entrega 1 usaba Ridge, elegido con todos los tipos de institución; al limitar el alcance, Random Forest supera a Ridge por 0,0095 y, según el criterio, pasa a ser el modelo. En la persistencia, las cohortes sin historial usan la mediana de entrenamiento.'),
    P(f"<b>Configuración.</b> Pipeline de scikit-learn: imputación por mediana con indicador de faltante, logaritmo y estandarización para los conteos, imputación y estandarización para las tasas, codificación one-hot con categorías raras agrupadas y RandomForestRegressor(n_estimators = 300, max_depth = 5, random_state = 42). Los hiperparámetros se fijaron antes de comparar y luego se revisaron en la misma ventana 2022–2024, sin usar 2025 (evidencia/comparacion_hiperparametros.csv). Con 100, 300 o 500 árboles el MAE medio es {f(HP[(HP.profundidad == '5') & (HP.arboles == 300)].MAE_medio.iloc[0], 4)} en los tres casos: el error del bosque ya se estabilizó, como predice Breiman (2001). Con profundidad 3 sube a {f(HP[HP.profundidad == '3'].MAE_medio.iloc[0], 4)}; con 8, 12 o sin límite baja a cerca de {f(HP[HP.profundidad == '8'].MAE_medio.iloc[0], 3)}. La mejora de la profundidad 8 ({f(HP[(HP.profundidad == '5') & (HP.arboles == 300)].MAE_medio.iloc[0] - HP[HP.profundidad == '8'].MAE_medio.iloc[0], 4)}, unos 0,2 puntos) apenas supera el umbral de 0,002, que se fijó para elegir entre tipos de modelo; se mantuvo la profundidad 5. "
      "<b>Supuestos y límites.</b> Un bosque no extrapola: fuera del rango de entrenamiento repite el valor del borde, y la aplicación lo avisa. Responde por tramos, de modo que un cambio pequeño en un predictor puede mover la predicción de forma escalonada. Los mismos programas aparecen en entrenamiento y prueba, en años distintos; no se midió desempeño en programas nuevos.")]
# 6. arquitectura
E += [KeepTogether([P('5. Arquitectura e integración', H1), fig('fig_arquitectura', 170, 'Figura 2. Recorrido de una solicitud: entrada, validación, derivación, modelo guardado y cupos.')]),
      P("<b>Componentes.</b> <i>cupos_app.py</i> carga el modelo y verifica su huella SHA-256 contra <i>contrato_modelo.json</i>; <i>validar</i> separa errores (bloquean y el modelo no se llama) de avisos (informan) y aplica el alcance universitario; <i>a_features</i> deriva año de estudio, duración y años restantes; <i>predecir</i> acota la salida a [0, 1]; <i>proyectar_lote</i> suma los estudiantes esperados por programa, año siguiente y año de estudio. "
        "<b>Interfaces.</b> Página web local (<i>iniciar.bat</i> crea un entorno de Python dentro de la carpeta y la abre en el navegador), JSON para un caso, CSV para un lote y línea de comandos; el notebook queda como demostración técnica."),
      P("<b>Reglas del modo lote</b> (corregidas tras la entrega 1). (1) Una cohorte se identifica por programa + año observado + año de ingreso; si se repite, todas sus filas quedan como DUPLICADA y ninguna suma. (2) Ninguna fila rechazada suma a un total, y cada fila de cupos informa cuántas se excluyeron en su programa. (3) El año 1 de t+1 (ingreso nuevo) se calcula aparte: se usa el ingreso proyectado si se entrega; si no, el ingreso de t del mismo programa, solo cuando esa fila fue aceptada; sin dato válido queda vacío con el motivo, en vez de un 0. "
        "<b>Decisiones de diseño.</b> El pipeline completo se guarda en un solo archivo y la aplicación solo llama a <i>predict</i>; el contrato es la única fuente para validación y construcción de la fila del modelo; el arancel se pide en pesos porque el modelo se entrenó con pesos; cada resultado lleva el error típico de referencia (MAE de prueba).")]
# 7. validación
E += [P('6. Validación y resultados', H1), P(
    f"Todas las cifras provienen de ejecutar <i>construir_modelo.py</i>, <i>comparar_modelos.py</i>, <i>ejecutar_validacion.py</i> y las suites de prueba sobre la muestra, y quedan en <i>evidencia/</i>. <b>Integridad.</b> El modelo guardado coincide con el reentrenado; la aplicación reproduce el pipeline en {integ['coinciden']} de {integ['cohortes_en_contrato']} cohortes (otras {integ['fuera_por_arancel_en_uf']} quedan fuera del contrato por tener el arancel en UF); y la huella de lo aprendido es idéntica antes y después de {miles(R['sin_reajuste']['llamadas_totales_predict'])} llamadas a <i>predict</i>.")]
E += [P('6.1 Continuidad en la prueba 2025', H2), tabla([['Alternativa', 'MAE', 'MAE pond. por n', 'RMSE', 'R<super>2</super>', 'Sesgo']] + [[i, f(r.MAE), f(r.MAE_ponderado_n), f(r.RMSE), f(r.R2, 2), f(r.sesgo)] for i, r in MET.iterrows()], [62, 20, 28, 20, 18, 20],
      f'Tabla 2. El modelo supera a ambas líneas base. El R<super>2</super> de {f(m.R2, 2)} es modesto: en universidades la continuidad es alta y varía poco, así que hay poca variación que explicar. Las bases tienen R<super>2</super> negativo.'),
      fig('fig_pred_obs', 88, 'Figura 3. Continuidad estimada frente a la observada en 2026; el tamaño del punto crece con la cohorte.')]
E += [P('6.2 Varios cortes temporales', H2), P('La entrega 1 se validó con un solo corte. Ahora se repite el entrenamiento para cada año de prueba entre 2022 y 2025, usando solo años anteriores.'),
      tabla([['Año de prueba', 'Entrenamiento', 'Cohortes de prueba', 'Modelo', 'Retención previa', 'Media']] + [[r.anio_prueba, r.anios_entrenamiento, r.filas_prueba, f'<b>{f(r.MAE)}</b>', f(r.MAE_base_ret_prev), f(r.MAE_base_media)] for _, r in VT.iterrows()], [26, 28, 30, 24, 30, 24],
            'Tabla 3. MAE por corte (evidencia/validacion_temporal.csv). El modelo gana en los cuatro; el error baja a medida que hay más años de entrenamiento.'),
      fig('fig_validacion_temporal', 135, 'Figura 4. Error del modelo y de las líneas base en cada corte temporal.')]
E += [KeepTogether([P('6.3 Cupos: de la proporción a los estudiantes', H2), P('Como el uso previsto es dimensionar cupos, se compara el número esperado de estudiantes que continúan (n<sub>t</sub> × estimación) con el observado en 2026, por cohorte y sumando por programa.'),
      tabla([['Estimador', 'MAE por cohorte', 'WAPE cohorte', 'MAE por programa', 'WAPE programa', 'Sesgo total']] + [[i, f(r.MAE_est_por_cohorte, 2), f(r.WAPE_cohorte), f(r.MAE_est_por_programa, 2), f(r.WAPE_programa), f(r.sesgo_total_pct, 1) + ' %'] for i, r in CUP.iterrows()], [52, 24, 22, 26, 24, 22],
            f"Tabla 4. Sobre {miles(R['cupos']['obs_total'])} estudiantes que continúan, el modelo tiene el menor error por cohorte. Sumado por programa empata con la retención previa ({f(cm_.MAE_est_por_programa, 2)} contra {f(cr.MAE_est_por_programa, 2)}): parte de los errores por cohorte se compensan entre sí. El sesgo de {f(cm_.sesgo_total_pct, 1)} % indica que subestima levemente.")])]
E += [P('6.4 Análisis de errores', H2), tabla([['Tamaño de la cohorte', 'Cohortes', 'Observado medio', 'Estimado medio', 'MAE', 'Sesgo']] + [[i, int(r.cohortes), f(r.observado_medio), f(r.prediccion_media), f(r.MAE), f(r.sesgo)] for i, r in TAM.iterrows()], [40, 22, 30, 30, 22, 22],
      'Tabla 5. El error se concentra en cohortes de 5 a 19 estudiantes, donde una persona mueve varios puntos. En las de 5 a 9 el modelo subestima de forma sistemática (sesgo −0,11): conviene usarlo con cautela en programas pequeños.'),
      P(f"<b>Robustez.</b> Se perturbó una variable a la vez en las cohortes de prueba. Arancel ±5% casi no mueve la predicción; edad media ±1 año la mueve más de 2 puntos en el 2–3% de las cohortes; retención previa −5 puntos la mueve más de 2 puntos en el {round(ROB.iloc[0].sobre_2pp*100)}% de las cohortes (máximo {round(ROB.iloc[0].cambio_abs_max*100)} puntos). Es la contracara de un modelo por tramos: es más preciso en promedio, pero algunas cohortes cerca de un corte del árbol cambian de forma escalonada (evidencia/robustez.csv).")]
nb = len(BIT); okb = int((BIT.resultado == 'Cumple').sum())
E += [P('6.5 Pruebas del prototipo', H2), P(
    f"<b>Bitácora.</b> {okb} de {nb} casos cumplen: 20 de una cohorte (normal, inválidos, límites, no finitos, categorías, coherencia, unidades, alcance y opcionales) y 5 nuevos del modo lote, agregados por la retroalimentación de la entrega 1: cohorte duplicada (CP-21), fila de ingreso rechazada (CP-22), ingreso entregado por el usuario (CP-23), totales iguales a la suma de filas aceptadas (CP-24) y cohorte fuera de alcance en un lote (CP-25). En los rechazos el modelo no se llama. "
    f"<b>Escenarios.</b> <i>pruebas_escenarios.py</i> ejecuta {miles(ESC['total'])} escenarios (campos con todos los tipos de valor y límites, categorías, grilla de años × duración, 40.000 combinaciones aleatorias o mutadas, un lote mezclado y envíos al formulario web) y compara cada resultado con un verificador escrito aparte, que ahora incluye el alcance y la regla de cohorte única: {miles(ESC['cumplen'])} de {miles(ESC['total'])} cumplen, sin excepciones. "
    f"<b>Adversarias.</b> {int((ADV.resultado == 'Cumple').sum())} de {len(ADV)} casos pensados para romper la aplicación cumplen (tipos de numpy, números extremos, Unicode, CSV de Excel, concurrencia, servidor web, integridad del modelo y duplicados escritos de otra forma)."),
    P("<b>Qué no cubrían las pruebas de la entrega 1.</b> Las suites verificaban que el lote no fallara, pero no que sus totales fueran correctos: el profesor encontró que una cohorte duplicada se sumaba dos veces y que una fila rechazada aportaba al supuesto de primer año. Se corrigió el código, se agregaron casos que comprueban los totales y se repitieron todas las suites.")]
# 8. riesgos
E += [P('7. Riesgos, ética, seguridad, sesgos, privacidad e impacto', H1), P(
    "<b>Privacidad.</b> Bases públicas anonimizadas; el repositorio contiene solo cohortes agregadas, sin MRUN, fechas de nacimiento ni registros individuales, y sin credenciales. "
    "<b>Sesgos.</b> El modelo usa proporción de mujeres y edad media de la cohorte como predictores, y subestima en cohortes pequeñas; usarlo sin cuidado podría subdimensionar la oferta de programas pequeños. No se hizo una evaluación formal de equidad. "
    "<b>Alcance.</b> Aplicar el modelo a CFT o IP daría estimaciones sin respaldo; la aplicación las rechaza con un mensaje claro en lugar de predecir. "
    "<b>Impacto y uso previsto.</b> Apoya la planificación de recursos; no debe usarse para decidir sobre estudiantes ni para cerrar programas. "
    "<b>Seguridad.</b> Validación de cada campo, rechazo de valores no finitos y booleanos, límites de tamaño en el servidor web y verificación de la huella del modelo antes de cargarlo, porque un archivo .joblib puede ejecutar código al cargarse. "
    "<b>Licencias.</b> Datos de fuente pública oficial sin licencia declarada (sección 3); scikit-learn, pandas, numpy, joblib y matplotlib son software libre. "
    "<b>Mitigaciones.</b> Avisos por rango de entrenamiento y por cohortes sin historial; error típico junto a cada resultado; ingreso nuevo marcado como supuesto o «sin dato»; filas excluidas informadas en los cupos.")]
# 9. límites
E += [P('8. Limitaciones y trabajo futuro', H1), P(
    "<b>Limitaciones.</b> (1) Muestra del 4% de los programas. (2) Los mismos programas están en entrenamiento y prueba; no se midió desempeño en programas nuevos. (3) El objetivo cuenta como «no continúa» un cambio de código de programa. (4) Mayor error y subestimación en cohortes de 5 a 9 estudiantes. (5) Por programa, el modelo empata con la retención previa. (6) No estima el ingreso nuevo ni cupos por asignatura. (7) El año de estudio es nominal (año observado − año de ingreso + 1): un estudiante que repite cuenta en su año nominal aunque curse asignaturas de años anteriores. (8) Los cupos solo suman a quienes siguen en su cohorte; no incluyen traslados desde otros programas ni reincorporaciones, que el usuario debe agregar si son relevantes. "
    "<b>Trabajo futuro.</b> Reentrenar con todas las universidades (las bases completas están disponibles en el mismo portal); reconciliar códigos de programa entre años, lo que permitiría reincorporar CFT e IP; ajustar la profundidad del bosque (la 8 mejora levemente en validación); estimar un intervalo de incertidumbre por cohorte; modelar el ingreso nuevo; y conectar mallas curriculares para pasar de cupos por año a cupos por asignatura.")]
E += [P('9. Conclusiones', H1), P(
    f"El prototipo cumple el flujo completo (entrada, validación, modelo y cupos) con evidencia reproducible. Limitar el alcance a universidades hizo que el objetivo mida continuidad real y no cambios de códigos; con ese alcance, Random Forest anticipa la continuidad mejor que Ridge y que las líneas base en los cuatro cortes temporales (MAE {f(m.MAE)} en 2025). "
    f"En estudiantes, el error medio es de {f(cm_.MAE_est_por_cohorte, 2)} por cohorte: útil para planificar, no para fijar cupos exactos. La corrección del modo lote cierra las dos fallas que encontró la evaluación de la entrega 1. Las mejoras de mayor valor son reconciliar códigos de programa y medir el desempeño en programas no vistos.")]
E += [P('10. Referencias y fuentes', H1),
      P("Ministerio de Educación de Chile. «Matrícula en educación superior». Portal de datos abiertos. https://datosabiertos.mineduc.cl/matricula-en-educacion-superior/ (consultado el 21-11-2026). Muestra del 4% de los programas entregada en el curso.", REF),
      P("Breiman, L. (2001). Random Forests. <i>Machine Learning</i>, 45(1), 5–32. https://doi.org/10.1023/A:1010933404324. Respalda que el error del bosque se estabiliza al aumentar el número de árboles.", REF),
      P("Servicio de Información de Educación Superior (SIES), Ministerio de Educación (2018). <i>Informe Retención de 1er año de Pregrado, cohortes 2013–2017</i>. Copia disponible en https://analisis.umag.cl/documentos/retencion_1er_ano_sies_2018.pdf (consultado el 26-11-2026). Define la retención de 1.er año y entrega las tasas por tipo de institución citadas en la sección 2.", REF),
      P("Tinto, V. (1975). Dropout from higher education: A theoretical synthesis of recent research. <i>Review of Educational Research</i>, 45(1), 89–125. Modelo de referencia sobre deserción en educación superior.", REF),
      P("scikit-learn. «Common pitfalls and recommended practices» (documentación 1.9.1). https://scikit-learn.org/stable/common_pitfalls.html (consultado el 21-11-2026). Respalda ajustar el preprocesamiento solo con datos de entrenamiento y usar Pipeline para evitar fuga de datos.", REF),
      P("scikit-learn. «RandomForestRegressor» (documentación 1.9.1). https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html (consultado el 21-11-2026). Describe el modelo y los parámetros n_estimators, max_depth y random_state. El modelo se entrenó con scikit-learn 1.8.0.", REF),
      P("scikit-learn. «TimeSeriesSplit» (documentación 1.9.1). https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html (consultado el 21-11-2026). Explica por qué con datos ordenados en el tiempo no conviene la validación aleatoria: se entrenaría con datos futuros y se evaluaría con pasados.", REF),
      P("Docente del curso. «Proyecto Integrador: calendario, descripción de entregables y rúbrica de evaluación» (v02, 30-09-2026), y retroalimentación de la evaluación EVAL-01.", REF)]
E += [P('11. Anexo: uso de IA generativa e integridad académica', H1), P(
    "<b>Herramienta.</b> Claude (Anthropic), en conversación con un entorno de ejecución de código. "
    "<b>Forma de uso.</b> El equipo definió el problema, el alcance y el diseño. También escribió la primera versión del código, los análisis, la documentación y el informe. La IA se usó después, sobre ese material, para corregir errores, mejorar y ordenar el código, ampliar las pruebas y pulir la redacción. No produjo resultados por sí misma: las métricas, tablas y figuras salen de ejecutar el código del repositorio. "
    "<b>Verificación.</b> Cada cambio sugerido por la IA se revisó y se volvió a ejecutar antes de incorporarlo. Las referencias se abrieron y se comprobó que respaldan lo afirmado."),
    tabla([['Área', 'Trabajo del equipo', 'Aporte de la IA', 'Cómo se comprobó'],
           ['Aplicación y scripts', 'Primera versión de validación, predicción, modo lote, entrenamiento, comparación y validación', 'Corrección de errores, reorganización y mejoras', 'Suites de prueba y ejecución de la aplicación'],
           ['Corrección del modo lote', 'Identificó las fallas de la entrega 1 y definió las reglas nuevas', 'Apoyo para implementar y depurar', 'CP-21 a CP-24'],
           ['Alcance y elección del modelo', 'Análisis por tipo de institución, decisión de limitar a universidades y cambio a Random Forest según el criterio del PI-02', 'Revisión del análisis y apoyo en la comparación', 'evidencia/alcance_por_tipo.csv y comparacion_modelos.csv'],
           ['Validación temporal', 'Decidió agregar cortes por la observación del profesor', 'Apoyo para implementarlos', 'evidencia/validacion_temporal.csv'],
           ['Página web, notebook, figuras y repositorio', 'Diseño y contenido', 'Mejoras de presentación y orden', 'Ejecución de la aplicación y del notebook'],
           ['Informe y presentación', 'Estructura y redacción', 'Revisión de redacción y formato', 'Cifras contrastadas con evidencia/']], [34, 56, 40, 40]),
    P("<b>Datos personales y credenciales.</b> No se cargaron. <b>Defensa.</b> Las respuestas serán del equipo, sin IA en tiempo real.")]
if __name__ == '__main__':
    SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                  title='Informe técnico · Continuidad de cohortes y cupos', author='Ivan Oliva y Bastian Gonzalez').build(E, onFirstPage=portada, onLaterPages=pie)
    print('ok')
