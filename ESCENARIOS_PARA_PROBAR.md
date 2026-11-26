# Escenarios para probar el formulario

Punto de partida: el caso que viene cargado en el formulario (cohorte real de una universidad: anio_t 2025, anio_ingreso 2023, n_t 22, prog_total_t 45, n_prev 23, ret_prev 0,9565, prop_mujer 0,3182, edad_media 22,68, dur_semestres 8, arancel 4347000). Cambie SOLO el campo indicado, pulse «Estimar continuidad» y compare con el resultado esperado. Después devuelva el campo a su valor original.
Los porcentajes son los obtenidos al ejecutar cada escenario con el modelo entregado.

## A. Debe dar resultado (OK)
- Sin cambios: 86% (unos 18,9 de 22); el valor real en 2026 fue 91%
- n_t = 5 (límite válido): 86%
- anio_ingreso = 2024 (2.º año): 84%
- anio_ingreso = 2025 y vaciar n_prev y ret_prev (cohorte nueva): 72%
- ret_prev = 1 (límite válido): 86%
- ret_prev = 0,5 (coma decimal): 67%

## B. Debe dar resultado CON AVISO
- Vaciar n_prev y ret_prev: 76% + aviso de cohorte antigua sin historial
- Vaciar edad_media: 86% + aviso de imputación
- Vaciar arancel_anual_clp: 86% + aviso de imputación
- arancel = 9000000000: 86% + aviso fuera del rango de entrenamiento
- arancel = 10000: 85% + aviso fuera del rango (un modelo de árboles no extrapola: repite el valor del borde)

## C. Debe RECHAZAR (el modelo no se llama)
Fuera del alcance
- tipo_inst_1 = Centros de Formación Técnica -> "está fuera del alcance del modelo, que solo estima continuidad en universidades"
- tipo_inst_1 = Institutos Profesionales -> mismo mensaje
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
- n_t = 46 -> "n_t (46) no puede superar prog_total_t (45)"
- prog_total_t = 5 -> "n_t (22) no puede superar prog_total_t (5)"
- anio_ingreso = 2026 -> "no puede ser posterior a anio_t"
- anio_ingreso = 2025 (sin vaciar n_prev y ret_prev) -> "la cohorte ingresa este año: n_prev y ret_prev deben ir vacíos"
- Vaciar solo n_prev, o solo ret_prev -> "deben informarse juntos"
- anio_ingreso = 2022 -> "la cohorte cursa su año 4 de 4: no le queda un año nominal por delante"
- dur_semestres = 3 -> "cursa su año 3 de 1.5: no le queda un año nominal por delante"

## D. Modo lote
- `cupos_app.py lote datos_ejemplo/cohortes_2025.csv --salida resultados`: 328 cohortes, todas aceptadas.
- Copiar una fila del CSV y pegarla al final: las dos filas quedan como DUPLICADA y su año de estudio deja de sumar.
- Cambiar a 4 el n_t de una fila de ingreso (anio_ingreso = 2025): la fila se rechaza y el año 1 de ese programa queda «sin dato» en vez de sumar 4.

## E. Casos reales completos
Ver casos_para_probar.json y .csv (5 cohortes universitarias reales con su valor observado en 2026). También se cargan desde la página, en «Cargar un caso real».
