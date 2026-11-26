"""Suite de pruebas de la aplicación (25 casos definidos antes de ejecutar: 20 de una cohorte y 5 del modo lote). No necesita los datos, solo el modelo y su contrato.
Uso:  python casos_prueba.py   (escribe evidencia/bitacora_pruebas.csv)"""
import copy, os
import numpy as np, pandas as pd
import cupos_app as app

def ejecutar_casos(M):
    ref0 = next(c['entrada'] for c in M.contrato['casos_referencia'] if c['entrada']['tipo_inst_1'] in M.alcance['tipo_inst_1']); rn = ref0
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
     ('CP-19', 'Alcance', 'cohorte de CFT: fuera del alcance (solo universidades)', ca(tipo_inst_1='Centros de Formación Técnica'), 'error', 'tipo_inst_1'),
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
    return pd.DataFrame(bit + casos_lote(M, rn)), CASOS

def casos_lote(M, rn):
    """Casos del modo lote: los totales no pueden incluir filas duplicadas ni rechazadas."""
    dy = int(rn['dur_semestres'] / 2); t = rn['anio_t']
    def coh(ingreso, n, prog='P1', **kw):
        e = {**rn, 'anio_ingreso': ingreso, 'n_t': n, 'prog_total_t': 400, 'programa': prog, **kw}
        if ingreso == t:
            e.update(n_prev=None, ret_prev=None)
        return e
    base = [coh(t, 60), coh(t - 1, 50)]
    if dy >= 3:
        base.append(coh(t - 2, 40))
    def lote(filas, **kw):
        antes = M.llamadas
        d, c = app.proyectar_lote(M, pd.DataFrame(filas), **kw)
        return d, c, M.llamadas - antes
    def total(c, anio):
        v = c[c.anio_estudio_t1 == anio].cupos_esperados
        return float(v.sum()) if len(v) and v.notna().all() else (np.nan if len(v) else 0.0)
    d0, c0, _ = lote(base)
    out = []
    def reg(cid, tipo, prop, esp, cumple, d, llamadas, detalle):
        out.append(dict(caso=cid, tipo=tipo, proposito=prop, esperado=esp, estado_observado=', '.join(f'{k}:{v}' for k, v in d.estado.value_counts().items()),
                        llamadas_modelo=llamadas, mensajes=detalle[:300], resultado='Cumple' if cumple else 'No cumple'))

    # CP-21: una cohorte repetida no se suma dos veces y no llega al modelo
    d, c, ll = lote(base + [base[1]])
    dup = d[d.estado == 'DUPLICADA']
    ok = len(dup) == 2 and total(c, 3) == 0.0 and total(c, 1) == total(c0, 1) and ll == len(base) - 1
    reg('CP-21', 'Lote', 'cohorte duplicada en el CSV', 'ambas filas DUPLICADA, no suman y no llaman al modelo',
        ok, d, ll, f'año 3 sin duplicado {total(c0, 3):.1f}, con duplicado {total(c, 3):.1f}')

    # CP-22: una fila de ingreso rechazada (n_t = 4) no alimenta el supuesto de primer año
    d, c, ll = lote([coh(t, 4)] + base[1:])
    fila1 = c[c.anio_estudio_t1 == 1]
    ok = (d.iloc[0].estado == 'RECHAZADA' and len(fila1) == 1 and np.isnan(fila1.cupos_esperados.iloc[0])
          and 'sin dato' in fila1.origen.iloc[0])
    reg('CP-22', 'Lote', 'fila de ingreso rechazada (n_t = 4)', 'año 1 sin dato (no 4 ni 0) y marcado en origen', ok, d, ll,
        f'año 1: {fila1.cupos_esperados.tolist()} / {fila1.origen.tolist()}')

    # CP-23: el ingreso dado reemplaza al supuesto
    d, c, ll = lote(base, ingreso_proyectado={'P1': 75})
    fila1 = c[c.anio_estudio_t1 == 1]
    ok = fila1.cupos_esperados.iloc[0] == 75 and fila1.origen.iloc[0] == 'ingreso dado'
    reg('CP-23', 'Lote', 'ingreso proyectado entregado por el usuario', 'año 1 = 75 con origen «ingreso dado»', ok, d, ll,
        f'año 1: {fila1.cupos_esperados.tolist()}')

    # CP-24: los totales cuadran con el detalle
    d, c, ll = lote(base + [coh(t - 1, 30, prog='P2'), coh(t - 2, 3, prog='P2')])
    sumado = c[c.origen == 'continuidad (modelo)'].cupos_esperados.sum()
    esperado = d[d.estado == 'OK'].estudiantes_esperados.sum()
    p2 = c[c.programa == 'P2']
    ok = abs(sumado - esperado) < 0.5 and len(p2) > 0 and (p2.filas_excluidas == 1).all() and (d.estado == 'RECHAZADA').sum() == 1
    reg('CP-24', 'Lote', 'totales iguales a la suma de filas aceptadas', 'diferencia < 0,5 (redondeo) y la fila rechazada se informa',
        ok, d, ll, f'cupos {sumado:.1f} / detalle {esperado:.1f}')

    # CP-25: una fila fuera de alcance no suma
    d, c, ll = lote(base + [coh(t - 1, 50, prog='P3', tipo_inst_1='Institutos Profesionales')])
    ok = (d[d.programa == 'P3'].estado == 'RECHAZADA').all() and 'P3' not in set(c.programa)
    reg('CP-25', 'Alcance', 'cohorte de instituto profesional en el lote', 'rechazada y fuera de los totales', ok, d, ll,
        d[d.programa == 'P3'].mensajes.iloc[0])
    return out



if __name__ == '__main__':
    M = app.Modelo(); BIT, _ = ejecutar_casos(M)
    os.makedirs('evidencia', exist_ok=True); BIT.to_csv('evidencia/bitacora_pruebas.csv', index=False)
    print(BIT[['caso', 'tipo', 'estado_observado', 'llamadas_modelo', 'resultado']].to_string(index=False))
    print(f"{(BIT.resultado == 'Cumple').sum()} de {len(BIT)} casos cumplen")
