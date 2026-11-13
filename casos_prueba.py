"""Suite de pruebas de la aplicación (20 casos definidos antes de ejecutar). No necesita los datos, solo el modelo y su contrato.
Uso:  python casos_prueba.py   (escribe evidencia/bitacora_pruebas.csv)"""
import copy, os
import numpy as np, pandas as pd
import cupos_app as app

def ejecutar_casos(M):
    ref0 = M.contrato['casos_referencia'][0]['entrada']; rn = ref0
    def ca(**kw): return {**rn, **kw}
    sin = {k: v for k, v in rn.items() if k != 'arancel_anual_clp'}
    dy = rn['dur_semestres'] / 2; ult = ca(anio_ingreso=int(rn['anio_t'] - dy + 1))
    CASOS = [
     ('CP-01', 'Normal', 'flujo completo con una cohorte real', rn, 'ok', None),
     ('CP-02', 'Inválido', 'arancel negativo', ca(arancel_anual_clp=-100000), 'error', 'arancel_anual_clp'),
     ('CP-03', 'Incompleto', 'falta un campo obligatorio (prop_mujer)', {k: v for k, v in rn.items() if k != 'prop_mujer'}, 'error', 'prop_mujer'),
     ('CP-04', 'Inválido', 'texto en campo numérico', ca(n_t='diez'), 'error', 'n_t'),
     ('CP-05', 'Integración', 'misma predicción que el pipeline de referencia', rn, 'consistencia', None),
     ('CP-06', 'Fuera de rango', 'arancel tres veces el máximo de entrenamiento', ca(arancel_anual_clp=M.ref['arancel_pesos']['max'] * 3), 'advertencia', 'arancel_anual_clp'),
     ('CP-07', 'Límite', 'n_t = 0', ca(n_t=0), 'error', 'n_t'),
     ('CP-08', 'Límite', 'n_t = 4, justo bajo el mínimo del contrato', ca(n_t=4), 'error', 'n_t'),
     ('CP-09', 'No finito', 'NaN en ret_prev', ca(ret_prev=float('nan')), 'error', 'ret_prev'),
     ('CP-10', 'No finito', 'infinito en el arancel', ca(arancel_anual_clp=float('inf')), 'error', 'arancel_anual_clp'),
     ('CP-11', 'Tipo', 'booleano en prop_mujer', ca(prop_mujer=True), 'error', 'prop_mujer'),
     ('CP-12', 'Categoría', 'región inexistente', ca(region_sede='Narnia'), 'error', 'region_sede'),
     ('CP-13', 'Rango', 'proporción mayor que 1', ca(ret_prev=1.4), 'error', 'ret_prev'),
     ('CP-14', 'Coherencia', 'ingreso posterior al año observado', ca(anio_ingreso=rn['anio_t'] + 1), 'error', 'anio_ingreso'),
     ('CP-15', 'Coherencia', 'cohorte mayor que el total del programa', ca(n_t=rn['prog_total_t'] + 1), 'error', 'n_t'),
     ('CP-16', 'Dominio', 'cohorte en su último año nominal', ult, 'error', 'anio_ingreso'),
     ('CP-17', 'Coherencia', 'n_prev sin ret_prev', ca(ret_prev=None), 'error', 'n_prev'),
     ('CP-18', 'Unidades', 'arancel informado en UF', ca(arancel_anual_clp=55.0), 'error', 'arancel_anual_clp'),
     ('CP-19', 'Limitación', 'cohorte de CFT: debe avisar el error alto', ca(tipo_inst_1='Centros de Formación Técnica'), 'advertencia', 'CFT'),
     ('CP-20', 'Opcionales', 'sin historial ni edad: predice y avisa', ca(n_prev=None, ret_prev=None, edad_media=None), 'advertencia', 'n_prev'),
    ]
    bit = []; ll0 = M.llamadas
    for cid, tipo, prop, ent, regla, campo in CASOS:
        l_antes = M.llamadas
        try: out = app.predecir(M, copy.deepcopy(ent))
        except Exception as e: out = dict(estado='EXCEPCION', errores=[repr(e)], advertencias=[])
        llamo = M.llamadas - l_antes
        if regla == 'error': cumple = out['estado'] == 'RECHAZADA' and any(m_.startswith(campo) for m_ in out['errores']) and llamo == 0
        elif regla == 'advertencia': cumple = out['estado'] == 'OK' and any(campo in m_ for m_ in out['advertencias'])
        elif regla == 'consistencia': cumple = out['estado'] == 'OK' and bool(np.isclose(out['prediccion_sin_acotar'], float(M._pipe.predict(app.a_features(M, app.validar(M, ent)[2]))[0]), atol=1e-10, rtol=0))
        else: cumple = out['estado'] == 'OK' and 0 <= out['prediccion'] <= 1
        esp = {'ok': 'respuesta OK con predicción en [0, 1]', 'error': f'rechazo que nombre {campo}; el modelo no se llama', 'consistencia': 'predicción igual al pipeline (atol 1e-10)',
               'advertencia': f'respuesta OK con advertencia sobre {campo}'}[regla]
        bit.append(dict(caso=cid, tipo=tipo, proposito=prop, esperado=esp, estado_observado=out['estado'], llamadas_modelo=llamo,
                        mensajes=' | '.join(out['errores'] + out['advertencias'])[:300], resultado='Cumple' if cumple else 'No cumple'))
    return pd.DataFrame(bit), CASOS



if __name__ == '__main__':
    M = app.Modelo(); BIT, _ = ejecutar_casos(M)
    os.makedirs('evidencia', exist_ok=True); BIT.to_csv('evidencia/bitacora_pruebas.csv', index=False)
    print(BIT[['caso', 'tipo', 'estado_observado', 'llamadas_modelo', 'resultado']].to_string(index=False))
    print(f"{(BIT.resultado == 'Cumple').sum()} de {len(BIT)} casos cumplen")
