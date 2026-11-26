"""Suite exhaustiva de escenarios. El resultado esperado lo calcula un verificador escrito aparte, solo desde el contrato
(no reutiliza la lógica de cupos_app). Cualquier discrepancia es un defecto de la app.
Uso:  python pruebas_escenarios.py    (escribe evidencia/pruebas_escenarios.csv y evidencia/resumen_escenarios.json)"""
import json, os, random, threading, time, copy, urllib.request, urllib.parse, math
import numpy as np, pandas as pd
import cupos_app as app

M = app.Modelo()
BASE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datos_ejemplo', 'caso_valido.json'), encoding='utf-8'))
CAT = M.categorias
ALCANCE = {'tipo_inst_1': ['Universidades']}   # definido aquí, no leído de la app
# --- contrato escrito de nuevo, independiente de cupos_app: campo -> (entero?, minimo, maximo, obligatorio)
SPEC = {'anio_t': (True, 2019, 2040, True), 'anio_ingreso': (True, 1990, None, True), 'n_t': (True, 5, 1_000_000, True),
        'prog_total_t': (True, 1, 1_000_000, True), 'n_prev': (True, 1, 1_000_000, False), 'ret_prev': (False, 0, 1, False),
        'prop_mujer': (False, 0, 1, True), 'edad_media': (False, 14, 90, False), 'dur_semestres': (True, 1, 20, True),
        'arancel_anual_clp': (False, 10000, 10_000_000_000, False)}

def esperado(e):
    """Devuelve ('error', None) o ('ok', n_avisos_minimo) segun el contrato."""
    if not isinstance(e, dict): return 'error'
    if set(e) - set(SPEC) - set(CAT): return 'error'
    for k, (ent, lo, hi, obl) in SPEC.items():
        v = e.get(k)
        if v is None:
            if obl: return 'error'
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)) or (isinstance(v, float) and not math.isfinite(v)): return 'error'
        if ent and v != int(v): return 'error'
        if lo is not None and v < lo: return 'error'
        if hi is not None and v > hi: return 'error'
    for c, opciones in CAT.items():
        # el contrato acepta mayúsculas/minúsculas y espacios sobrantes en las categorías (se normalizan al valor oficial)
        if not isinstance(e.get(c), str) or e[c].strip().casefold() not in {o.casefold() for o in opciones}: return 'error'
        # el modelo solo cubre universidades: otro tipo de institución se rechaza aunque sea una categoría conocida
        if c in ALCANCE and e[c].strip().casefold() not in {o.casefold() for o in ALCANCE[c]}: return 'error'
    if e['anio_ingreso'] > e['anio_t'] or e['n_t'] > e['prog_total_t']: return 'error'
    if (e.get('n_prev') is None) != (e.get('ret_prev') is None): return 'error'
    nueva = e['anio_ingreso'] == e['anio_t']
    if nueva and e.get('n_prev') is not None: return 'error'
    if e['anio_t'] - e['anio_ingreso'] + 1 >= e['dur_semestres'] / 2: return 'error'
    return 'ok'

FILAS = []; DEFECTOS = []; EXC = 0
def correr(grupo, nombre, entrada, campo=None):
    """Ejecuta un escenario y lo compara con el verificador. campo: si se espera rechazo, el campo que debe nombrarse."""
    global EXC
    ll = M.llamadas; esp = esperado(entrada)
    try: r = app.predecir(M, copy.deepcopy(entrada))
    except Exception as ex:
        EXC += 1; r = dict(estado='EXCEPCION', errores=[repr(ex)], advertencias=[])
    llamo = M.llamadas - ll; obs = 'ok' if r['estado'] == 'OK' else 'error'
    ok = obs == esp and r['estado'] != 'EXCEPCION'
    if esp == 'error': ok = ok and llamo == 0 and (campo is None or any(campo in m for m in r['errores']))
    else: ok = ok and llamo == 1 and 0 <= r['prediccion'] <= 1 and np.isfinite(r['prediccion'])
    FILAS.append(dict(grupo=grupo, escenario=nombre, esperado=esp, observado=obs, llamadas_modelo=llamo,
                      prediccion=r.get('prediccion'), n_avisos=len(r.get('advertencias', [])), resultado='Cumple' if ok else 'FALLA',
                      mensaje=' | '.join(r.get('errores', []) + r.get('advertencias', []))[:200]))
    if not ok: DEFECTOS.append(FILAS[-1])
    return r

# 1) cada campo numérico con todos los tipos de valor
POOL = lambda lo, hi, ent: ([None, '', 'abc', True, False, float('nan'), float('inf'), float('-inf'), [1], {'a': 1}, '5'] +
        ([lo - 1, lo, lo + 1] if lo is not None else []) + ([hi - 1, hi, hi + 1] if hi is not None else []) + ([lo + 0.5] if ent and lo is not None else []))
def invalido_solo(k, v):
    """True si el valor, por sí solo (sin mirar otros campos), viola el contrato del campo."""
    ent, lo, hi, obl = SPEC[k]
    if v is None: return obl
    if isinstance(v, bool) or not isinstance(v, (int, float)) or (isinstance(v, float) and not math.isfinite(v)): return True
    return (ent and v != int(v)) or (lo is not None and v < lo) or (hi is not None and v > hi)
for k, (ent, lo, hi, obl) in SPEC.items():
    for v in POOL(lo, hi, ent):
        e = {**BASE, k: v}
        # el mensaje debe nombrar el campo solo cuando el valor es inválido por sí mismo; si el rechazo viene de una regla cruzada, solo se exige el rechazo
        correr('campo numérico', f'{k} = {v!r}', e, campo=k if invalido_solo(k, v) else None)
# 2) cada categoría: todas las válidas y varias inválidas
for c, ops in CAT.items():
    for o in ops: correr('categoría válida', f'{c} = {o}', {**BASE, c: o})
    for v in [None, '', 'Narnia', 5, True, ops[0].lower(), ops[0] + ' ', ['x']]: correr('categoría inválida', f'{c} = {v!r}', {**BASE, c: v}, campo=c)
# 3) campos extra, faltantes y entrada que no es diccionario
for k in list(BASE):
    e = {a: b for a, b in BASE.items() if a != k}; correr('campo faltante', f'sin {k}', e, campo=k if esperado(e) == 'error' and k not in ('n_prev', 'ret_prev') else None)
correr('campo extra', 'campo desconocido', {**BASE, 'extra': 1}, campo='extra')
for nombre, v in [('None', None), ('lista', [1, 2]), ('texto', 'hola'), ('diccionario vacío', {}), ('número', 5)]: correr('entrada no válida', nombre, v)
# 4) coherencia entre campos: grilla de año observado, año de ingreso y duración
for t in (2019, 2025, 2040):
    for off in range(-12, 3):
        for dur in range(1, 21):
            e = {**BASE, 'anio_t': t, 'anio_ingreso': t + off, 'dur_semestres': dur, 'n_prev': None, 'ret_prev': None}
            correr('grilla años × duración', f't={t} ingreso={t+off} dur={dur}', e)
# 5) n_t frente a prog_total_t, y pares n_prev / ret_prev
for nt in (5, 6, 25, 26, 27, 100):
    for pt in (1, 5, 26, 100): correr('n_t × prog_total_t', f'n_t={nt} prog_total_t={pt}', {**BASE, 'n_t': nt, 'prog_total_t': pt})
for npv in (None, 1, 18):
    for rp in (None, 0, 0.5, 1):
        for ing in (2024, 2025): correr('n_prev × ret_prev × cohorte nueva', f'n_prev={npv} ret_prev={rp} ingreso={ing}', {**BASE, 'n_prev': npv, 'ret_prev': rp, 'anio_ingreso': ing})
# 6) fuzz: 20.000 combinaciones aleatorias
rnd = random.Random(7)
def valor(k):
    ent, lo, hi, obl = SPEC[k]; r = rnd.random()
    if r < .70:
        a = lo if lo is not None else 0; b = hi if hi is not None else (lo * 200 if lo else 5000)
        if k.startswith('anio'): return rnd.randint(2018, 2041)
        return rnd.randint(int(a), int(b)) if ent else round(rnd.uniform(a, b), 4)
    if r < .80: return None
    return rnd.choice(['x', True, float('nan'), float('inf'), -1, 0, 10 ** 9, 2.5, '', [1]])
for i in range(20000):
    e = {k: valor(k) for k in SPEC}
    for c, ops in CAT.items(): e[c] = rnd.choice(ops) if rnd.random() < .93 else rnd.choice([None, 'Narnia', 3])
    if rnd.random() < .5 and isinstance(e['anio_t'], int) and e['anio_t'] > 2018: e['anio_ingreso'] = rnd.randint(e['anio_t'] - 6, e['anio_t'])
    if rnd.random() < .5 and isinstance(e['n_t'], int): e['prog_total_t'] = e['n_t'] + rnd.randint(0, 200)
    if rnd.random() < .6: e['n_prev'] = rnd.randint(1, 80) if rnd.random() < .5 else None; e['ret_prev'] = round(rnd.random(), 3) if e['n_prev'] is not None else None
    correr('fuzz', f'aleatorio {i}', e)
# 6b) fuzz por mutación: se parte de una entrada válida y se alteran 0, 1 o 2 campos
def valida():
    dur = rnd.randint(2, 16); ys = rnd.randint(1, max(1, math.ceil(dur / 2) - 1)); t = rnd.randint(2019, 2035)
    nt = rnd.randint(5, 300); nueva = ys == 1
    e = dict(anio_t=t, anio_ingreso=t - ys + 1, n_t=nt, prog_total_t=nt + rnd.randint(0, 500), n_prev=None if nueva else rnd.randint(1, 300),
             ret_prev=None, prop_mujer=round(rnd.random(), 4), edad_media=rnd.choice([None, round(rnd.uniform(17, 45), 2)]),
             dur_semestres=dur, arancel_anual_clp=rnd.choice([None, float(rnd.randint(500_000, 8_000_000))]))
    if not nueva: e['ret_prev'] = round(rnd.random(), 4)
    for c, ops in CAT.items(): e[c] = rnd.choice(ops)
    return e
MUT = [None, '', 'x', True, float('nan'), float('inf'), -1, 0, 4, 10 ** 9, 2.5, [1], 1.5, 55.0]
for i in range(20000):
    e = valida()
    for _ in range(rnd.choice([0, 0, 1, 1, 2])):
        k = rnd.choice(list(e)); e[k] = rnd.choice(MUT) if k in SPEC else rnd.choice([None, 'Narnia', 3, e[k]])
    correr('fuzz por mutación', f'mutación {i}', e)
# 7) el mismo caso dos veces da lo mismo y no se modifica la entrada
e = copy.deepcopy(BASE); r1 = app.predecir(M, e); r2 = app.predecir(M, e)
FILAS.append(dict(grupo='determinismo', escenario='misma entrada dos veces', esperado='igual', observado='igual' if r1 == r2 else 'distinto', llamadas_modelo=2, prediccion=r1['prediccion'],
                  n_avisos=len(r1['advertencias']), resultado='Cumple' if r1 == r2 and e == BASE else 'FALLA', mensaje=''))
if FILAS[-1]['resultado'] == 'FALLA': DEFECTOS.append(FILAS[-1])
# 8) lote mezclado: filas válidas e inválidas en la misma tabla
mezcla = [BASE, {**BASE, 'arancel_anual_clp': 55.0}, {**BASE, 'n_prev': None, 'ret_prev': None}, {**BASE, 'region_sede': 'Narnia'}, {**BASE, 'anio_ingreso': 2022}, {**BASE, 'anio_ingreso': 2023}]
df = pd.DataFrame([{**m, 'programa': f'P{i}'} for i, m in enumerate(mezcla)])   # programa distinto: cada fila es una cohorte única
det, cup = app.proyectar_lote(M, df)
exp = [esperado(m) for m in mezcla]; obs = ['ok' if s == 'OK' else 'error' for s in det.estado]
lote_ok = exp == obs and set(cup.programa) == {f'P{i}' for i, x in enumerate(exp) if x == 'ok'} and det[det.estado == 'RECHAZADA'].estudiantes_esperados.isna().all()
FILAS.append(dict(grupo='lote', escenario='6 filas mezcladas (3 válidas, 3 inválidas)', esperado=str(exp), observado=str(obs), llamadas_modelo=int((det.estado == 'OK').sum()), prediccion=None,
                  n_avisos=int((det.mensajes != '').sum()), resultado='Cumple' if lote_ok else 'FALLA', mensaje=''))
if not lote_ok: DEFECTOS.append(FILAS[-1])
# 9) formulario web: el mismo flujo por HTTP
hilo = threading.Thread(target=app.servir_web, args=(M, 8791, False), daemon=True); hilo.start(); time.sleep(1.2)
def post(cambio):
    d = {k: ('' if v is None else str(v)) for k, v in BASE.items()}; d.update(cambio)
    try: return urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8791', urllib.parse.urlencode(d).encode()), timeout=10).read().decode('utf-8')
    except Exception as ex: return 'EXC ' + repr(ex)
WEB = [('caso base', {}, 'ok'), ('arancel en UF', {'arancel_anual_clp': '55'}, 'error'), ('n_t = 4', {'n_t': '4'}, 'error'), ('ret_prev con coma', {'ret_prev': '0,5'}, 'ok'),
       ('campos opcionales vacíos', {'n_prev': '', 'ret_prev': '', 'edad_media': '', 'arancel_anual_clp': ''}, 'ok'), ('texto en n_t', {'n_t': 'diez'}, 'error'),
       ('región inválida', {'region_sede': 'Narnia'}, 'error'), ('CFT fuera de alcance', {'tipo_inst_1': 'Centros de Formación Técnica'}, 'error'), ('último año', {'anio_ingreso': str(int(BASE['anio_t'] - BASE['dur_semestres'] / 2 + 1))}, 'error'),
       ('todo vacío', {k: '' for k in SPEC}, 'error'), ('inyección HTML', {'n_t': '<script>alert(1)</script>'}, 'error')]
for nombre, cambio, esp in WEB:
    h = post(cambio); ok = ('Entrada rechazada' in h) == (esp == 'error') and ('se estima que' in h) == (esp == 'ok') and 'EXC' not in h[:5] and '<script>alert' not in h
    FILAS.append(dict(grupo='formulario web', escenario=nombre, esperado=esp, observado='error' if 'Entrada rechazada' in h else ('ok' if 'se estima que' in h else '?'), llamadas_modelo=None, prediccion=None,
                      n_avisos=h.count('class="a"'), resultado='Cumple' if ok else 'FALLA', mensaje=''))
    if not ok: DEFECTOS.append(FILAS[-1])
# --- resumen
T = pd.DataFrame(FILAS); os.makedirs('evidencia', exist_ok=True); T.to_csv('evidencia/pruebas_escenarios.csv', index=False)
res = T.groupby('grupo').agg(escenarios=('resultado', 'size'), cumplen=('resultado', lambda s: int((s == 'Cumple').sum()))).reset_index()
resumen = dict(total=int(len(T)), cumplen=int((T.resultado == 'Cumple').sum()), fallas=int((T.resultado == 'FALLA').sum()), excepciones=EXC,
               por_grupo=res.to_dict('records'), rechazados_que_llegaron_al_modelo=int(T[(T.esperado == 'error') & (T.llamadas_modelo.fillna(0) > 0)].shape[0]),
               ok_con_prediccion_fuera_de_0_1=int(T[(T.observado == 'ok') & ((T.prediccion < 0) | (T.prediccion > 1))].shape[0]))
json.dump(resumen, open('evidencia/resumen_escenarios.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(res.to_string(index=False)); print(f"\nTOTAL {resumen['total']} | cumplen {resumen['cumplen']} | fallas {resumen['fallas']} | excepciones {EXC}")
for d in DEFECTOS[:25]: print('FALLA:', d['grupo'], '|', d['escenario'], '| esperado', d['esperado'], 'observado', d['observado'], '|', d['mensaje'][:100])
