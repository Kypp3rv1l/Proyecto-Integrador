# Datos

**Fuente:** SIES, Ministerio de Educación de Chile, «Matrícula en Educación Superior» 2017–2026 (bases públicas con MRUN anonimizado). Entregada al curso como `T04_muestra_SIES_2017_2026.zip`: muestra del 4% de los programas, un CSV por año.
**URL de descarga:** https://datosabiertos.mineduc.cl/matricula-en-educacion-superior/ (portal de datos abiertos del Mineduc; un archivo `Matricula-Ed-Superior-AAAA.rar` por año, 2007–2026). La base 2026 corresponde al corte publicado el 10-08-2026 (`20260810_Matrícula_Ed_Superior_2026_PUBL_MRUN.csv`), acompañada de su ficha de registro `ER_Matricula_Educacion_Superior_2007_2026_PUBL_MRUN.pdf`.
**Fecha de consulta de la página:** 21-11-2026.
**Licencia o condición de uso:** la página de descarga no declara una licencia ni términos de uso (revisada el 21-11-2026). Son datos públicos y anonimizados publicados por el Mineduc; se usan con fines académicos y citando la fuente. No se redistribuyen las bases originales: el repositorio solo incluye cohortes agregadas.

## Preparación (resumen)
- Se usa solo pregrado, estudiantes con MRUN y un registro por (año, programa, estudiante).
- Unidad de análisis: cohorte = programa (`codigo_unico`) × año de ingreso al programa (`anio_ing_carr_act`) observada en el año t.
- Objetivo: proporción de la cohorte de t que aparece en t+1 en el mismo programa.
- Se conservan cohortes de 5 o más estudiantes que aún no están en su último año nominal.
- Arancel: si `formato_valores` viene vacío (2017–2021), un valor menor a 10.000 se interpreta como UF; esa regla coincide con el campo declarado en los años 2022–2026 (0 discrepancias). El arancel en UF no se convierte y queda como faltante.
- Alcance: solo universidades (`tipo_inst_1 = Universidades`). En CFT e IP muchos códigos de programa desaparecen de un año a otro (en CFT, el 26,2% de las cohortes de 2025), y la base lo registra como «no continúa».
- Partición temporal: entrenamiento con cohortes universitarias observadas en 2019–2024 (2.312), prueba en 2025 (331). Además se validó con cortes en 2022, 2023 y 2024, cada uno entrenado solo con los años anteriores. 2017 solo se usa como diagnóstico porque su año de ingreso viene vacío en la mayoría de las filas.

## Privacidad
Los datos son públicos y anonimizados. El prototipo trabaja con cifras agregadas por cohorte; en `datos_ejemplo/` y `evidencia/` no hay registros individuales, MRUN ni fechas de nacimiento.

## Limitaciones de los datos
Muestra del 4%; códigos de programa que cambian entre años (ver README); 2020 y 2021 incluyen efectos de la pandemia y se mantienen en el entrenamiento; el año de estudio se calcula de forma nominal desde el año de ingreso, por lo que no refleja repitencia.
