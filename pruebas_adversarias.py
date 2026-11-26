"""Casos pensados para romper la aplicación: tipos raros, Unicode, números extremos, CSV mal formados, servidor, concurrencia,
línea de comandos y archivos alterados. Criterio: la app nunca debe lanzar una excepción ni colgarse; debe responder de forma
controlada (OK o rechazo con mensaje) y nunca devolver una predicción inválida.
Uso:  python pruebas_adversarias.py"""
import json, os, sys, copy, math, time, shutil, tempfile, subprocess, threading, socket, io, decimal, fractions, collections, unicodedata, urllib.request, urllib.parse
import numpy as np, pandas as pd
import cupos_app as app
AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = json.load(open(os.path.join(AQUI, 'datos_ejemplo', 'caso_valido.json'), encoding='utf-8'))
M = app.Modelo(); R = []
def reg(grupo, nombre, ok, detalle=''):
    R.append(dict(grupo=grupo, caso=nombre, resultado='Cumple' if ok else 'DEFECTO', detalle=str(detalle)[:220]))
def pred(grupo, nombre, entrada, espera=None):
    """espera: 'ok', 'error' o None (cualquiera de los dos, pero controlado y sin excepción)."""
    try: r = app.predecir(M, entrada)
    except Exception as e:
        reg(grupo, nombre, False, f'EXCEPCIÓN {type(e).__name__}: {e}'); return None
    bien = r['estado'] in ('OK', 'RECHAZADA')
    if r['estado'] == 'OK': bien = bien and np.isfinite(r['prediccion']) and 0 <= r['prediccion'] <= 1 and np.isfinite(r['estudiantes_esperados'])
    if espera == 'ok': bien = bien and r['estado'] == 'OK'
    if espera == 'error': bien = bien and r['estado'] == 'RECHAZADA' and bool(r['errores'])
    reg(grupo, nombre, bien, f"{r['estado']} " + (f"{r['prediccion']:.3f}" if r['estado'] == 'OK' else ' | '.join(r['errores'])[:140])); return r
# ---------- 1. tipos de dato de Python y numpy
G = 'tipos de dato'
pred(G, 'numpy int64/int32/float32/float64', {**BASE, 'n_t': np.int64(10), 'prog_total_t': np.int32(26), 'n_prev': np.int64(18), 'ret_prev': np.float32(.3889), 'prop_mujer': np.float64(.3)}, 'ok')
pred(G, 'numpy bool_ en proporción', {**BASE, 'prop_mujer': np.bool_(True)}, 'error')
pred(G, 'Decimal en proporción', {**BASE, 'prop_mujer': decimal.Decimal('0.3')})
pred(G, 'Fraction en proporción', {**BASE, 'prop_mujer': fractions.Fraction(3, 10)})
pred(G, 'número complejo', {**BASE, 'prop_mujer': 1 + 2j}, 'error')
pred(G, 'bytes en n_t', {**BASE, 'n_t': b'10'}, 'error')
pred(G, 'conjunto en n_t', {**BASE, 'n_t': {10}}, 'error')
pred(G, 'n_t entero escrito como float 10.0', {**BASE, 'n_t': 10.0}, 'ok')
pred(G, 'anio_t como float 2025.0', {**BASE, 'anio_t': 2025.0}, 'ok')
pred(G, 'n_t texto numérico "10"', {**BASE, 'n_t': '10'}, 'error')
pred(G, 'OrderedDict como entrada', collections.OrderedDict(BASE), 'ok')
pred(G, 'pandas Series como entrada', pd.Series(BASE), 'error')
pred(G, 'claves que no son texto (mezcla int y str)', {**BASE, 1: 'a', 2: 'b'}, 'error')
pred(G, 'claves tupla', {**BASE, (1, 2): 'a'}, 'error')
pred(G, 'orden de claves distinto', dict(reversed(list(BASE.items()))), 'ok')
# ---------- 2. números extremos
G = 'números extremos'
pred(G, 'n_t = 10**30', {**BASE, 'n_t': 10 ** 30, 'prog_total_t': 10 ** 30 + 1})
pred(G, 'n_t = 1e308', {**BASE, 'n_t': 1e308, 'prog_total_t': 1e308})
pred(G, 'arancel = 1e308', {**BASE, 'arancel_anual_clp': 1e308})
pred(G, 'arancel = 1.7976931348623157e308 (máximo float)', {**BASE, 'arancel_anual_clp': sys.float_info.max})
pred(G, 'prop_mujer denormal 5e-324', {**BASE, 'prop_mujer': 5e-324}, 'ok')
pred(G, 'ret_prev = 1.0000000000000002 (justo sobre 1)', {**BASE, 'ret_prev': 1.0000000000000002}, 'error')
pred(G, 'ret_prev = 0.9999999999999999', {**BASE, 'ret_prev': 0.9999999999999999}, 'ok')
pred(G, 'ret_prev = -0.0', {**BASE, 'ret_prev': -0.0}, 'ok')
pred(G, 'n_t = 4.999999999999999', {**BASE, 'n_t': 4.999999999999999}, 'error')
pred(G, 'n_t = 5.0000000000000001 (igual a 5.0)', {**BASE, 'n_t': 5.0000000000000001}, 'ok')
pred(G, 'edad_media = 14 y 90 (límites)', {**BASE, 'edad_media': 14}, 'ok'); pred(G, 'edad_media = 90', {**BASE, 'edad_media': 90}, 'ok')
pred(G, 'dur_semestres = 20 con ingreso antiguo', {**BASE, 'dur_semestres': 20, 'anio_ingreso': 2017}, 'ok')
pred(G, 'anio_ingreso = 1990 (mínimo) con dur 20 y anio_t 2025', {**BASE, 'anio_ingreso': 1990, 'dur_semestres': 20}, 'error')
pred(G, 'anio_t = 2040 con ingreso 2039', {**BASE, 'anio_t': 2040, 'anio_ingreso': 2039}, 'ok')
# ---------- 3. texto y Unicode en categorías
G = 'texto y Unicode'
reg_ok = BASE['region_sede']
nfd = unicodedata.normalize('NFD', 'Valparaíso'); nfc = 'Valparaíso'
r = pred(G, 'región "Valparaíso" con tilde descompuesta (NFD, pegado desde Mac)', {**BASE, 'region_sede': nfd}); 
if r is not None: reg(G, '  -> debería aceptarse como válida (misma palabra)', r['estado'] == 'OK', r['estado'])
pred(G, 'región con espacio al final', {**BASE, 'region_sede': reg_ok + ' '}); 
pred(G, 'región con espacio inicial', {**BASE, 'region_sede': ' ' + reg_ok})
pred(G, 'región en MAYÚSCULAS', {**BASE, 'region_sede': reg_ok.upper()})
pred(G, 'región con espacio de no separación (U+00A0)', {**BASE, 'region_sede': reg_ok.replace(' ', ' ')})
pred(G, 'región con carácter nulo', {**BASE, 'region_sede': reg_ok + '\x00'}, 'error')
pred(G, 'región con carácter de ancho cero', {**BASE, 'region_sede': reg_ok + '​'}, 'error')
t0 = time.time(); r = pred(G, 'región de 1 MB de texto', {**BASE, 'region_sede': 'A' * 1_000_000}, 'error')
if r is not None: reg(G, '  -> el mensaje de error no debe repetir el 1 MB', max(len(m) for m in r['errores']) < 2000, f"largo del mensaje {max(len(m) for m in r['errores'])}")
pred(G, 'emoji en categoría', {**BASE, 'jornada': '😀'}, 'error')
# duplicados escritos de otra forma siguen siendo la misma cohorte
G = 'lote'
d, c = app.proyectar_lote(M, pd.DataFrame([{**BASE, 'programa': 'P1'}, {**BASE, 'programa': ' P1 ', 'anio_ingreso': float(BASE['anio_ingreso'])}]))
reg(G, 'duplicado con espacios en programa y año como 2024.0', (d.estado == 'DUPLICADA').all() and len(c) == 0, str(d.estado.tolist()))
d, c = app.proyectar_lote(M, pd.DataFrame([{**BASE, 'programa': 'P1'}, {**BASE, 'programa': 'P2'}]))
reg(G, 'misma cohorte en programas distintos no es duplicado', (d.estado == 'OK').all(), str(d.estado.tolist()))
# ---------- 4. consistencia
G = 'consistencia'
a = app.predecir(M, BASE); b = app.predecir(M, {**BASE, 'n_t': float(BASE['n_t']), 'anio_t': float(BASE['anio_t'])})
reg(G, 'entero y float equivalente dan igual resultado', a['prediccion'] == b['prediccion'])
u = app.predecir(M, BASE)['prediccion']; lote = app.proyectar_lote(M, pd.DataFrame([{**BASE, 'programa': f'P{i}'} for i in range(3)]))[0].continuidad
reg(G, 'caso individual = fila de lote', np.allclose(lote, u, atol=1e-12))
ent = copy.deepcopy(BASE); app.predecir(M, ent); reg(G, 'predecir no modifica la entrada', ent == BASE)
base_sin = {k: BASE[k] for k in BASE}; app.validar(M, base_sin); reg(G, 'validar no modifica la entrada', base_sin == BASE)
v = [app.predecir(M, {**BASE, 'n_t': n, 'prog_total_t': 1000})['estudiantes_esperados'] for n in (10, 20, 40)]
reg(G, 'estudiantes esperados ≈ n_t × proporción (coherencia aritmética)', all(abs(e - n * app.predecir(M, {**BASE, 'n_t': n, 'prog_total_t': 1000})['prediccion']) < 1e-9 for e, n in zip(v, (10, 20, 40))))
# ---------- 5. concurrencia
G = 'concurrencia'
res = []; errs = []
def hilo(i):
    try: res.append(app.predecir(M, {**BASE, 'n_t': 10 + i % 5})['prediccion'])
    except Exception as e: errs.append(repr(e))
ll0 = M.llamadas; hs = [threading.Thread(target=hilo, args=(i,)) for i in range(200)]
[h.start() for h in hs]; [h.join() for h in hs]
esperado_p = {n: app.predecir(M, {**BASE, 'n_t': n})['prediccion'] for n in range(10, 15)}
reg(G, '200 predicciones simultáneas sin excepción', not errs, errs[:1])
reg(G, '  -> resultados iguales a los secuenciales', all(any(abs(x - y) < 1e-12 for y in esperado_p.values()) for x in res) and len(res) == 200)
reg(G, '  -> el contador de llamadas coincide con las predicciones realizadas', M.llamadas - ll0 - 5 == 200, f'contado {M.llamadas - ll0 - 5} de 200')
# ---------- 6. lote
G = 'lote'
def lote_ok(nombre, df, **kw):
    try: d, c = app.proyectar_lote(M, df, **kw); reg(G, nombre, True, f'{len(d)} filas, estados {d.estado.value_counts().to_dict() if len(d) else {}}'); return d, c
    except Exception as e: reg(G, nombre, False, f'EXCEPCIÓN {type(e).__name__}: {e}')
cols = list(BASE)
lote_ok('tabla vacía con columnas', pd.DataFrame(columns=cols))
lote_ok('tabla sin columnas', pd.DataFrame())
lote_ok('todas las filas inválidas', pd.DataFrame([{**BASE, 'n_t': 1}] * 3))
lote_ok('falta la columna anio_t', pd.DataFrame([{k: v for k, v in BASE.items() if k != 'anio_t'}] * 2))
lote_ok('sin columna programa', pd.DataFrame([BASE]))
lote_ok('programa con valores vacíos', pd.DataFrame([{**BASE, 'programa': None}, {**BASE, 'programa': 'A'}]))
lote_ok('programa numérico', pd.DataFrame([{**BASE, 'programa': 1}, {**BASE, 'programa': 2}]))
lote_ok('filas duplicadas', pd.DataFrame([BASE] * 5))
lote_ok('columnas extra', pd.DataFrame([{**BASE, 'comentario': 'hola', 'otra': 3}]))
d = lote_ok('NaN en campos obligatorios', pd.DataFrame([{**BASE, 'n_t': np.nan}]))
if d: reg(G, '  -> debe rechazarse', d[0].estado.iloc[0] == 'RECHAZADA')
d = lote_ok('NaN en categoría', pd.DataFrame([{**BASE, 'jornada': np.nan}]))
if d: reg(G, '  -> debe rechazarse', d[0].estado.iloc[0] == 'RECHAZADA')
t0 = time.time(); big = pd.DataFrame([BASE] * 2000); d = lote_ok('2.000 filas (tiempo)', big); seg = time.time() - t0
reg(G, '  -> 2.000 filas en menos de 60 s', seg < 60, f'{seg:.1f} s')
# ---------- 7. archivos CSV
G = 'CSV'
tmp = tempfile.mkdtemp(); cols = list(BASE)
def csv(nombre, texto, enc='utf-8'):
    p = os.path.join(tmp, nombre); open(p, 'w', encoding=enc, newline='').write(texto); return p
fila = ','.join('' if BASE[c] is None else str(BASE[c]) for c in cols); enc_ = ','.join(cols)
def con(**kw):
    e = {**BASE, **kw}
    return ','.join('' if e[c] is None else str(e[c]) for c in cols)
def prueba_csv(nombre, ruta, espera_estado=None, extra=''):
    try:
        df = app._csv_a_df(ruta); d, c = app.proyectar_lote(M, df)
        est = d.estado.tolist(); bien = (espera_estado is None) or est == espera_estado
        reg(G, nombre, bien, f'estados {est} {extra} {d.mensajes.iloc[0][:100] if len(d) else ""}')
    except ValueError as e:
        # un archivo vacío debe fallar con un mensaje claro (la línea de comandos lo muestra con código 2)
        reg(G, nombre, 'vacío' in str(e) and 'vacío' in nombre, f'rechazado con mensaje claro: {e}')
    except Exception as e: reg(G, nombre, False, f'EXCEPCIÓN {type(e).__name__}: {e}')
prueba_csv('CSV normal', csv('a.csv', enc_ + '\n' + fila + '\n'), ['OK'])
prueba_csv('CSV con BOM (Excel)', csv('b.csv', '﻿' + enc_ + '\n' + fila + '\n'), ['OK'])
prueba_csv('CSV con punto y coma (Excel en español)', csv('c.csv', enc_.replace(',', ';') + '\n' + fila.replace(',', ';') + '\n'), ['OK'])
prueba_csv('CSV con saltos de línea de Windows', csv('d.csv', enc_ + '\r\n' + fila + '\r\n'), ['OK'])
prueba_csv('CSV en latin-1 (Excel antiguo)', csv('e.csv', enc_ + '\n' + fila + '\n', 'latin-1'), ['OK'])
prueba_csv('CSV solo con encabezado', csv('f.csv', enc_ + '\n'))
prueba_csv('CSV vacío', csv('g.csv', ''))
prueba_csv('arancel con texto "abc" (debe rechazar, no imputar en silencio)', csv('h.csv', enc_ + '\n' + con(arancel_anual_clp='abc') + '\n'), ['RECHAZADA'])
prueba_csv('arancel con formato chileno 2.000.000', csv('i.csv', enc_ + '\n' + con(arancel_anual_clp='"2.000.000"') + '\n'), ['OK'])
prueba_csv('arancel con símbolo $2000000', csv('j.csv', enc_ + '\n' + con(arancel_anual_clp='$2000000') + '\n'))
prueba_csv('n_t con texto "diez"', csv('k.csv', enc_ + '\n' + con(n_t='diez') + '\n'), ['RECHAZADA'])
prueba_csv('fila con menos columnas', csv('l.csv', enc_ + '\n' + ','.join(fila.split(',')[:5]) + '\n'))
prueba_csv('fila con más columnas', csv('m.csv', enc_ + '\n' + fila + ',x,y,z\n'))
prueba_csv('dos filas, una válida y una inválida', csv('n.csv', enc_ + '\n' + fila + '\n' + con(n_t=2, anio_ingreso=BASE['anio_ingreso'] - 1) + '\n'), ['OK', 'RECHAZADA'])
# ---------- 8. línea de comandos
G = 'línea de comandos'
def cli(nombre, args, espera_cod=None, no_traceback=True):
    p = subprocess.run([sys.executable, os.path.join(AQUI, 'cupos_app.py')] + args, capture_output=True, text=True, cwd=AQUI, timeout=120)
    sal = p.stdout + p.stderr; limpio = 'Traceback' not in sal
    reg(G, nombre, (limpio or not no_traceback) and (espera_cod is None or p.returncode == espera_cod), f'código {p.returncode} | {sal.strip().splitlines()[-1][:110] if sal.strip() else ""}')
cli('caso con archivo inexistente', ['caso', os.path.join(tmp, 'no_existe.json')])
open(os.path.join(tmp, 'roto.json'), 'w').write('{"anio_t": 2025,')
cli('caso con JSON mal formado', ['caso', os.path.join(tmp, 'roto.json')])
open(os.path.join(tmp, 'lista.json'), 'w').write('[1,2,3]')
cli('caso con JSON que es una lista', ['caso', os.path.join(tmp, 'lista.json')])
open(os.path.join(tmp, 'ok.json'), 'w').write(json.dumps(BASE))
cli('caso con JSON válido', ['caso', os.path.join(tmp, 'ok.json')], 0)
cli('lote con archivo inexistente', ['lote', os.path.join(tmp, 'no.csv')])
cli('lote con salida en una ruta que es un archivo', ['lote', os.path.join(AQUI, 'datos_ejemplo', 'cohortes_2025.csv'), '--salida', os.path.join(tmp, 'ok.json')])
cli('sin subcomando', [])
cli('subcomando desconocido', ['hola'])
# ---------- 9. archivos del modelo alterados
G = 'integridad'
for nombre, accion in [('modelo alterado en 1 byte', 'modelo'), ('contrato alterado', 'contrato'), ('falta el modelo', 'falta_modelo'), ('falta el contrato', 'falta_contrato'), ('modelo vacío', 'vacio')]:
    d = tempfile.mkdtemp()
    for f in ('modelo_continuidad.joblib', 'contrato_modelo.json'): shutil.copy(os.path.join(AQUI, f), d)
    if accion == 'modelo': b = bytearray(open(os.path.join(d, 'modelo_continuidad.joblib'), 'rb').read()); b[len(b) // 2] ^= 1; open(os.path.join(d, 'modelo_continuidad.joblib'), 'wb').write(b)
    if accion == 'contrato': c = json.load(open(os.path.join(d, 'contrato_modelo.json'), encoding='utf-8')); c['sha256_modelo'] = '0' * 64; json.dump(c, open(os.path.join(d, 'contrato_modelo.json'), 'w'))
    if accion == 'falta_modelo': os.remove(os.path.join(d, 'modelo_continuidad.joblib'))
    if accion == 'falta_contrato': os.remove(os.path.join(d, 'contrato_modelo.json'))
    if accion == 'vacio': open(os.path.join(d, 'modelo_continuidad.joblib'), 'wb').close()
    try: app.Modelo(d); reg(G, nombre, False, 'SE CARGÓ (debía rechazarlo)')
    except Exception as e: reg(G, nombre, True, f'{type(e).__name__}: {str(e)[:100]}')
# ---------- 10. servidor web
G = 'servidor web'
def puerto_libre():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p
PT = puerto_libre(); threading.Thread(target=app.servir_web, args=(M, PT, False), daemon=True).start(); time.sleep(1.2)
URL = f'http://127.0.0.1:{PT}'
def vivo():
    try: return b'Continuidad de cohortes' in urllib.request.urlopen(URL, timeout=5).read()
    except Exception: return False
def http(nombre, cuerpo=None, cabeceras=None, metodo=None, ruta='', espera_vivo=True, chequeo=None):
    try:
        rq = urllib.request.Request(URL + ruta, data=cuerpo, headers=cabeceras or {}, method=metodo)
        try: h = urllib.request.urlopen(rq, timeout=15).read().decode('utf-8', 'replace'); cod = 200
        except urllib.error.HTTPError as e: h = e.read().decode('utf-8', 'replace'); cod = e.code
    except Exception as e: h = 'EXC ' + repr(e); cod = None
    bien = vivo() == espera_vivo and (chequeo is None or chequeo(h, cod))
    reg(G, nombre, bien, f'http {cod}; servidor sigue vivo: {vivo()}')
formu = lambda **c: urllib.parse.urlencode({**{k: ('' if v is None else v) for k, v in BASE.items()}, **c}).encode()
http('cuerpo con bytes no UTF-8', b'n_t=\xff\xfe\xfa&anio_t=2025')
http('cuerpo de 5 MB', b'n_t=' + b'9' * 5_000_000)
http('Content-Length no numérico', b'x=1', {'Content-Length': 'abc'})
http('Content-Length negativo', b'x=1', {'Content-Length': '-5'})
http('campo repetido (n_t dos veces)', formu() + b'&n_t=4')
http('ruta inexistente /foo (GET)', ruta='/foo', chequeo=lambda h, c: c in (200, 404))
http('HEAD', metodo='HEAD', chequeo=lambda h, c: c is not None)
http('PUT', b'x=1', metodo='PUT', chequeo=lambda h, c: c is not None)
http('inyección HTML en categoría', formu(tipo_inst_1='<img src=x onerror=alert(1)>'), chequeo=lambda h, c: '<img src=x' not in h)
http('inyección HTML en campo numérico', formu(n_t='"><script>alert(1)</script>'), chequeo=lambda h, c: '<script>alert' not in h)
http('campo desconocido en el formulario', formu() + b'&foo=bar', chequeo=lambda h, c: 'Entrada rechazada' in h)
http('cuerpo vacío', b'', chequeo=lambda h, c: 'Entrada rechazada' in h)
http('100 envíos seguidos', formu())
def ráfaga():
    ok = 0
    for i in range(100):
        try: ok += b'se estima' in urllib.request.urlopen(urllib.request.Request(URL, formu()), timeout=15).read()
        except Exception: pass
    return ok
n_ok = ráfaga(); reg(G, '  -> los 100 envíos responden bien', n_ok == 100, f'{n_ok}/100')
pool = []
def cliente(i):
    try: pool.append(b'se estima' in urllib.request.urlopen(urllib.request.Request(URL, formu()), timeout=30).read())
    except Exception as e: pool.append(False)
hs = [threading.Thread(target=cliente, args=(i,)) for i in range(40)]; [h.start() for h in hs]; [h.join() for h in hs]
reg(G, '40 clientes simultáneos', sum(pool) == 40, f'{sum(pool)}/40')
# ---------- 11. formato de números escritos en el formulario
G = 'números escritos a mano'
for texto, esp in [('2000000', 2000000), ('2.000.000', 2000000), ('2,000,000', 2000000), ('2 000 000', 2000000), ('$2.000.000', 2000000), ('2000000.0', 2000000), ('2e6', 2000000), (' 2000000 ', 2000000), ('0,5', 0.5), ('0.5', 0.5), ('.5', 0.5), ('50%', 0.5), ('1e-1', 0.1), ('٣', 3)]:
    v = app._parsear(texto)
    reg(G, f'"{texto}" -> {v!r}', v == esp if esp is not None else not isinstance(v, (int, float)), f'esperado {esp!r}')
# ---------- resumen
T = pd.DataFrame(R); os.makedirs(os.path.join(AQUI, 'evidencia'), exist_ok=True); T.to_csv(os.path.join(AQUI, 'evidencia', 'pruebas_adversarias.csv'), index=False)
print(T.groupby('grupo').resultado.value_counts().unstack(fill_value=0).to_string())
print(f"\nTOTAL {len(T)} | cumplen {(T.resultado == 'Cumple').sum()} | DEFECTOS {(T.resultado == 'DEFECTO').sum()}")
for _, r in T[T.resultado == 'DEFECTO'].iterrows(): print(f"DEFECTO [{r.grupo}] {r.caso} :: {r.detalle}")
shutil.rmtree(tmp, ignore_errors=True)
