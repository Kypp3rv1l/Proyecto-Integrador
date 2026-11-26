# Continuidad de cohortes y cupos

Proyecto Integrador, Desarrollo de Soluciones Inteligentes (UBO), docente Enrique Pastene. Prototipo funcional (EVAL-01, 13-11-2026), corregido para el informe y la defensa (EVAL-02, 27-11-2026).
Integrantes: **Ivan Oliva y Bastian Gonzalez, Paralelo 2**

Dada una cohorte (programa y año de ingreso) matriculada en el año t, la aplicación estima qué parte seguirá en el mismo programa en t+1 y la convierte en estudiantes esperados. Con un CSV de cohortes, suma esos estudiantes por programa y año de estudio para anticipar cupos. Se usa desde una página local en el navegador. El modelo es una regresión con Random Forest entrenada con matrícula SIES 2017–2026 (muestra del 4% de los programas) y cubre **solo universidades**: en centros de formación técnica e institutos profesionales muchos códigos de programa desaparecen de un año a otro, y eso no es continuidad real (ver «Alcance»).

## Instructivo paso a paso (ejecución y verificación)

Pasos para ejecutar y verificar el proyecto desde una terminal, en orden. Cada paso indica qué debe aparecer. Los comandos son para Linux y macOS; en Windows, reemplazar `.venv/bin/python` por `.venv\Scripts\python` y `python3` por `py`. Todos se ejecutan desde la carpeta raíz del repositorio.

**A. Preparar el entorno**

1. `python3 --version`
   Comprobar: Python 3.11, 3.12 o 3.13.
2. `python3 -m venv .venv`
   Comprobar: se crea la carpeta `.venv`.
3. `.venv/bin/python -m pip install -r requirements.txt`
4. `.venv/bin/python -c "import pandas, sklearn; print(pandas.__version__, sklearn.__version__)"`
   Comprobar: imprime `2.2.3 1.8.0`. El modelo guardado solo carga con scikit-learn 1.8.0.

**B. Usar la aplicación**

5. `.venv/bin/python cupos_app.py demo`
   Comprobar: el caso válido dice `ESTADO: OK` con `continuidad estimada: 0.860 | estudiantes esperados: 18.9`; el inválido dice `ESTADO: RECHAZADA` con un error de arancel en UF y otro de región; la última línea es `llamadas al modelo: 1 (el inválido no llegó al modelo)`.
6. `.venv/bin/python cupos_app.py caso datos_ejemplo/caso_valido.json`
   Comprobar: `ESTADO: OK` y `continuidad estimada: 0.860`.
7. `.venv/bin/python cupos_app.py lote datos_ejemplo/cohortes_2025.csv --salida resultados`
   Comprobar: `OK    328` y al final `escrito en resultados/: proyeccion_cohortes.csv y cupos_esperados.csv`. Ambos archivos existen en `resultados/`.
8. `.venv/bin/python cupos_app.py web --no-abrir --puerto 8000` (dejarlo corriendo en otra terminal o en segundo plano)
   Comprobar: imprime `Servidor en http://127.0.0.1:8000`.
9. `curl -s http://127.0.0.1:8000 | grep -c "Estimar continuidad"`
   Comprobar: un número mayor que 0 (la página carga). En un navegador, la misma dirección muestra el formulario.
10. `curl -s -X POST -d "anio_t=2025&anio_ingreso=2023&n_t=4" http://127.0.0.1:8000 | grep -c "Entrada rechazada"`
    Comprobar: un número mayor que 0 (una cohorte de 4 estudiantes se rechaza sin llamar al modelo).
11. Detener el servidor del paso 8 (Ctrl+C en su terminal).

**C. Pruebas**

12. `.venv/bin/python casos_prueba.py`
    Comprobar: la última línea es `25 de 25 casos cumplen`. Tarda segundos.
13. `.venv/bin/python pruebas_escenarios.py`
    Comprobar: la última línea es `TOTAL 41279 | cumplen 41279 | fallas 0 | excepciones 0`. Tarda 2 a 3 minutos.
14. `.venv/bin/python pruebas_adversarias.py`
    Comprobar: la última línea es `TOTAL 122 | cumplen 122 | DEFECTOS 0`. Tarda menos de un minuto.

**D. Regenerar modelo y evidencia desde los datos (opcional)**

Requiere `T04_muestra_SIES_2017_2026.zip` (la muestra entregada en el curso; no se incluye en el repositorio) copiado en la carpeta raíz. Estos pasos sobrescriben el modelo y `evidencia/`; con los mismos datos y versiones, los archivos resultantes son idénticos a los guardados.

15. `.venv/bin/python -m pip install -r requirements-extra.txt`
16. `.venv/bin/python construir_modelo.py T04_muestra_SIES_2017_2026.zip`
    Comprobar: `modelo guardado | filas entrenamiento 2312 | MAE prueba 2025 0.0723`.
17. `.venv/bin/python comparar_modelos.py T04_muestra_SIES_2017_2026.zip`
    Comprobar: Random Forest tiene el menor `MAE_medio` (0.0975), luego Ridge (0.1070).
18. `.venv/bin/python comparar_hiperparametros.py T04_muestra_SIES_2017_2026.zip`
    Comprobar: con profundidad 5, los tres números de árboles dan 0.0975.
19. `.venv/bin/python ejecutar_validacion.py T04_muestra_SIES_2017_2026.zip`
    Comprobar: termina con `OK. Evidencia en evidencia`. Tarda cerca de un minuto.
20. `git status --short evidencia modelo_continuidad.joblib contrato_modelo.json`
    Comprobar: no lista archivos modificados (la evidencia regenerada es igual a la guardada). Si el proyecto se descargó como zip y no como repositorio git, omitir este paso.

**E. Regenerar el informe (opcional)**

21. `cd informe`
22. `../.venv/bin/python figuras.py .. .`
23. `../.venv/bin/python informe.py .. PI_Informe_Tecnico.pdf`
24. `../.venv/bin/python a_word.py .. PI_Informe_Tecnico.docx`
    Comprobar: `PI_Informe_Tecnico.pdf` (8 páginas) y `PI_Informe_Tecnico.docx` actualizados en `informe/`.

## Ejecutar en un PC (Windows)

El Python que usa el proyecto queda dentro de esta misma carpeta (`.venv`). No instala nada en el sistema ni pide permisos de administrador.

1. En GitHub, pulsar **Code** y luego **Download ZIP**.
2. Descomprimir en una carpeta donde se pueda escribir, por ejemplo Documentos.
   Comprobar: la carpeta contiene `iniciar.bat` y `cupos_app.py`.
3. Abrir el Símbolo del sistema y escribir `py --version`. Si `py` no existe, escribir `python --version`.
   Comprobar: dice 3.11, 3.12 o 3.13. Si no, ver «Si el PC no tiene Python».
4. Hacer doble clic en `iniciar.bat`.
   La primera vez crea `.venv` e instala las librerías (necesita internet y tarda unos minutos). Las siguientes veces abre en segundos.
   Comprobar: la ventana negra dice `Servidor en http://127.0.0.1:8000` y se abre el navegador.
5. En la página, elegir un caso en **Cargar un caso real**.
   Comprobar: aparece un porcentaje grande y una fila de puntos.
6. Pulsar **Solo 4 estudiantes** en **Probar un error**.
   Comprobar: el panel dice «Entrada rechazada» y el campo se marca en rojo.
7. Para cerrar, pulsar Ctrl+C en la ventana negra.

Si el puerto 8000 está ocupado: `iniciar.bat --puerto 8001`.

## Qué se debería ver

Con el caso que viene cargado en el formulario (`datos_ejemplo/caso_valido.json`: cohorte real de 22 estudiantes de una universidad, ingreso 2023 observada en 2025):

- Resultado: 86%, unos 18,9 estudiantes de 22 siguen en el programa el año siguiente, cuando cursen el año 4.
- Error típico de referencia: ±7,2 puntos porcentuales.
- Valor real de esa cohorte en 2026: 91%.

Con **Solo 4 estudiantes** no hay porcentaje: el panel dice «Entrada rechazada» y el mensaje empieza con `n_t`. En ese caso el modelo no se llama.

## Sin internet en el PC

Las librerías se descargan una vez en otro PC con internet y se llevan en la carpeta.

1. En un PC con internet, con la misma versión de Python (por ejemplo 3.12) y Windows, abrir una terminal en esta carpeta.
2. Escribir `py -m pip download -r requirements.txt -d wheels`.
   Comprobar: aparece la carpeta `wheels` con archivos `.whl`.
3. Copiar la carpeta completa (con `wheels`) al PC sin internet.
4. Hacer doble clic en `iniciar.bat`. Detecta `wheels` e instala desde ahí.

## Si el PC no tiene Python

1. Instalar Python 3.12 desde python.org marcando «Install for current user» (no requiere administrador), o pedir al laboratorio la versión 3.11 a 3.13.
2. Repetir desde el paso 3.

Plan B sin instalar nada: abrir `PI06_Prototipo_Cupos.ipynb` en Google Colab, ejecutar la primera celda y subir el zip del repositorio cuando lo pida.

## macOS y Linux

1. Abrir una terminal en la carpeta.
2. `bash iniciar.sh`

## Otras formas de usarlo

Desde la carpeta, con el Python local (`.venv\Scripts\python` en Windows, `.venv/bin/python` en macOS y Linux):

- `cupos_app.py demo`: un caso válido y uno rechazado.
- `cupos_app.py caso datos_ejemplo/caso_valido.json`: un caso propio.
- `cupos_app.py lote datos_ejemplo/cohortes_2025.csv --salida resultados`: proyección de cupos a partir de un CSV de cohortes.

## Datos de entrada

Son 19 campos: 10 numéricos y 9 categóricos. Las categorías permitidas y los rangos de referencia están en `contrato_modelo.json`.

| Campo | Qué es | Regla |
|---|---|---|
| `anio_t` | Año en que se observa la cohorte | Entero, 2019 a 2040 |
| `anio_ingreso` | Año en que la cohorte entró al programa | Entero, no posterior a `anio_t` |
| `n_t` | Estudiantes de la cohorte en `anio_t` | Entero, mínimo 5 |
| `prog_total_t` | Estudiantes de todo el programa en `anio_t` | Entero, no menor que `n_t` |
| `n_prev` | Estudiantes de la cohorte el año anterior | Opcional; va junto con `ret_prev` |
| `ret_prev` | Proporción que la cohorte retuvo del año anterior a `anio_t` | Opcional, 0 a 1 |
| `prop_mujer` | Proporción de mujeres en la cohorte | 0 a 1 |
| `edad_media` | Edad promedio de la cohorte | Opcional, 14 a 90 |
| `dur_semestres` | Duración del programa | Entero, 1 a 20 semestres |
| `arancel_anual_clp` | Arancel anual | Opcional, en pesos chilenos, no en UF |
| `tipo_inst_1` | Tipo de institución | Solo Universidades; CFT e IP se rechazan por estar fuera del alcance |
| `area_conocimiento` | Área de conocimiento | 10 opciones |
| `region_sede` | Región de la sede | 16 opciones |
| `jornada` | Jornada | 5 opciones |
| `modalidad` | Modalidad | 3 opciones |
| `nivel_carrera_1` | Nivel de la carrera | 5 opciones |
| `acreditada_carr` | Acreditación de la carrera | 3 opciones |
| `acreditada_inst` | Acreditación de la institución | 3 opciones |
| `tipo_plan_carr` | Tipo de plan | 3 opciones |

Notas:

- Los números pueden escribirse como `2000000`, `2.000.000`, `$2.000.000` o `50%`.
- Si la cohorte ingresa en `anio_t`, `n_prev` y `ret_prev` van vacíos.
- Una cohorte en su último año nominal se rechaza: ahí «no continuar» sería titularse.
- Un error bloquea la predicción. Una advertencia la deja pasar y avisa (por ejemplo, arancel fuera del rango de entrenamiento o campo opcional vacío).

## Modo lote: cómo se suman los cupos

- Una cohorte se identifica por `programa` + `anio_t` + `anio_ingreso`. Si esa combinación aparece más de una vez, todas sus filas quedan como `DUPLICADA`: no se sabe cuál es la correcta, así que ninguna suma.
- Ninguna fila rechazada o duplicada suma a un total. La columna `filas_excluidas` de `cupos_esperados.csv` dice cuántas se dejaron fuera en cada programa.
- El año 1 de t+1 (ingreso nuevo) no lo estima el modelo y se calcula aparte: se usa el ingreso proyectado si se entrega; si no, el ingreso de t del mismo programa, solo cuando esa fila fue aceptada. Si no hay un dato válido, queda vacío con el motivo en `origen` («sin dato…»), en vez de un 0 que parezca real.
- Los cupos se separan por programa, año siguiente (`anio_t1`) y año de estudio.

## Pruebas

Con el Python local, desde la carpeta:

| Comando | Qué prueba | Debe terminar con | Demora |
|---|---|---|---|
| `casos_prueba.py` | Bitácora de 25 casos escritos a mano (20 de una cohorte y 5 del modo lote) | `25 de 25 casos cumplen` | Segundos |
| `pruebas_escenarios.py` | 41.279 escenarios contra un verificador escrito aparte | `TOTAL 41279 \| cumplen 41279 \| fallas 0 \| excepciones 0` | 2 a 3 minutos |
| `pruebas_adversarias.py` | 122 casos pensados para romper la aplicación | `TOTAL 122 \| cumplen 122 \| DEFECTOS 0` | Menos de un minuto |

Para regenerar todo desde los datos: `construir_modelo.py T04_muestra_SIES_2017_2026.zip` (entrena) y después `ejecutar_validacion.py T04_muestra_SIES_2017_2026.zip` (evidencia y ejemplos). Necesitan `pip install -r requirements-extra.txt` y el zip en la carpeta (no se incluye en el repositorio).

Los resultados guardados están en `evidencia/`. Casos para probar a mano: `ESCENARIOS_PARA_PROBAR.md`.

## Contenido

| Archivo | Para qué sirve |
|---|---|
| `iniciar.bat`, `iniciar.sh` | Crean el Python local la primera vez y abren la página |
| `cupos_app.py` | Aplicación: validación, predicción, lote, página web y línea de comandos |
| `modelo_continuidad.joblib`, `contrato_modelo.json` | Modelo entrenado y su contrato (variables, categorías, rangos, versiones, huellas) |
| `construir_modelo.py` | Entrena el modelo y escribe el contrato |
| `comparar_modelos.py` | Compara Random Forest, Ridge y dos líneas base en validación 2022–2024 |
| `comparar_hiperparametros.py` | Compara número de árboles y profundidad del Random Forest en la misma validación |
| `casos_prueba.py`, `pruebas_escenarios.py`, `pruebas_adversarias.py` | Los tres niveles de prueba |
| `ejecutar_validacion.py` | Regenera `evidencia/` |
| `PI06_Prototipo_Cupos.ipynb` | Demostración en notebook, ya ejecutada |
| `datos_ejemplo/`, `resultados_ejemplo/` | Un caso en JSON, 5 casos reales para cargar en la página, 328 cohortes universitarias 2025 agregadas (sin personas) y la salida del modo lote |
| `evidencia/` | Métricas, retro-prueba de cupos, errores por grupo, figuras y resultados de pruebas |
| `requirements.txt`, `requirements-extra.txt` | Librerías de la aplicación y las adicionales para el notebook y la validación |
| `informe/` | Informe técnico en PDF (EVAL-02), sus figuras y los scripts que lo generan desde `evidencia/` |
| `DATOS.md` | Origen, tratamiento y límites de los datos |
| `ESCENARIOS_PARA_PROBAR.md` | Casos para probar el formulario a mano, con su resultado esperado |

Requiere Python 3.11 a 3.13, pandas 2.2.3 y scikit-learn 1.8.0. El modelo guardado depende de esa versión de scikit-learn.

## Resultados

Prueba temporal principal: entrenamiento con cohortes universitarias observadas en 2019–2024 (2.312) y prueba en 2025 (331 cohortes, 110 programas). Las cifras salen de `evidencia/`.

| | MAE | RMSE | R² |
|---|---|---|---|
| Modelo (Random Forest) | 0,072 | 0,103 | 0,24 |
| Base: retención del año anterior | 0,089 | 0,129 | −0,21 |
| Base: media de entrenamiento | 0,098 | 0,126 | −0,16 |

El MAE es más bajo que en la versión con CFT e IP (0,133) porque en universidades la continuidad es más alta y estable. Por la misma razón el R² es modesto: hay poca variación que explicar.

Elección del modelo (`comparar_modelos.py`, validación con años de prueba 2022, 2023 y 2024, sin tocar 2025): Random Forest 0,098 de MAE medio, Ridge 0,107, constante 0,113 y persistencia 0,123. El criterio, fijado antes de comparar, era elegir el menor MAE salvo diferencias menores a 0,002; por eso se cambió Ridge (entrega 1) por Random Forest.

Varios cortes temporales (`evidencia/validacion_temporal.csv`), cada uno entrenado solo con los años anteriores:

| Año de prueba | Modelo | Base: retención anterior | Base: media |
|---|---|---|---|
| 2022 | 0,108 | 0,124 | 0,129 |
| 2023 | 0,097 | 0,122 | 0,124 |
| 2024 | 0,088 | 0,104 | 0,111 |
| 2025 | 0,072 | 0,089 | 0,098 |

El modelo le gana a ambas bases en los cuatro cortes.

- Retro-prueba de cupos (proyectar 2026 con datos de 2025 y comparar con la matrícula real): por cohorte, el error es 3,29 estudiantes con el modelo y 3,84 con la retención del año anterior. Por programa (sumando cohortes) quedan empatados: 7,13 contra 7,12. El sesgo total del modelo es −2,3% (subestima levemente).
- Integración: 328 de 328 cohortes dan la misma predicción en la aplicación y en el pipeline de referencia (3 quedan fuera por tener el arancel en UF).

## Alcance: solo universidades

`evidencia/alcance_por_tipo.csv` muestra el porcentaje de cohortes cuyo código de programa ya no existe al año siguiente. En CFT fue 26,2% en 2025 (contra 5,7% en 2023 y 1,0% en 2024); en universidades, 0,3% en 2025. Ese salto lo cuenta la base como «no continúa», aunque probablemente sean cambios administrativos de códigos. Además, el proyecto está pensado para la planificación académica en universidades. Por eso el modelo se entrena solo con universidades y la aplicación rechaza las otras instituciones con un mensaje claro.

## Límites

- Cohortes pequeñas: de 5 a 9 estudiantes el MAE es 0,120 y el modelo subestima (sesgo −0,11); con 50 o más, 0,059.
- Por programa, el modelo empata con la retención del año anterior; la ventaja está en la estimación por cohorte.
- Un Random Forest responde por tramos: cambiar la retención previa en 5 puntos mueve más de 2 puntos la predicción en una de cada cuatro cohortes (`evidencia/robustez.csv`).
- El año de estudio es nominal (año observado − año de ingreso + 1): quien repite cuenta en su año nominal.
- Los cupos solo suman a quienes siguen en su cohorte; no incluyen traslados desde otros programas ni reincorporaciones.
- Los hiperparámetros (300 árboles, profundidad 5) se fijaron antes de comparar. Revisados después en 2022–2024 (`comparar_hiperparametros.py`): el número de árboles no cambia el error y la profundidad 8 mejora 0,0022 de MAE medio; se mantuvo 5 porque esa diferencia es de 0,2 puntos porcentuales.
- En la persistencia, las cohortes sin retención previa usan la mediana de entrenamiento en `comparar_modelos.py` y la media en la validación por cortes; por eso esa línea base muestra cifras algo distintas en cada tabla.
- El modelo se entrenó con los mismos programas que se prueban (en años distintos); no se midió su desempeño en programas nuevos.
- Ingreso nuevo: el modelo no estima el año 1 de t+1. Se entrega como dato o se asume igual al de t, y la salida lo marca.
- Los datos son una muestra del 4% de los programas. Origen y tratamiento: `DATOS.md`.
- Es una ayuda para planificar cupos, no una decisión sobre personas.

## Declaración de uso de IA

Se utilizó Claude (Anthropic) como apoyo posterior al trabajo del equipo. El equipo definió el problema, el alcance y el diseño, y escribió la primera versión del código, los análisis, la documentación y el informe. La IA se usó sobre ese material para corregir errores, mejorar y ordenar el código, ampliar las pruebas y revisar la redacción. Cada cambio se revisó y se volvió a ejecutar antes de incorporarlo. Los resultados informados (métricas, pruebas y evidencias) corresponden a ejecuciones reales del código de este repositorio.

| Área | Trabajo del equipo | Aporte de la IA | Cómo se comprobó |
|---|---|---|---|
| Aplicación y scripts | Primera versión de validación, predicción, modo lote, entrenamiento, comparación y validación | Corrección de errores, reorganización y mejoras | Suites de prueba y ejecución de la aplicación |
| Corrección del modo lote | Identificó las fallas de la entrega 1 y definió las reglas nuevas | Apoyo para implementar y depurar | CP-21 a CP-24 |
| Alcance y elección del modelo | Análisis por tipo de institución, decisión de limitar a universidades y cambio a Random Forest según el criterio del PI-02 | Revisión del análisis y apoyo en la comparación | `evidencia/alcance_por_tipo.csv` y `comparacion_modelos.csv` |
| Validación temporal | Decidió agregar cortes por la observación del profesor | Apoyo para implementarlos | `evidencia/validacion_temporal.csv` |
| Página web, notebook, figuras y repositorio | Diseño y contenido | Mejoras de presentación y orden | Ejecución de la aplicación y del notebook |
| Informe y presentación | Estructura y redacción | Revisión de redacción y formato | Cifras contrastadas con `evidencia/` |

**Decisiones del equipo:** Definimos que la demostración debía ser ejecutable y permitir observar directamente cómo se realizan las predicciones, por lo que optamos por desarrollar una aplicación web local y mantener el notebook como respaldo. También solicitamos comprobar que la retención utilizada como objetivo estuviera respaldada por los datos. Establecimos probar distintos escenarios, incluidas entradas incorrectas y casos límite, para identificar y corregir posibles fallas. Finalmente, definimos adaptar el diseño de la aplicación para la presentación y organizar el repositorio con instrucciones que permitieran ejecutar el proyecto en los computadores de la universidad. Después de la entrega 1 decidimos limitar el modelo a universidades, corregir cómo el lote suma los cupos y validar con varios cortes temporales.
