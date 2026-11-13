"""Genera la evidencia de validación del prototipo a partir de los datos reales (todas las cifras salen de esta ejecución).
Uso:  python ejecutar_validacion.py T04_muestra_SIES_2017_2026.zip
Escribe en evidencia/ y datos_ejemplo/cohortes_2025.csv."""
import sys, os, glob, json, zipfile, tempfile, hashlib, copy, platform, warnings
import numpy as np, pandas as pd, sklearn
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
import construir_modelo as cm
import cupos_app as app
from sklearn.metrics import r2_score

ZIP = sys.argv[1]; EV = 'evidencia'; os.makedirs(EV, exist_ok=True); os.makedirs('datos_ejemplo', exist_ok=True)
AZUL, CELESTE = '#20377D', '#80BBDF'
plt.rcParams.update({'axes.spines.top': False, 'axes.spines.right': False, 'axes.titleweight': 'bold'})
tmp = tempfile.mkdtemp(); zipfile.ZipFile(ZIP).extractall(tmp)
CL = {y: cm.clean_year(pd.read_csv(glob.glob(f'{tmp}/*_{y}_PUBL_MRUN_MUESTRA4pct.csv')[0], sep=';', dtype=str, keep_default_na=False), y)
      for y in range(2018, 2027)}
DATA = {t: cm.dataset(CL, t) for t in cm.T_OBS}
DEV = pd.concat([DATA[t] for t in cm.T_OBS if t < cm.TEST_T], ignore_index=True); TE = DATA[cm.TEST_T].copy()
M = app.Modelo()
RES = {'entorno': dict(python=platform.python_version(), sklearn=sklearn.__version__, pandas=pd.__version__, numpy=np.__version__),
       'datos': dict(sha256_zip=cm.sha256(ZIP), cohortes_entrenamiento=int(len(DEV)), cohortes_prueba=int(len(TE)),
                     programas_prueba=int(TE.codigo_unico.nunique()))}

# 1) el modelo guardado = el que se obtiene al reentrenar; no se reajusta al predecir
re = cm.build_pipeline().fit(DEV[cm.FEATURES], DEV.y.values)
X, y = TE[cm.FEATURES], TE.y.values
p_guardado = np.clip(M.predict(X), 0, 1); p_re = np.clip(re.predict(X), 0, 1)
RES['modelo_guardado_igual_reentrenado'] = bool(np.allclose(p_guardado, p_re, atol=1e-8, rtol=0))

# 2) métricas de la continuidad (proporción) y líneas base
def met(yr, yp, w):
    return dict(MAE=float(np.mean(np.abs(yr - yp))), MAE_ponderado_n=float(np.average(np.abs(yr - yp), weights=w)),
                RMSE=float(np.sqrt(np.mean((yr - yp) ** 2))), R2=float(r2_score(yr, yp)), sesgo=float(np.mean(yp - yr)))
b_media = np.full(len(y), DEV.y.mean()); b_ret = TE.ret_prev.fillna(DEV.y.mean()).to_numpy()
MET = pd.DataFrame({'Ridge (modelo)': met(y, p_guardado, TE.n_t), 'Base: media de entrenamiento': met(y, b_media, TE.n_t),
                    'Base: retención del año previo': met(y, b_ret, TE.n_t)}).T
MET.round(4).to_csv(f'{EV}/metricas_continuidad.csv'); print(MET.round(4))

# 3) del porcentaje a los cupos: estudiantes continuantes esperados vs observados por cohorte y por programa
TE['pred'] = p_guardado; TE['obs_n'] = np.rint(TE.n_t * TE.y).astype(int)
TE['codigo_vigente'] = TE.codigo_unico.isin(set(CL[2026].codigo_unico))
def cupos_tab(d):
    est = {'Modelo': d.n_t * d.pred, 'Base: todos continúan': d.n_t.astype(float), 'Base: media de entrenamiento': d.n_t * DEV.y.mean(),
           'Base: retención del año previo': d.n_t * d.ret_prev.fillna(DEV.y.mean())}
    out = {}
    for k, e in est.items():
        e = e.to_numpy(); o = d.obs_n.to_numpy(); pr = pd.DataFrame({'p': d.codigo_unico.to_numpy(), 'e': e, 'o': o}).groupby('p')[['e', 'o']].sum()
        out[k] = dict(MAE_est_por_cohorte=float(np.mean(np.abs(e - o))), WAPE_cohorte=float(np.abs(e - o).sum() / o.sum()),
                      MAE_est_por_programa=float(np.mean(np.abs(pr.e - pr.o))), WAPE_programa=float(np.abs(pr.e - pr.o).sum() / pr.o.sum()),
                      sesgo_total_pct=float((e.sum() - o.sum()) / o.sum() * 100))
    return pd.DataFrame(out).T
CUP = cupos_tab(TE); CUP_V = cupos_tab(TE[TE.codigo_vigente])
CUP.round(4).to_csv(f'{EV}/cupos_backtest_todas.csv'); CUP_V.round(4).to_csv(f'{EV}/cupos_backtest_codigo_vigente.csv')
print('\nCUPOS (todas las cohortes)\n', CUP.round(3), '\nCUPOS (solo programas cuyo código sigue en 2026)\n', CUP_V.round(3))
RES['cupos'] = dict(todas=CUP.round(4).to_dict('index'), codigo_vigente=CUP_V.round(4).to_dict('index'),
                    obs_total=int(TE.obs_n.sum()), cohortes_codigo_desaparece=int((~TE.codigo_vigente).sum()),
                    programas_codigo_desaparece=int(TE[~TE.codigo_vigente].codigo_unico.nunique()),
                    estudiantes_en_programas_que_desaparecen=int(TE[~TE.codigo_vigente].n_t.sum()))

# 4) dónde se concentra el error
det = TE[['codigo_unico', 'anio', 'n_t', 'tipo_inst_1', 'area_conocimiento', 'codigo_vigente']].copy()
det['observado'] = y; det['prediccion'] = p_guardado; det['error'] = det.prediccion - det.observado; det['error_abs'] = det.error.abs()
det.to_csv(f'{EV}/predicciones_prueba.csv', index=False)
def grupo(col):
    g = det.groupby(col, observed=True)
    return pd.DataFrame({'cohortes': g.size(), 'observado_medio': g.observado.mean(), 'prediccion_media': g.prediccion.mean(),
                         'MAE': g.error_abs.mean(), 'sesgo': g.error.mean()}).sort_values('cohortes', ascending=False)
det['tramo_n_t'] = pd.cut(det.n_t, [0, 9, 19, 49, np.inf], labels=['5–9', '10–19', '20–49', '50 o más'])
POR_TIPO, POR_AREA, POR_TAM = grupo('tipo_inst_1'), grupo('area_conocimiento'), grupo('tramo_n_t')
POR_VIG = grupo('codigo_vigente'); POR_TIPO_V = det[det.codigo_vigente].groupby('tipo_inst_1').agg(cohortes=('error', 'size'), MAE=('error_abs', 'mean'), sesgo=('error', 'mean'))
for nom, t in [('por_tipo_institucion', POR_TIPO), ('por_area', POR_AREA), ('por_tamano_cohorte', POR_TAM), ('por_codigo_vigente', POR_VIG), ('por_tipo_codigo_vigente', POR_TIPO_V)]:
    t.round(4).to_csv(f'{EV}/error_{nom}.csv')
print('\n', POR_TIPO.round(3), '\n', POR_TIPO_V.round(3), '\n', POR_TAM.round(3))
RES['error_por_tipo'] = POR_TIPO.round(4).to_dict('index'); RES['error_por_tipo_codigo_vigente'] = POR_TIPO_V.round(4).to_dict('index')
RES['error_por_tamano'] = POR_TAM.round(4).to_dict('index'); RES['metricas_continuidad'] = MET.round(4).to_dict('index')
RES['mae_continuidad_codigo_vigente'] = float(det[det.codigo_vigente].error_abs.mean())

# 5) figuras
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
ax[0].scatter(det.observado, det.prediccion, s=8 + 2 * np.sqrt(det.n_t), alpha=.4, color=AZUL, edgecolor='none'); ax[0].plot([0, 1], [0, 1], '--', color='gray', lw=1)
ax[0].set(xlabel='Continuidad observada', ylabel='Continuidad predicha', title='Predicción vs. observado · prueba 2025')
ax[1].hist(det.error, bins=30, color=CELESTE, edgecolor='white'); ax[1].axvline(0, ls='--', color='gray', lw=1); ax[1].set(xlabel='Error (predicho − observado)', ylabel='Cohortes', title='Residuos')
pp = TE.assign(e=TE.n_t * TE.pred).groupby('codigo_unico')[['e', 'obs_n']].sum()
ax[2].scatter(pp.obs_n, pp.e, s=14, alpha=.5, color=AZUL, edgecolor='none'); mx = max(pp.max()) * 1.05; ax[2].plot([0, mx], [0, mx], '--', color='gray', lw=1)
ax[2].set(xlabel='Continuantes observados (programa)', ylabel='Continuantes esperados', title='Cupos por programa · prueba 2025', xscale='symlog', yscale='symlog')
fig.tight_layout(); fig.savefig(f'{EV}/fig_desempeno.png', dpi=150, bbox_inches='tight'); plt.close(fig)
fig, ax = plt.subplots(figsize=(7.5, 4))
x = np.arange(len(POR_TIPO)); w = .38
ax.bar(x - w / 2, POR_TIPO.MAE, w, color=AZUL, label='todas las cohortes')
ax.bar(x + w / 2, POR_TIPO_V.reindex(POR_TIPO.index).MAE, w, color=CELESTE, label='programa con código vigente en 2026')
ax.set_xticks(x); ax.set_xticklabels([s.replace('Centros de Formación Técnica', 'CFT').replace('Institutos Profesionales', 'IP') for s in POR_TIPO.index]); ax.set(ylabel='MAE', title='Error por tipo de institución · prueba 2025'); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f'{EV}/fig_error_tipo.png', dpi=150, bbox_inches='tight'); plt.close(fig)

# 6) robustez ante pequeñas perturbaciones (una variable a la vez)
rob = []
for col, modo, d in [('ret_prev', 'abs', -.05), ('ret_prev', 'abs', .05), ('arancel_pesos', 'rel', -.05), ('arancel_pesos', 'rel', .05), ('edad_media', 'abs', -1.), ('edad_media', 'abs', 1.)]:
    ok = X[col].notna(); base = np.clip(M.predict(X[ok]), 0, 1); v = X[ok].copy()
    v[col] = v[col] + d if modo == 'abs' else v[col] * (1 + d)
    if col == 'ret_prev': v[col] = v[col].clip(0, 1)
    ch = np.clip(M.predict(v), 0, 1) - base
    rob.append(dict(variable=col, perturbacion=f'{d:+g}' + (' relativo' if modo == 'rel' else ''), cohortes=int(ok.sum()),
                    cambio_abs_medio=float(np.mean(np.abs(ch))), cambio_abs_max=float(np.max(np.abs(ch))), sobre_2pp=float(np.mean(np.abs(ch) > .02))))
ROB = pd.DataFrame(rob); ROB.round(4).to_csv(f'{EV}/robustez.csv', index=False); print('\n', ROB.round(4)); RES['robustez'] = ROB.round(4).to_dict('records')

# 7) integración: la aplicación reproduce el pipeline en todas las cohortes que el contrato puede representar
def a_entrada(r):
    n = lambda v: None if pd.isna(v) else v
    d = dict(anio_t=int(r.t), anio_ingreso=int(r.anio), n_t=int(r.n_t), n_prev=None if pd.isna(r.n_prev) else int(r.n_prev), ret_prev=n(r.ret_prev),
             prog_total_t=int(r.prog_total_t), prop_mujer=float(r.prop_mujer), edad_media=n(r.edad_media), dur_semestres=int(r.dur_sem),
             arancel_anual_clp=n(r.arancel_pesos)); d.update({c: str(r[c]) for c in cm.CAT}); return d
dentro = TE[TE.arancel_uf == 0]; res_int = []
for (_, r), ref in zip(dentro.iterrows(), M._pipe.predict(dentro[cm.FEATURES])):
    out = app.predecir(M, a_entrada(r))
    res_int.append(out['estado'] == 'OK' and bool(np.isclose(out['prediccion_sin_acotar'], ref, atol=1e-10, rtol=0)))
RES['integracion'] = dict(cohortes_en_contrato=int(len(dentro)), coinciden=int(sum(res_int)), fuera_por_arancel_en_uf=int(len(TE) - len(dentro)))
print('\nintegración:', RES['integracion'])
# cohortes de ejemplo para el modo lote (datos agregados por cohorte, sin personas)
ej = pd.DataFrame([dict(programa=r.codigo_unico, **a_entrada(r)) for _, r in dentro.iterrows()])
ej.round({'ret_prev': 4, 'prop_mujer': 4, 'edad_media': 2}).to_csv('datos_ejemplo/cohortes_2025.csv', index=False)

# 8) bitácora de casos de prueba (definidos en casos_prueba.py antes de ejecutar)
from casos_prueba import ejecutar_casos
BIT, CASOS = ejecutar_casos(M); BIT.to_csv(f'{EV}/bitacora_pruebas.csv', index=False); print('\n', BIT[['caso', 'tipo', 'estado_observado', 'llamadas_modelo', 'resultado']].to_string(index=False))
RES['bitacora'] = dict(casos=len(BIT), cumplen=int((BIT.resultado == 'Cumple').sum()), llamadas_del_modelo_en_casos_de_error=int(BIT[BIT.caso.isin([c[0] for c in CASOS if c[4] == 'error'])].llamadas_modelo.sum()))

# 9) lote de ejemplo end-to-end
det_l, cup_l = app.proyectar_lote(M, app._csv_a_df('datos_ejemplo/cohortes_2025.csv'))
os.makedirs('resultados_ejemplo', exist_ok=True); det_l.to_csv('resultados_ejemplo/proyeccion_cohortes.csv', index=False); cup_l.to_csv('resultados_ejemplo/cupos_esperados.csv', index=False)
RES['lote_ejemplo'] = dict(cohortes=int(len(det_l)), ok=int((det_l.estado == 'OK').sum()), programas=int(cup_l.programa.nunique()), con_advertencia=int((det_l.mensajes != '').sum()))

# 10) el pipeline no cambió tras todas las predicciones
def huella(p):
    pr = p.named_steps['prep']; r = p.named_steps['modelo']; c = pr.named_transformers_['cnt']; t = pr.named_transformers_['rate']
    partes = [r.coef_, np.atleast_1d(r.intercept_), c.named_steps['imp'].statistics_, c.named_steps['sc'].mean_, c.named_steps['sc'].scale_,
              t.named_steps['imp'].statistics_, t.named_steps['sc'].mean_, t.named_steps['sc'].scale_]
    return hashlib.sha256(b''.join(np.ascontiguousarray(a, dtype=float).tobytes() for a in partes)).hexdigest()
import joblib
RES['sin_reajuste'] = dict(huella_guardada=huella(joblib.load('modelo_continuidad.joblib')), huella_tras_predicciones=huella(M._pipe), llamadas_totales_predict=M.llamadas)
RES['sin_reajuste']['igual'] = RES['sin_reajuste']['huella_guardada'] == RES['sin_reajuste']['huella_tras_predicciones']
json.dump(RES, open(f'{EV}/resumen_evidencia.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('\nOK. Evidencia en', EV)
