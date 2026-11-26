"""Construye el modelo de continuidad y su contrato (paso previo; la aplicación solo carga el resultado).
Entrena el modelo elegido en la comparación de comparar_modelos.py (Random Forest, 300 árboles de profundidad 5) ajustado con el desarrollo (t = 2019-2024) y lo guarda
junto a su contrato de entrada. El alcance es solo universidades: en CFT e IP muchos códigos de programa
desaparecen de un año a otro y la base los cuenta como «no continúa», lo que mide otra cosa. Uso:  python construir_modelo.py T04_muestra_SIES_2017_2026.zip
Si el .joblib no carga por diferencia de versiones, este script lo regenera."""
import sys, os, json, glob, zipfile, hashlib, platform, tempfile, warnings
import numpy as np, pandas as pd, sklearn, joblib
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
warnings.filterwarnings('ignore')
ALCANCE={'tipo_inst_1':['Universidades']}
SEED=42; YEARS=list(range(2017,2027)); T_OBS=list(range(2019,2026)); TEST_T=2025; MIN_N=5; UMBRAL_UF=10_000
CAT=['tipo_inst_1','area_conocimiento','region_sede','jornada','modalidad','nivel_carrera_1','acreditada_carr','acreditada_inst','tipo_plan_carr']
NUM_CNT=['n_t','n_prev','prog_total_t','arancel_pesos']; NUM_RATE=['ret_prev','prop_mujer','edad_media','year_of_study','dur_years','remaining_years']; BIN=['arancel_uf']
FEATURES=NUM_CNT+NUM_RATE+BIN+CAT
def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def clean_year(df,y):
    d=df[(df.nivel_global=='Pregrado')&(df.mrun!='')].drop_duplicates(['cat_periodo','codigo_unico','mrun']).copy()
    d['anio']=pd.to_numeric(d.anio_ing_carr_act,errors='coerce'); d['dur_sem']=pd.to_numeric(d.dur_estudio_carr,errors='coerce').where(lambda s:s>0)
    nac=d.fec_nac_alu.where(d.fec_nac_alu!='190001'); ed=y-pd.to_numeric(nac.str[:4],errors='coerce'); d['edad']=ed.where(ed.between(14,90))
    d['mujer']=(d.gen_alu=='2').astype(float); ar=pd.to_numeric(d.valor_arancel,errors='coerce')
    un=np.where(d.formato_valores!='',d.formato_valores,np.where((ar>0)&(ar<UMBRAL_UF),'Monto en UF','Monto en Pesos'))
    d['arancel_uf']=(un=='Monto en UF').astype(float); d['arancel_pesos']=ar.where((un=='Monto en Pesos')&(ar>0)); return d.reset_index(drop=True)
def cohort_table(c):
    t=c.groupby(['codigo_unico','anio']).agg(n_t=('mrun','size'),prop_mujer=('mujer','mean'),edad_media=('edad','mean')).reset_index()
    p=c.groupby('codigo_unico').agg(prog_total_t=('mrun','size'),dur_sem=('dur_sem','first'),arancel_pesos=('arancel_pesos','first'),arancel_uf=('arancel_uf','max'),**{k:(k,'first') for k in CAT}).reset_index()
    return t.merge(p,on='codigo_unico',how='left')
def transition(cl,t):
    a,b=cl[t],cl[t+1]; nxt=set(zip(b.mrun,b.codigo_unico)); ok=np.fromiter(((m,c) in nxt for m,c in zip(a.mrun,a.codigo_unico)),bool,len(a))
    return a.assign(ok=ok).groupby(['codigo_unico','anio']).ok.mean().rename('y').reset_index()
def features(cl,t):
    X=cohort_table(cl[t]); pv=cohort_table(cl[t-1])[['codigo_unico','anio','n_t']].rename(columns={'n_t':'n_prev'}); rp=transition(cl,t-1).rename(columns={'y':'ret_prev'})
    X=X.merge(pv,on=['codigo_unico','anio'],how='left').merge(rp,on=['codigo_unico','anio'],how='left'); X['t']=t
    X['year_of_study']=t-X.anio+1; X['dur_years']=X.dur_sem/2; X['remaining_years']=X.dur_years-X.year_of_study; return X
def dataset(cl,t,solo_alcance=True):
    D=features(cl,t).merge(transition(cl,t),on=['codigo_unico','anio'],how='left')
    if solo_alcance: D=D[D.tipo_inst_1.isin(ALCANCE['tipo_inst_1'])]
    return D[D.dur_years.notna()&(D.year_of_study<D.dur_years)&(D.n_t>=MIN_N)].reset_index(drop=True)
def build_pipeline(modelo='rf'):
    cnt=Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('log',FunctionTransformer(np.log1p,feature_names_out='one-to-one',validate=False)),('sc',StandardScaler())])
    rate=Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler())])
    prep=ColumnTransformer([('cnt',cnt,NUM_CNT),('rate',rate,NUM_RATE),('bin','passthrough',BIN),('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False,min_frequency=5),CAT)])
    est=RandomForestRegressor(n_estimators=300,max_depth=5,random_state=SEED,n_jobs=1) if modelo=='rf' else Ridge(alpha=1.0,random_state=SEED)
    return Pipeline([('prep',prep),('modelo',est)])
if __name__=='__main__':
    zpath=sys.argv[1]; out=sys.argv[2] if len(sys.argv)>2 else '.'
    tmp=tempfile.mkdtemp(); zipfile.ZipFile(zpath).extractall(tmp)
    RAW={y:pd.read_csv(glob.glob(f'{tmp}/*_{y}_PUBL_MRUN_MUESTRA4pct.csv')[0],sep=';',dtype=str,keep_default_na=False) for y in YEARS}
    CL={y:clean_year(RAW[y],y) for y in YEARS if y>=2018}; DATA={t:dataset(CL,t) for t in T_OBS}
    DEV=pd.concat([DATA[t] for t in T_OBS if t<TEST_T],ignore_index=True); TE=DATA[TEST_T]
    pipe=build_pipeline().fit(DEV[FEATURES],DEV.y.values)
    pt=pipe.predict(TE[FEATURES]); mae=float(np.mean(np.abs(TE.y.values-np.clip(pt,0,1)))); mae_pond=float(np.average(np.abs(TE.y.values-np.clip(pt,0,1)),weights=TE.n_t.values))
    # validación con varios cortes temporales: para cada año t se entrena con 2019..t-1 y se evalúa en t
    cortes=[]
    for tv in (2022,2023,2024,2025):
        tr=pd.concat([DATA[t] for t in T_OBS if t<tv],ignore_index=True); va=DATA[tv]
        pv=np.clip(build_pipeline().fit(tr[FEATURES],tr.y.values).predict(va[FEATURES]),0,1)
        cortes.append(dict(anio_prueba=tv,anios_entrenamiento=f'2019-{tv-1}',filas_entrenamiento=int(len(tr)),filas_prueba=int(len(va)),
                           MAE=float(np.mean(np.abs(va.y.values-pv))),MAE_base_media=float(np.mean(np.abs(va.y.values-tr.y.mean()))),
                           MAE_base_ret_prev=float(np.mean(np.abs(va.y.values-va.ret_prev.fillna(tr.y.mean()).values))),sesgo=float(np.mean(pv-va.y.values))))
    joblib.dump(pipe,f'{out}/modelo_continuidad.joblib')
    ohe=pipe.named_steps['prep'].named_transformers_['cat']; cats={c:[str(v) for v in k] for c,k in zip(CAT,ohe.categories_)}
    q=lambda s:{'p01':float(s.quantile(.01)),'p99':float(s.quantile(.99)),'min':float(s.min()),'max':float(s.max())}
    refs={c:q(DEV[c].dropna()) for c in ['n_t','n_prev','prog_total_t','arancel_pesos','edad_media']}
    # casos de referencia reales (ya conocidos) para comprobar que el artefacto carga y predice igual en cualquier entorno
    TEu=TE[(TE.arancel_uf==0)&TE.arancel_pesos.notna()&TE.n_prev.notna()&TE.ret_prev.notna()&TE.edad_media.notna()].sample(6,random_state=SEED)
    def a_entrada(r):
        d=dict(anio_t=int(r.t),anio_ingreso=int(r.anio),n_t=int(r.n_t),n_prev=int(r.n_prev),ret_prev=round(float(r.ret_prev),4),prog_total_t=int(r.prog_total_t),prop_mujer=round(float(r.prop_mujer),4),
               edad_media=round(float(r.edad_media),2),dur_semestres=int(r.dur_sem),arancel_anual_clp=float(r.arancel_pesos))
        d.update({c:str(r[c]) for c in CAT}); return d
    gold=[dict(entrada=a_entrada(r),y_observado_t_mas_1=round(float(r.y),4),prediccion_esperada=float(pipe.predict(pd.DataFrame([r[FEATURES]]))[0])) for _,r in TEu.iterrows()]
    meta=dict(descripcion='Pipeline scikit-learn (ColumnTransformer + Random Forest de 300 arboles, profundidad 5) elegido por menor MAE en la validacion 2022-2024; ajustado con cohortes universitarias de desarrollo t=2019-2024 de la muestra SIES 4%; no se reajusta al predecir',
        objetivo='proporcion de la cohorte (programa x anio de ingreso) matriculada en t que sigue en el MISMO programa en t+1',
        filas_entrenamiento=int(len(DEV)),min_n_cohorte=MIN_N,features=FEATURES,categorias_permitidas=cats,referencias_numericas=refs,
        prueba_2025=dict(MAE=mae,MAE_ponderado_n=mae_pond,filas=int(len(TE))),
        versiones=dict(python=platform.python_version(),sklearn=sklearn.__version__,pandas=pd.__version__,numpy=np.__version__,joblib=joblib.__version__),
        alcance=ALCANCE,validacion_temporal=cortes,sha256_muestra_entrenamiento=sha256(zpath),sha256_modelo=sha256(f'{out}/modelo_continuidad.joblib'),semilla=SEED,casos_referencia=gold)
    json.dump(meta,open(f'{out}/contrato_modelo.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print('modelo guardado | filas entrenamiento',len(DEV),'| MAE prueba 2025 %.4f (ponderado %.4f)'%(mae,mae_pond),'| versiones',meta['versiones'])
