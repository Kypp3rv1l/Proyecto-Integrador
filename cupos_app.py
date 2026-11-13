"""Prototipo de anticipación de cupos: valida la entrada, aplica el modelo de continuidad ya entrenado
y convierte la estimación en estudiantes esperados por programa y año de estudio.

Uso (desde esta carpeta):
  python cupos_app.py demo
  python cupos_app.py caso entrada.json
  python cupos_app.py lote datos_ejemplo/cohortes_2025.csv --salida resultados
  python cupos_app.py web          (formulario en el navegador para predecir en vivo)
"""
import math, sys, os, io, json, csv, re, argparse, hashlib, warnings, threading, unicodedata
import numpy as np, pandas as pd, joblib
warnings.filterwarnings('ignore')
AQUI = os.path.dirname(os.path.abspath(__file__))

def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def _limpiar(t):
    return ' '.join(unicodedata.normalize('NFC', t).replace('\u00a0', ' ').split())

def _corto(v, n=60):
    t = repr(v)
    return t if len(t) <= n else t[:n] + f'… ({len(t)} caracteres)'

class Modelo:
    """Carga el pipeline guardado y el contrato. Solo expone predict: nunca reajusta."""
    def __init__(self, carpeta=AQUI):
        self.contrato = json.load(open(os.path.join(carpeta, 'contrato_modelo.json'), encoding='utf-8'))
        ruta = os.path.join(carpeta, 'modelo_continuidad.joblib')
        if _sha256(ruta) != self.contrato['sha256_modelo']:
            raise RuntimeError('modelo_continuidad.joblib no coincide con la huella del contrato; regenerar con construir_modelo.py')
        self._pipe = joblib.load(ruta)
        self.llamadas = 0
        self._cerrojo = threading.Lock()
        self.features = self.contrato['features']
        self.categorias = self.contrato['categorias_permitidas']
        self.ref = self.contrato['referencias_numericas']
        self.min_n = self.contrato['min_n_cohorte']
        self.mae = self.contrato['prueba_2025']['MAE']
    def predict(self, X):
        with self._cerrojo:
            self.llamadas += 1
            return self._pipe.predict(X)
    def canonica(self, campo, valor):
        """Devuelve la categoría oficial que corresponde al texto (sin distinguir mayúsculas ni tildes descompuestas ni espacios de más), o None."""
        if not isinstance(valor, str) or len(valor) > 200:
            return None
        buscado = _limpiar(valor).casefold()
        for oficial in self.categorias[campo]:
            if _limpiar(oficial).casefold() == buscado:
                return oficial
        return None

# Campos de negocio: (nombre, tipo, minimo, maximo, obligatorio, unidad)
NUMERICOS = [
    ('anio_t', 'entero', 2019, 2040, True, 'año'),
    ('anio_ingreso', 'entero', 1990, None, True, 'año'),
    ('n_t', 'entero', 5, 1_000_000, True, 'estudiantes'),
    ('prog_total_t', 'entero', 1, 1_000_000, True, 'estudiantes'),
    ('n_prev', 'entero', 1, 1_000_000, False, 'estudiantes'),
    ('ret_prev', 'real', 0.0, 1.0, False, 'proporción'),
    ('prop_mujer', 'real', 0.0, 1.0, True, 'proporción'),
    ('edad_media', 'real', 14, 90, False, 'años'),
    ('dur_semestres', 'entero', 1, 20, True, 'semestres'),
    ('arancel_anual_clp', 'real', 10_000, 10_000_000_000, False, 'pesos chilenos por año'),
]
CATEGORICOS = ['tipo_inst_1', 'area_conocimiento', 'region_sede', 'jornada', 'modalidad',
               'nivel_carrera_1', 'acreditada_carr', 'acreditada_inst', 'tipo_plan_carr']
CAMPOS = [c[0] for c in NUMERICOS] + CATEGORICOS

def _numero(v):
    if not isinstance(v, (int, float, np.integer, np.floating)) or isinstance(v, (bool, np.bool_)):
        return False
    try:
        return math.isfinite(float(v))      # float() de un entero gigante lanza OverflowError
    except OverflowError:
        return False

def validar(m, entrada):
    """Devuelve (errores, advertencias, registro limpio). Con errores no se llama al modelo."""
    err, adv, r = [], [], {}
    if not isinstance(entrada, dict):
        return ['la entrada debe ser un diccionario campo -> valor'], [], None
    for extra in sorted(set(entrada) - set(CAMPOS), key=str)[:20]:
        err.append(f"{_corto(extra, 40)}: campo no reconocido")
    for nombre, tipo, lo, hi, obligatorio, unidad in NUMERICOS:
        v = entrada.get(nombre)
        if v is None:
            if obligatorio:
                err.append(f'{nombre}: campo obligatorio ausente')
            r[nombre] = None
            continue
        if not _numero(v):
            err.append(f'{nombre}: se espera un número ({unidad}), llegó {_corto(v)}')
            continue
        if tipo == 'entero' and float(v) != int(v):
            err.append(f'{nombre}: debe ser entero ({unidad}), llegó {_corto(v)}')
            continue
        v = int(v) if tipo == 'entero' else float(v)
        if lo is not None and v < lo:
            if nombre == 'arancel_anual_clp' and v <= 0:
                err.append(f'{nombre}={v:g}: debe ser un monto positivo en pesos chilenos por año')
            elif nombre == 'arancel_anual_clp':
                err.append(f'{nombre}={v:g}: parece estar en UF; debe informarse en pesos chilenos por año (mínimo {lo:,})')
            elif nombre == 'n_t':
                err.append(f'{nombre}={v}: una cohorte de menos de {lo} estudiantes no es estimable (el modelo se entrenó con {lo} o más)')
            else:
                err.append(f'{nombre}={v:g}: menor que el mínimo permitido ({lo} {unidad})')
            continue
        if hi is not None and v > hi:
            err.append(f'{nombre}={v:g}: mayor que el máximo permitido ({hi} {unidad})')
            continue
        r[nombre] = v
    for nombre in CATEGORICOS:
        v = entrada.get(nombre)
        if v is None:
            err.append(f'{nombre}: campo obligatorio ausente')
        elif m.canonica(nombre, v) is None:
            err.append(f'{nombre}: categoría no reconocida ({_corto(v)}); opciones: {", ".join(m.categorias[nombre])}')
        else:
            r[nombre] = m.canonica(nombre, v)
    if err:
        return err, adv, None
    # coherencia entre campos
    if r['anio_ingreso'] > r['anio_t']:
        err.append(f"anio_ingreso ({r['anio_ingreso']}) no puede ser posterior a anio_t ({r['anio_t']})")
    if r['n_t'] > r['prog_total_t']:
        err.append(f"n_t ({r['n_t']}) no puede superar prog_total_t ({r['prog_total_t']})")
    if (r['n_prev'] is None) != (r['ret_prev'] is None):
        err.append('n_prev y ret_prev deben informarse juntos o dejarse ambos vacíos')
    if err:
        return err, adv, None
    nueva = r['anio_ingreso'] == r['anio_t']
    ys = r['anio_t'] - r['anio_ingreso'] + 1
    if nueva and r['n_prev'] is not None:
        err.append('la cohorte ingresa este año: n_prev y ret_prev no existen y deben ir vacíos')
    if ys >= r['dur_semestres'] / 2:
        err.append(f"anio_ingreso: la cohorte cursa su año {ys} de {r['dur_semestres'] / 2:g}: no le queda un año nominal por delante, "
                   'la continuidad mediría titulación y el modelo no aplica')
    if err:
        return err, adv, None
    # advertencias (no bloquean)
    if not nueva and r['n_prev'] is None:
        adv.append('cohorte antigua sin n_prev/ret_prev: se imputa la mediana de entrenamiento y la estimación es menos fiable')
    for nombre in ('edad_media', 'arancel_anual_clp'):
        if r[nombre] is None:
            adv.append(f'{nombre} ausente: se imputa la mediana de entrenamiento')
    for nombre, col in [('n_t', 'n_t'), ('n_prev', 'n_prev'), ('prog_total_t', 'prog_total_t'),
                        ('arancel_anual_clp', 'arancel_pesos'), ('edad_media', 'edad_media')]:
        v = r[nombre]
        if v is not None and not (m.ref[col]['min'] <= v <= m.ref[col]['max']):
            adv.append(f"{nombre}={v:g} está fuera del rango visto en entrenamiento ({m.ref[col]['min']:g} a {m.ref[col]['max']:g}); el modelo extrapola")
    if r['n_prev'] and r['n_t'] > 1.5 * r['n_prev']:
        adv.append(f"n_t ({r['n_t']}) supera 1,5 veces n_prev ({r['n_prev']}): revisar que sea la misma cohorte")
    if r['tipo_inst_1'] == 'Centros de Formación Técnica':
        adv.append('en CFT el error de prueba 2025 fue alto (MAE 0,28) porque varios programas cambian o pierden su código al año siguiente; tomar la estimación con cautela')
    return err, adv, r

def a_features(m, r):
    ys = r['anio_t'] - r['anio_ingreso'] + 1
    dy = r['dur_semestres'] / 2
    nan = np.nan
    fila = dict(n_t=r['n_t'], n_prev=nan if r['n_prev'] is None else r['n_prev'], prog_total_t=r['prog_total_t'],
                arancel_pesos=nan if r['arancel_anual_clp'] is None else r['arancel_anual_clp'],
                ret_prev=nan if r['ret_prev'] is None else r['ret_prev'], prop_mujer=r['prop_mujer'],
                edad_media=nan if r['edad_media'] is None else r['edad_media'],
                year_of_study=ys, dur_years=dy, remaining_years=dy - ys, arancel_uf=0.0,
                **{c: r[c] for c in CATEGORICOS})
    return pd.DataFrame([fila], columns=m.features)

def predecir(m, entrada):
    err, adv, r = validar(m, entrada)
    if err:
        return dict(estado='RECHAZADA', errores=err, advertencias=adv)
    try:
        bruta = float(m.predict(a_features(m, r))[0])
        if not np.isfinite(bruta):
            raise ValueError('la estimación no es un número finito')
    except Exception as exc:
        return dict(estado='RECHAZADA', errores=[f'no se pudo estimar con esta combinación de valores ({type(exc).__name__}); revisar los datos'], advertencias=adv)
    p = min(max(bruta, 0.0), 1.0)
    if p != bruta:
        adv.append(f'la estimación del modelo ({bruta:.3f}) cayó fuera de [0, 1] y se acotó')
    return dict(estado='OK', prediccion=p, prediccion_sin_acotar=bruta, estudiantes_esperados=r['n_t'] * p,
                anio_estudio_siguiente=r['anio_t'] - r['anio_ingreso'] + 2, error_tipico_pp=round(m.mae * 100, 1),
                errores=[], advertencias=adv)

def proyectar_lote(m, cohortes, ingreso_proyectado=None):
    """cohortes: DataFrame con los campos del contrato y, opcional, la columna 'programa'.
    Devuelve (detalle por cohorte, cupos esperados por programa y año de estudio en t+1).
    Las filas inválidas se rechazan una a una; no afectan a las demás."""
    columnas = ['fila', 'programa', 'anio_t', 'anio_ingreso', 'n_t', 'estado', 'continuidad', 'estudiantes_esperados', 'anio_estudio_t1', 'mensajes']
    det = []
    for i, reg in enumerate(cohortes.to_dict('records')):
        reg = {k: (None if (isinstance(v, float) and np.isnan(v)) or v is pd.NA else v) for k, v in reg.items()}
        prog = reg.pop('programa', 'programa_unico')
        prog = 'sin_programa' if prog is None else str(prog)
        res = predecir(m, reg)
        det.append(dict(fila=i, programa=prog, anio_t=reg.get('anio_t'), anio_ingreso=reg.get('anio_ingreso'), n_t=reg.get('n_t'),
                        estado=res['estado'], continuidad=res.get('prediccion'), estudiantes_esperados=res.get('estudiantes_esperados'),
                        anio_estudio_t1=res.get('anio_estudio_siguiente'), mensajes=' | '.join(res['errores'] + res['advertencias'])))
    det = pd.DataFrame(det, columns=columnas)
    ok = det[det.estado == 'OK']
    cupos = ok.groupby(['programa', 'anio_estudio_t1']).estudiantes_esperados.sum().round(1).rename('cupos_esperados').reset_index()
    cupos['origen'] = 'continuidad (modelo)'
    # año 1 de t+1: no lo predice el modelo; se toma un ingreso proyectado dado, o el ingreso observado en t como supuesto
    dado = ingreso_proyectado or {}
    nuevos = []
    for prog, g in ok.groupby('programa'):
        valor = dado.get(prog, g[g.anio_ingreso == g.anio_t].n_t.sum())
        nuevos.append(dict(programa=prog, anio_estudio_t1=1, cupos_esperados=float(valor),
                           origen='ingreso dado' if prog in dado else 'supuesto: igual al ingreso de t'))
    cupos = pd.concat([cupos, pd.DataFrame(nuevos, columns=['programa', 'anio_estudio_t1', 'cupos_esperados', 'origen'])], ignore_index=True)
    return det, cupos.sort_values(['programa', 'anio_estudio_t1']).reset_index(drop=True)

def _mostrar(r):
    print('ESTADO:', r['estado'])
    if r['estado'] == 'OK':
        print(f"  continuidad estimada: {r['prediccion']:.3f} | estudiantes esperados: {r['estudiantes_esperados']:.1f} "
              f"| año de estudio siguiente: {r['anio_estudio_siguiente']} | error típico: ±{r['error_tipico_pp']} pp")
    for e in r['errores']:
        print('  ERROR       :', e)
    for a in r['advertencias']:
        print('  ADVERTENCIA :', a)


def _parsear(texto):
    """Texto escrito a mano -> None, int, float o el texto mismo (la validación decide si sirve).
    Acepta coma o punto decimal, separador de miles (2.000.000 o 2,000,000), espacios, $ y %."""
    if not isinstance(texto, str):
        return texto
    t = texto.strip().replace('$', '').replace(' ', '').replace('\u00a0', '')
    if t == '':
        return None
    pct = t.endswith('%')
    if pct:
        t = t[:-1]
    if re.fullmatch(r'[1-9]\d{0,2}(\.\d{3})+(,\d+)?', t):        # 2.000.000 o 2.000.000,5
        t = t.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'[1-9]\d{0,2}(,\d{3})+(\.\d+)?', t):      # 2,000,000 o 2,000,000.5
        t = t.replace(',', '')
    else:
        t = t.replace(',', '.')
    try:
        v = float(t)
    except ValueError:
        return texto.strip()
    if not np.isfinite(v):
        return texto.strip()
    if pct:
        v /= 100
    return int(v) if v.is_integer() and '.' not in t and not pct else v

PLANTILLA = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Continuidad de cohortes</title>
<style>
:root{--papel:#F1F3F6;--tinta:#16213B;--suave:#5A6482;--linea:#D3D9E3;--blanco:#fff;--mint:#6FE0BF;--hueso:#5B6785;--ambar:#FFD27A;--coral:#FFB4AB;--error:#A8201A;--foco:#3B4FD8;
--serif:"Charter","Sitka Text","Iowan Old Style",Cambria,Georgia,serif;--sans:"Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box}
html{color-scheme:light}
body{margin:0;background:var(--papel);color:var(--tinta);font:16px/1.5 var(--sans)}
.cabecera,main,footer{max-width:1120px;margin:0 auto;padding-left:1rem;padding-right:1rem}
.cabecera{padding-top:2.5rem;padding-bottom:1.5rem}
h1{font:600 clamp(2rem,4vw,2.75rem)/1.1 var(--serif);letter-spacing:-.015em;margin:0 0 .6rem}
.cabecera p{margin:0;max-width:52ch;color:var(--suave);font-size:1.0625rem}
main{display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,430px);gap:3rem;align-items:start;padding-bottom:3rem}
form{min-width:0}
.atajos{display:flex;flex-wrap:wrap;gap:1rem 2rem;align-items:flex-end;padding:0 0 1.5rem;margin-bottom:1.75rem;border-bottom:1px solid var(--linea)}
.atajos[hidden]{display:none}
.atajos label,.atajos .titulo{display:block;font-size:.875rem;font-weight:600;margin-bottom:.35rem}
.atajos select{min-width:16rem;max-width:100%}
.chips{display:flex;flex-wrap:wrap;gap:.5rem}
.chip{font:500 .875rem var(--sans);color:var(--tinta);background:var(--blanco);border:1px solid var(--linea);border-radius:999px;padding:.35rem .85rem;cursor:pointer}
.chip:hover{border-color:var(--tinta)}
.nota{margin:.35rem 0 .9rem;font-size:.875rem;color:var(--suave);max-width:60ch}
#observado{margin:.35rem 0 0}
fieldset{border:0;margin:0 0 2rem;padding:0;min-width:0}
legend{float:left;width:100%;padding:0;margin:0 0 .4rem;font:600 1.25rem/1.3 var(--serif)}
legend+*{clear:both}
.rejilla{display:grid;grid-template-columns:repeat(auto-fill,minmax(14rem,1fr));gap:1rem 1.25rem}
.campo label{display:block;font-size:.875rem;font-weight:600;margin-bottom:.3rem}
.entrada{position:relative}
input,select{width:100%;height:2.6rem;font:inherit;color:var(--tinta);background:var(--blanco);border:1px solid #AEB7C8;border-radius:6px;padding:0 .75rem}
input{padding-right:5.2rem}
input::placeholder{color:#8A93AA}
.entrada span{position:absolute;right:.75rem;top:50%;transform:translateY(-50%);font-size:.8125rem;color:var(--suave);pointer-events:none}
.campo.invalido input,.campo.invalido select{border-color:var(--error);box-shadow:0 0 0 1px var(--error);background:#FDEDEB}
input:focus-visible,select:focus-visible,.chip:focus-visible,.enviar:focus-visible{outline:3px solid var(--foco);outline-offset:2px}
.enviar{font:600 1.0625rem var(--sans);background:var(--tinta);color:#fff;border:0;border-radius:8px;padding:.85rem 1.75rem;cursor:pointer}
.enviar:hover{background:#26345A}
.enviar:disabled{opacity:.6;cursor:progress}
.panel{position:sticky;top:1.5rem;background:var(--tinta);color:#E7EAF3;border-radius:14px;padding:2rem 1.75rem;min-height:22rem}
.cifra{margin:0;font:600 clamp(4.5rem,9vw,6.5rem)/1 var(--serif);letter-spacing:-.03em;color:#fff}
.cifra small{font-size:.4em;margin-left:.08em;color:var(--mint);letter-spacing:0}
.frase{margin:.9rem 0 0;font-size:1.0625rem;line-height:1.55}
.frase b{color:#fff}
.puntos{display:flex;flex-wrap:wrap;gap:7px;margin:1.5rem 0 .9rem}
.p{display:block;width:14px;height:14px;border-radius:50%;border:1.5px solid var(--hueso);animation:aparece .35s both;animation-delay:calc(var(--i)*22ms)}
.p.queda{background:var(--mint);border-color:var(--mint)}
.puntos.fantasma{opacity:.4}
.puntos.fantasma .p{animation:none}
.leyenda{margin:0;font-size:.875rem;color:#B8C0D6}
.llave{display:inline-block;width:10px;height:10px;border-radius:50%;border:1.5px solid var(--hueso);margin:0 .4rem 0 0;vertical-align:baseline}
.llave.queda{background:var(--mint);border-color:var(--mint)}
.leyenda .llave:not(:first-child){margin-left:1.1rem}
.nota-puntos{margin:.5rem 0 0;font-size:.8125rem;color:#B8C0D6}
.error-tipico{margin:1.5rem 0 0;padding-top:1rem;border-top:1px solid #34426A;font-size:.875rem;color:#B8C0D6}
.vacio{margin:0;font-size:1.0625rem;line-height:1.55;color:#C9D0E4}
.rechazo{margin:0;font:600 2rem/1.15 var(--serif);color:var(--coral)}
.errores,.avisos{margin:1rem 0 0;padding-left:1.1rem}
.errores li{color:var(--coral);margin-bottom:.5rem}
.avisos-t{margin:1.5rem 0 0;font:600 1rem var(--sans);color:var(--ambar)}
.avisos li{color:var(--ambar);margin-bottom:.5rem;font-size:.9375rem}
code{font-family:ui-monospace,Consolas,monospace;font-size:.9em}
footer{padding-top:1.5rem;padding-bottom:2.5rem;background:linear-gradient(var(--linea),var(--linea)) center top/calc(100% - 2rem) 1px no-repeat;color:var(--suave);font-size:.875rem}
footer p{margin:0;max-width:70ch}
@keyframes aparece{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}
@media (max-width:900px){main{grid-template-columns:1fr;gap:1.5rem}.panel{position:static;order:-1;min-height:0}}
@media (prefers-reduced-motion:reduce){.p{animation:none}}
</style></head>
<body>
<header class="cabecera">
<h1>Continuidad de cohortes</h1>
<p>Estime cuántos estudiantes de una cohorte seguirán en su programa el año siguiente y planifique los cupos.</p>
</header>
<main>
<form method="post" id="form" novalidate>
<div class="atajos" id="atajos" hidden>
<div><label for="caso">Cargar un caso real</label><select id="caso"></select><p class="nota" id="observado"></p></div>
<div><span class="titulo">Probar un error</span><div class="chips" id="chips"></div></div>
</div>
%%GRUPOS%%
<button class="enviar" type="submit">Estimar continuidad</button>
</form>
<aside class="panel" id="resultado" role="status" aria-live="polite" data-malos="%%MALOS%%">%%PANEL%%</aside>
</main>
<footer><p>Modelo Ridge entrenado con la matrícula SIES 2017–2026 (muestra del 4% de los programas). Apoya la planificación de cupos; no decide sobre personas.</p></footer>
<script id="casos" type="application/json">%%CASOS%%</script>
<script>
(function () {
  var form = document.getElementById('form'), res = document.getElementById('resultado');
  var atajos = document.getElementById('atajos'), sel = document.getElementById('caso'), obs = document.getElementById('observado');
  var casos = JSON.parse(document.getElementById('casos').textContent || '[]');
  function marcar() {
    var m = (res.dataset.malos || '').split(',');
    form.querySelectorAll('.campo').forEach(function (c) {
      c.classList.toggle('invalido', m.indexOf(c.querySelector('input,select').name) >= 0);
    });
  }
  function estimar(desplazar) {
    var btn = form.querySelector('.enviar');
    btn.disabled = true; res.setAttribute('aria-busy', 'true');
    fetch(location.pathname, {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                              body: new URLSearchParams(new FormData(form)).toString()})
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (t) {
        var n = new DOMParser().parseFromString(t, 'text/html').getElementById('resultado');
        res.innerHTML = n.innerHTML; res.dataset.malos = n.dataset.malos; marcar();
        if (desplazar && window.matchMedia('(max-width:900px)').matches) res.scrollIntoView({block: 'start'});
      })
      .catch(function () {
        res.innerHTML = '<h2 class="rechazo">Sin conexión con el servidor</h2><p class="frase">Revise que <code>python cupos_app.py web</code> siga abierto en la terminal y vuelva a estimar.</p>';
      })
      .finally(function () { btn.disabled = false; res.removeAttribute('aria-busy'); });
  }
  form.addEventListener('submit', function (e) { e.preventDefault(); estimar(true); });
  form.addEventListener('input', function () { obs.textContent = ''; });
  if (casos.length) {
    sel.innerHTML = '<option value="">Elegir un caso…</option>' + casos.map(function (c, i) {
      return '<option value="' + i + '">' + c.nombre.replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</option>';
    }).join('');
    sel.addEventListener('change', function () {
      var c = casos[sel.value]; if (!c) return;
      Object.keys(c.entrada).forEach(function (k) {
        var el = form.elements[k]; if (el) el.value = c.entrada[k] === null ? '' : String(c.entrada[k]);
      });
      estimar(true);
      obs.textContent = c.observado === null || c.observado === undefined ? '' :
        'Valor observado en 2026: ' + Math.round(c.observado * 100) + '%';
    });
  } else { sel.parentNode.hidden = true; }
  [['Arancel en UF (55)', 'arancel_anual_clp', '55'], ['Solo 4 estudiantes', 'n_t', '4'], ['Retención de 1,4', 'ret_prev', '1,4']].forEach(function (e) {
    var b = document.createElement('button'); b.type = 'button'; b.className = 'chip'; b.textContent = e[0];
    b.addEventListener('click', function () { form.elements[e[1]].value = e[2]; obs.textContent = ''; estimar(true); });
    document.getElementById('chips').appendChild(b);
  });
  atajos.hidden = false;
  if (res.querySelector('.vacio')) estimar(false);
})();
</script>
</body></html>
'''

def servir_web(m, puerto=8000, abrir=True):
    """Formulario local para predecir en vivo (solo biblioteca estándar)."""
    import html, threading, webbrowser
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs
    base = json.load(open(os.path.join(AQUI, 'datos_ejemplo', 'caso_valido.json'), encoding='utf-8'))
    esc = lambda x: html.escape('' if x is None else str(x))
    casos_reales = []
    ruta_casos = os.path.join(AQUI, 'datos_ejemplo', 'casos_para_probar.json')
    if os.path.exists(ruta_casos):
        casos_reales = json.load(open(ruta_casos, encoding='utf-8'))
    ETIQ = {'anio_t': ('Año observado', 'año'), 'anio_ingreso': ('Año de ingreso de la cohorte', 'año'),
            'n_t': ('Estudiantes de la cohorte', 'estudiantes'), 'prog_total_t': ('Matrícula total del programa', 'estudiantes'),
            'n_prev': ('Cohorte el año anterior', 'estudiantes'), 'ret_prev': ('Retención del año anterior', '0 a 1'),
            'prop_mujer': ('Proporción de mujeres', '0 a 1'), 'edad_media': ('Edad media', 'años'),
            'dur_semestres': ('Duración del programa', 'semestres'), 'arancel_anual_clp': ('Arancel anual', 'CLP')}
    ETIQ_CAT = {'tipo_inst_1': 'Tipo de institución', 'area_conocimiento': 'Área de conocimiento', 'region_sede': 'Región de la sede',
                'jornada': 'Jornada', 'modalidad': 'Modalidad', 'nivel_carrera_1': 'Nivel de la carrera',
                'acreditada_carr': 'Acreditación de la carrera', 'acreditada_inst': 'Acreditación de la institución', 'tipo_plan_carr': 'Tipo de plan'}
    GRUPOS = [('La cohorte', ['anio_t', 'anio_ingreso', 'n_t', 'prog_total_t'], None),
              ('Historial y perfil', ['n_prev', 'ret_prev', 'prop_mujer', 'edad_media'],
               'La cohorte del año anterior y su retención van juntas. Déjelas vacías si la cohorte ingresa este año.'),
              ('El programa', ['dur_semestres', 'arancel_anual_clp'] + CATEGORICOS, 'El arancel va en pesos chilenos por año, no en UF.')]
    num_info = {n: un for n, tipo, lo, hi, obl, un in NUMERICOS}
    num_obl = {n: obl for n, tipo, lo, hi, obl, un in NUMERICOS}
    fmt1 = lambda x: f'{x:.1f}'.replace('.', ',')

    def campo(n, valores, malos):
        cls = ' invalido' if n in malos else ''
        v = valores.get(n)
        if isinstance(v, float) and v.is_integer():
            valores = {**valores, n: int(v)}      # 2000000.0 se muestra como 2000000
        if n in ETIQ:
            et, ud = ETIQ[n]
            ph = '' if num_obl[n] else ' placeholder="opcional"'
            return (f'<div class="campo{cls}"><label for="f_{n}">{esc(et)}</label><div class="entrada"><input id="f_{n}" name="{n}" value="{esc(valores.get(n))}" '
                    f'inputmode="decimal" autocomplete="off" title="{n}: {esc(num_info[n])}"{ph}><span>{esc(ud)}</span></div></div>')
        ops = ''.join(f'<option{" selected" if valores.get(n) == o else ""}>{esc(o)}</option>' for o in m.categorias[n])
        return (f'<div class="campo{cls}"><label for="f_{n}">{esc(ETIQ_CAT[n])}</label><div class="entrada"><select id="f_{n}" name="{n}" title="{n}">{ops}</select></div></div>')

    def panel(valores, res=None):
        """Contenido del panel de resultado y los campos a marcar como inválidos."""
        malos = []
        if res is None:
            puntos = ''.join(f'<i class="p" style="--i:{i}"></i>' for i in range(14))
            return ('<p class="vacio">Complete los datos de la cohorte y pulse «Estimar continuidad».</p>'
                    f'<div class="puntos fantasma" aria-hidden="true">{puntos}</div>'), malos
        for e in res['errores']:
            for n in list(ETIQ) + CATEGORICOS:
                if re.search(r'\b' + n + r'\b', e) and n not in malos:
                    malos.append(n)
        if res['estado'] == 'OK':
            pred, esp = res['prediccion'], res['estudiantes_esperados']
            n = int(round(float(_parsear(valores.get('n_t')) or 0))) if valores.get('n_t') is not None else 0
            n = max(n, 1)
            total = min(n, 60)
            quedan = max(0, min(total, int(round(pred * total))))
            puntos = ''.join(f'<i class="p{" queda" if i < quedan else ""}" style="--i:{i}"></i>' for i in range(total))
            nota_puntos = f'Cada punto representa unos {fmt1(n / total)} estudiantes.' if n > total else ''
            h = (f'<p class="cifra" aria-label="{pred * 100:.0f} por ciento">{pred * 100:.0f}<small>%</small></p>'
                 f'<p class="frase">De <b>{n}</b> estudiantes se estima que seguirán unos <b>{fmt1(esp)}</b> en el mismo programa el año siguiente, '
                 f'cuando cursen el año <b>{res["anio_estudio_siguiente"]}</b>.</p>'
                 f'<div class="puntos" role="img" aria-label="{quedan} de {total} puntos continúan">{puntos}</div>'
                 f'<p class="leyenda"><span class="llave queda"></span>Seguirán en el programa <span class="llave"></span>No seguirán en él</p>'
                 + (f'<p class="nota-puntos">{nota_puntos}</p>' if nota_puntos else '')
                 + f'<p class="error-tipico">Error típico de referencia: ±{esc(str(res["error_tipico_pp"]).replace(".", ","))} puntos porcentuales. Es una estimación, no una certeza.</p>')
        else:
            h = ('<h2 class="rechazo">Entrada rechazada</h2><p class="frase">El modelo no se llamó. Corrija lo siguiente y vuelva a estimar.</p>'
                 + '<ul class="errores">' + ''.join(f'<li>{esc(e)}</li>' for e in res['errores']) + '</ul>')
        if res['advertencias']:
            h += '<h3 class="avisos-t">Avisos</h3><ul class="avisos">' + ''.join(f'<li>{esc(a)}</li>' for a in res['advertencias']) + '</ul>'
        return h, malos

    def pagina(valores, res=None):
        panel_html, malos = panel(valores, res)
        grupos = ''
        for titulo, nombres, nota in GRUPOS:
            grupos += (f'<fieldset><legend>{esc(titulo)}</legend>' + (f'<p class="nota">{esc(nota)}</p>' if nota else '')
                       + '<div class="rejilla">' + ''.join(campo(n, valores, malos) for n in nombres) + '</div></fieldset>')
        casos_js = json.dumps([{'nombre': c['nombre'], 'entrada': c['entrada'], 'observado': c.get('observado_2026')} for c in casos_reales], ensure_ascii=False).replace('</', '<\\/')
        return (PLANTILLA.replace('%%GRUPOS%%', grupos).replace('%%PANEL%%', panel_html).replace('%%MALOS%%', esc(','.join(malos)))
                .replace('%%CASOS%%', casos_js)).encode('utf-8')
    class H(BaseHTTPRequestHandler):
        def _enviar(self, cuerpo):
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(cuerpo)
        def do_GET(self):
            self._enviar(pagina(base))
        def do_POST(self):
            try:
                largo = int(self.headers.get('Content-Length', 0))
            except ValueError:
                largo = -1
            if largo < 0:
                self.send_error(400, 'Content-Length inválido'); return
            if largo > 100_000:
                self.send_error(413, 'Solicitud demasiado grande'); return
            crudo_b = self.rfile.read(largo)
            datos = parse_qs(crudo_b.decode('utf-8', errors='replace'), keep_blank_values=True)
            crudo = {k[:60]: v[0][:300] for k, v in list(datos.items())[:60]}
            entrada = {k: (_parsear(v) if k in dict((n, 1) for n, *_ in NUMERICOS) else v) for k, v in crudo.items()}
            self._enviar(pagina(crudo, predecir(m, entrada)))
        def log_message(self, *a):
            pass
    ThreadingHTTPServer.daemon_threads = True
    ThreadingHTTPServer.request_queue_size = 128
    srv = ThreadingHTTPServer(('127.0.0.1', puerto), H)
    url = f'http://127.0.0.1:{puerto}'
    print('Servidor en', url, '(Ctrl+C para cerrar)')
    if abrir:
        threading.Timer(.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.server_close()

def _csv_a_df(ruta):
    """Lee un CSV de cohortes. Acepta coma, punto y coma o tabulador, BOM (Excel) y UTF-8 o Latin-1.
    Cada celda numérica se interpreta con _parsear: un texto inválido se rechaza en esa fila, no se imputa en silencio."""
    crudo = open(ruta, 'rb').read()
    try:
        texto = crudo.decode('utf-8-sig')
    except UnicodeDecodeError:
        texto = crudo.decode('latin-1')
    if not texto.strip():
        raise ValueError('el archivo CSV está vacío')
    primera = texto.splitlines()[0]
    sep = max([',', ';', '\t'], key=primera.count)
    df = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
    for n, *_ in NUMERICOS:
        if n in df:
            df[n] = df[n].map(_parsear).astype(object)
    for c in CATEGORICOS:
        if c in df:
            df[c] = df[c].map(lambda v: None if v == '' else v)
    return df

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('demo')
    c = sub.add_parser('caso'); c.add_argument('json')
    l = sub.add_parser('lote'); l.add_argument('csv'); l.add_argument('--salida', default='resultados')
    w = sub.add_parser('web'); w.add_argument('--puerto', type=int, default=8000); w.add_argument('--no-abrir', action='store_true')
    a = ap.parse_args(argv)
    m = Modelo()
    if a.cmd == 'demo':
        ejemplo = json.load(open(os.path.join(AQUI, 'datos_ejemplo', 'caso_valido.json'), encoding='utf-8'))
        print('--- caso válido ---'); _mostrar(predecir(m, ejemplo))
        malo = dict(ejemplo, arancel_anual_clp=55.0, region_sede='Narnia')
        print('\n--- caso inválido (arancel en UF y región inexistente) ---'); _mostrar(predecir(m, malo))
        print('\nllamadas al modelo:', m.llamadas, '(el inválido no llegó al modelo)')
    elif a.cmd == 'web':
        servir_web(m, a.puerto, not a.no_abrir)
    elif a.cmd == 'caso':
        _mostrar(predecir(m, json.load(open(a.json, encoding='utf-8'))))
    else:
        os.makedirs(a.salida, exist_ok=True)
        det, cupos = proyectar_lote(m, _csv_a_df(a.csv))
        det.to_csv(os.path.join(a.salida, 'proyeccion_cohortes.csv'), index=False)
        cupos.to_csv(os.path.join(a.salida, 'cupos_esperados.csv'), index=False)
        print(det.estado.value_counts().to_string()); print(cupos.head(12).to_string(index=False))
        print(f'\nescrito en {a.salida}/: proyeccion_cohortes.csv y cupos_esperados.csv')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, json.JSONDecodeError) as e:
        print(f'ERROR: {type(e).__name__}: {e}', file=sys.stderr)
        sys.exit(2)
