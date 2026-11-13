# Escenarios para probar el formulario

Punto de partida: el caso que viene cargado en el formulario (anio_t 2025, anio_ingreso 2024, n_t 10, prog_total_t 26, n_prev 18, ret_prev 0.3889, prop_mujer 0.3, edad_media 32.8, dur_semestres 8, arancel 2000000, Institutos Profesionales). Cambie SOLO el campo indicado, pulse Predecir y compare con el resultado esperado. Después devuelva el campo a su valor original.
Los porcentajes son los obtenidos al ejecutar cada escenario con el modelo entregado.

## A. Debe dar resultado (OK)
- Sin cambios: 52% (unos 5,2)
- n_t = 5 (límite válido): OK
- anio_ingreso = 2023 (3.er año): 53%
- anio_ingreso = 2025 y vaciar n_prev y ret_prev (cohorte nueva): 54%
- ret_prev = 1 (límite válido): 61%
- ret_prev = 0,5 (coma decimal): 54%
- tipo_inst_1 = Universidades: 49%

## B. Debe dar resultado CON AVISO
- Vaciar n_prev y ret_prev: 55% + aviso de cohorte antigua sin historial
- Vaciar edad_media: 60% + aviso de imputación
- Vaciar arancel_anual_clp: 45% + aviso de imputación
- tipo_inst_1 = Centros de Formación Técnica: 51% + aviso de error alto en CFT
- arancel = 9000000000: 82% + aviso fuera del rango de entrenamiento (muestra que un modelo lineal extrapola)
- arancel = 10000: 33% + aviso fuera del rango (ídem)

## C. Debe RECHAZAR (el modelo no se llama)
Campo faltante o vacío
- n_t vacío -> "campo obligatorio ausente"
- prop_mujer vacío -> "campo obligatorio ausente"
- Vaciar todos los campos numéricos -> un error por cada campo obligatorio
Tipo incorrecto
- n_t = diez -> "se espera un número"
- n_t = 10.5 -> "debe ser entero"
- dur_semestres = 7.5 -> "debe ser entero"
- ret_prev = nan -> "se espera un número"
- arancel = inf -> "se espera un número"
Fuera de rango
- n_t = 0, 4 o -3 -> "cohorte de menos de 5 estudiantes no es estimable"
- anio_t = 2018 (mínimo 2019) y 2041 (máximo 2040)
- ret_prev = 1.4 y ret_prev = -0.1
- prop_mujer = 1.2
- edad_media = 10 (mínimo 14) y 95 (máximo 90)
- dur_semestres = 0 y 21
Unidades del arancel
- arancel = 55 o 2.4 -> "parece estar en UF"
- arancel = 0 o -100000 -> "debe ser un monto positivo"
Coherencia entre campos
- n_t = 27 -> "n_t no puede superar prog_total_t (26)"
- prog_total_t = 5 -> "n_t (10) no puede superar prog_total_t (5)"
- anio_ingreso = 2026 -> "no puede ser posterior a anio_t"
- anio_ingreso = 2025 (sin vaciar n_prev y ret_prev) -> "la cohorte ingresa este año: n_prev y ret_prev deben ir vacíos"
- Vaciar solo n_prev, o solo ret_prev -> "deben informarse juntos"
- anio_ingreso = 2022 -> "la cohorte cursa su año 4 de 4: no le queda un año nominal por delante"
- dur_semestres = 3 -> "cursa su año 2 de 1.5: no le queda un año nominal por delante"

## D. Casos reales completos
Ver casos_para_probar.json y .csv (5 cohortes reales con su valor observado en 2026).
