"""Compara configuraciones del Random Forest en la misma ventana móvil usada para elegir el modelo (2022, 2023 y 2024).
2025 no se usa. Uso:  python comparar_hiperparametros.py T04_muestra_SIES_2017_2026.zip   (escribe evidencia/comparacion_hiperparametros.csv)"""
import sys, glob, zipfile, tempfile, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
import construir_modelo as cm
warnings.filterwarnings('ignore')

tmp = tempfile.mkdtemp(); zipfile.ZipFile(sys.argv[1]).extractall(tmp)
CL = {y: cm.clean_year(pd.read_csv(glob.glob(f'{tmp}/*_{y}_PUBL_MRUN_MUESTRA4pct.csv')[0], sep=';', dtype=str, keep_default_na=False), y)
      for y in range(2018, 2026)}
DATA = {t: cm.dataset(CL, t) for t in range(2019, 2025)}

# mismas etapas de preprocesamiento; solo cambia el bosque
CONFIG = [(300, 3), (300, 5), (300, 8), (300, 12), (300, None), (100, 5), (500, 5)]
filas = []
for arboles, prof in CONFIG:
    fila = dict(arboles=arboles, profundidad='sin límite' if prof is None else prof)
    for tv in (2022, 2023, 2024):
        tr = pd.concat([DATA[t] for t in range(2019, tv)], ignore_index=True); va = DATA[tv]
        pipe = cm.build_pipeline('rf')
        pipe.set_params(modelo=RandomForestRegressor(n_estimators=arboles, max_depth=prof, random_state=cm.SEED, n_jobs=-1))
        p = np.clip(pipe.fit(tr[cm.FEATURES], tr.y.values).predict(va[cm.FEATURES]), 0, 1)
        fila[str(tv)] = float(np.mean(np.abs(va.y.values - p)))
    fila['MAE_medio'] = np.mean([fila[k] for k in ('2022', '2023', '2024')])
    filas.append(fila); print(fila)
R = pd.DataFrame(filas)
R.round(4).to_csv('evidencia/comparacion_hiperparametros.csv', index=False); print(R.round(4).to_string(index=False))
