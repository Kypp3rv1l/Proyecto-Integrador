"""Compara alternativas de modelo en validación de ventana móvil (solo universidades).
Para cada año de prueba (2022, 2023, 2024) se entrena con los años anteriores; 2025 queda reservado para la prueba final.
Criterio fijado antes de comparar: gana el menor MAE medio; si la diferencia es menor a 0,002 se elige el más simple.
Uso:  python comparar_modelos.py T04_muestra_SIES_2017_2026.zip   (escribe evidencia/comparacion_modelos.csv)"""
import sys, glob, zipfile, tempfile, warnings
import numpy as np, pandas as pd
import construir_modelo as cm
warnings.filterwarnings('ignore')

tmp = tempfile.mkdtemp(); zipfile.ZipFile(sys.argv[1]).extractall(tmp)
CL = {y: cm.clean_year(pd.read_csv(glob.glob(f'{tmp}/*_{y}_PUBL_MRUN_MUESTRA4pct.csv')[0], sep=';', dtype=str, keep_default_na=False), y)
      for y in range(2018, 2026)}
DATA = {t: cm.dataset(CL, t) for t in range(2019, 2025)}


filas = []
for tv in (2022, 2023, 2024):
    tr = pd.concat([DATA[t] for t in range(2019, tv)], ignore_index=True); va = DATA[tv]; y = va.y.values
    pred = {'Constante (mediana)': np.full(len(y), tr.y.median()),
            'Persistencia (retención previa)': va.ret_prev.fillna(tr.y.median()).values,
            'Ridge (alpha = 1)': cm.build_pipeline('ridge').fit(tr[cm.FEATURES], tr.y.values).predict(va[cm.FEATURES]),
            'Random Forest (300 árboles, prof. 5)': cm.build_pipeline('rf').fit(tr[cm.FEATURES], tr.y.values).predict(va[cm.FEATURES])}
    for nom, p in pred.items():
        filas.append(dict(modelo=nom, anio_prueba=tv, MAE=float(np.mean(np.abs(y - np.clip(p, 0, 1))))))
R = pd.DataFrame(filas).pivot(index='modelo', columns='anio_prueba', values='MAE')
R['MAE_medio'] = R.mean(axis=1); R = R.sort_values('MAE_medio')
R.round(4).to_csv('evidencia/comparacion_modelos.csv'); print(R.round(4))
