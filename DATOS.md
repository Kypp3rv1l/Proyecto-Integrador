# Datos

**Fuente:** SIES, Ministerio de Educación de Chile, «Matrícula en Educación Superior» 2017–2026 (bases públicas con MRUN anonimizado). Entregada al curso como `T04_muestra_SIES_2017_2026.zip`: muestra del 4% de los programas, un CSV por año.
**URL de descarga y fecha de acceso:** [completar con la URL oficial y la fecha en que se descargó]
**Licencia o condición de uso:** [confirmar en la fuente oficial; no se declara una licencia sin verificarla]

## Preparación (resumen)
- Se usa solo pregrado, estudiantes con MRUN y un registro por (año, programa, estudiante).
- Unidad de análisis: cohorte = programa (`codigo_unico`) × año de ingreso al programa (`anio_ing_carr_act`) observada en el año t.
- Objetivo: proporción de la cohorte de t que aparece en t+1 en el mismo programa.
- Se conservan cohortes de 5 o más estudiantes que aún no están en su último año nominal.
- Arancel: si `formato_valores` viene vacío (2017–2021), un valor menor a 10.000 se interpreta como UF; esa regla coincide con el campo declarado en los años 2022–2026 (0 discrepancias). El arancel en UF no se convierte y queda como faltante.
- Partición temporal: entrenamiento con cohortes observadas en 2019–2024 (4.731), prueba en 2025 (774). 2017 solo se usa como diagnóstico porque su año de ingreso viene vacío en la mayoría de las filas.

## Privacidad
Los datos son públicos y anonimizados. El prototipo trabaja con cifras agregadas por cohorte; en `datos_ejemplo/` y `evidencia/` no hay registros individuales, MRUN ni fechas de nacimiento.

## Limitaciones de los datos
Muestra del 4%; códigos de programa que cambian entre años (ver README); 2020 y 2021 incluyen efectos de la pandemia y se mantienen en el entrenamiento.
