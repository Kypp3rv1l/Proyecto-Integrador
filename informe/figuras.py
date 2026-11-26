import sys, json, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
EV = sys.argv[1] + '/evidencia/'; OUT = sys.argv[2]
TINTA, VERDE, AZUL, GRIS, ARENA, ROJO = '#1B2A41', '#2E8B6F', '#3D6FB6', '#9AA3AF', '#D9A441', '#B5523B'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#555',
                     'axes.titleweight': 'bold', 'axes.titlesize': 13, 'axes.labelsize': 11, 'xtick.labelsize': 10, 'ytick.labelsize': 10})
def guardar(fig, n): fig.tight_layout(); fig.savefig(f'{OUT}/{n}.png', dpi=200, bbox_inches='tight'); plt.close(fig)

# validación temporal
vt = pd.read_csv(EV + 'validacion_temporal.csv')
fig, ax = plt.subplots(figsize=(7.5, 4))
for col, lab, c, ls in [('MAE', 'Modelo (Random Forest)', VERDE, '-'), ('MAE_base_ret_prev', 'Base: retención del año anterior', AZUL, '--'), ('MAE_base_media', 'Base: media', GRIS, ':')]:
    ax.plot(vt.anio_prueba, vt[col], ls, marker='o', lw=2.4, color=c, label=lab)
for x, y in zip(vt.anio_prueba, vt.MAE): ax.annotate(f'{y:.3f}'.replace('.', ','), (x, y), textcoords='offset points', xytext=(0, -16), ha='center', fontsize=9, color=VERDE)
ax.set(xlabel='Año de prueba (se entrena con los años anteriores)', ylabel='Error absoluto medio', title='El modelo gana en los cuatro cortes temporales')
ax.set_xticks(vt.anio_prueba); ax.legend(frameon=False, fontsize=9); ax.set_ylim(0.05, 0.14)
guardar(fig, 'fig_validacion_temporal')

# comparación de modelos
cm = pd.read_csv(EV + 'comparacion_modelos.csv', index_col=0).sort_values('MAE_medio')
fig, ax = plt.subplots(figsize=(7.5, 3.4))
col = [VERDE if 'Random' in i else GRIS for i in cm.index]
ax.barh(cm.index[::-1], cm.MAE_medio[::-1], color=col[::-1])
for i, v in enumerate(cm.MAE_medio[::-1]): ax.text(v + .001, i, f'{v:.3f}'.replace('.', ','), va='center', fontsize=10)
ax.set(xlabel='MAE medio en 2022, 2023 y 2024', title='Elección del modelo: menor error en validación'); ax.set_xlim(0, .14)
guardar(fig, 'fig_comparacion_modelos')

# alcance
al = pd.read_csv(EV + 'alcance_por_tipo.csv'); piv = al.pivot(index='anio_t', columns='tipo_inst_1', values='pct_codigo_desaparece')
fig, ax = plt.subplots(figsize=(7.5, 4)); x = np.arange(len(piv)); w = .26
for k, (tipo, c, lab) in enumerate([('Universidades', VERDE, 'Universidades'), ('Institutos Profesionales', AZUL, 'IP'), ('Centros de Formación Técnica', ROJO, 'CFT')]):
    ax.bar(x + (k - 1) * w, piv[tipo], w, color=c, label=lab)
    for xi, v in zip(x + (k - 1) * w, piv[tipo]): ax.text(xi, v + .4, f'{v:.1f}'.replace('.', ','), ha='center', fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels(piv.index); ax.set(ylabel='% de cohortes', xlabel='Año observado t', title='Cohortes cuyo código de programa desaparece en t+1')
ax.legend(frameon=False); guardar(fig, 'fig_alcance')

# predicción vs observado
pr = pd.read_csv(EV + 'predicciones_prueba.csv')
fig, ax = plt.subplots(figsize=(5.2, 5))
ax.scatter(pr.observado, pr.prediccion, s=10 + 2 * np.sqrt(pr.n_t), alpha=.45, color=VERDE, edgecolor='none')
ax.plot([0, 1], [0, 1], '--', color=GRIS, lw=1); ax.set(xlim=(0, 1.02), ylim=(0, 1.02), xlabel='Continuidad observada en 2026', ylabel='Continuidad estimada', title='Prueba 2025: 331 cohortes')
guardar(fig, 'fig_pred_obs')

# error por tamaño
tm = pd.read_csv(EV + 'error_por_tamano_cohorte.csv').set_index('tramo_n_t').loc[['5–9', '10–19', '20–49', '50 o más']]
fig, ax = plt.subplots(figsize=(6.5, 3.6)); ax.bar(tm.index, tm.MAE, color=[ARENA, ARENA, VERDE, VERDE])
for i, (v, n) in enumerate(zip(tm.MAE, tm.cohortes)): ax.text(i, v + .003, f'{v:.3f}'.replace('.', ',') + f'\n{n} cohortes', ha='center', fontsize=9)
ax.set(ylabel='MAE', xlabel='Estudiantes en la cohorte', title='El error crece en cohortes pequeñas'); ax.set_ylim(0, .16)
guardar(fig, 'fig_tamano')

# cupos
cu = pd.read_csv(EV + 'cupos_backtest_todas.csv', index_col=0)
fig, ax = plt.subplots(figsize=(7.5, 3.4)); orden = ['Modelo', 'Base: retención del año previo', 'Base: media de entrenamiento', 'Base: todos continúan']
v = cu.loc[orden].MAE_est_por_cohorte; ax.barh(orden[::-1], v[::-1], color=[GRIS, GRIS, AZUL, VERDE])
for i, x in enumerate(v[::-1]): ax.text(x + .08, i, f'{x:.2f}'.replace('.', ','), va='center', fontsize=10)
ax.set(xlabel='Error medio en estudiantes por cohorte (2025 → 2026)', title='Cupos: estudiantes que continúan'); ax.set_xlim(0, 8)
guardar(fig, 'fig_cupos')

# arquitectura
fig, ax = plt.subplots(figsize=(13, 4.4)); ax.set_xlim(0, 13); ax.set_ylim(0, 4.4); ax.axis('off')
def caja(x, y, w, h, t, c, b=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.04,rounding_size=0.14', fc=c, ec=TINTA, lw=1.3))
    ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=11.5, fontweight='bold' if b else 'normal', color=TINTA, linespacing=1.15)
def fl(x1, y1, x2, y2, ls='-'): ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=14, lw=1.5, color=TINTA, linestyle=ls))
caja(.1, 2.5, 2.0, 1.6, 'ENTRADA\nweb, JSON o CSV\n19 campos', '#F1E6CF', True)
caja(2.6, 2.5, 2.2, 1.6, 'VALIDACIÓN\ntipos y rangos\nsolo universidades\nreglas entre campos', '#F6DDB1', True)
caja(5.3, 2.5, 1.9, 1.6, 'DERIVACIÓN\naño de estudio\naños restantes', '#DCE7F5', True)
caja(7.7, 2.5, 2.3, 1.6, 'MODELO\nRandom Forest\nsolo predict', '#D3EDE2', True)
caja(10.5, 2.5, 2.4, 1.6, 'LOTE → CUPOS\ncohorte única\nexcluidas no suman', '#D3EDE2', True)
caja(2.6, .3, 2.2, 1.3, 'RECHAZO\nmensaje por campo\nmodelo no se llama', '#F3D3CB')
caja(7.7, .3, 2.3, 1.3, 'ARTEFACTOS\n.joblib + contrato\nhuella SHA-256', '#E6E8EB')
caja(10.5, .3, 2.4, 1.3, 'EVIDENCIA\nmétricas, pruebas\ncortes temporales', '#E6E8EB')
fl(2.1, 3.3, 2.6, 3.3); fl(4.8, 3.3, 5.3, 3.3); fl(7.2, 3.3, 7.7, 3.3); fl(10.0, 3.3, 10.5, 3.3); fl(3.7, 2.5, 3.7, 1.6); fl(8.85, 1.6, 8.85, 2.5)
fl(10.0, .95, 10.5, .95, '--')
guardar(fig, 'fig_arquitectura')
print('ok')
