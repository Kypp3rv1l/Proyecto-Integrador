# Continuidad de cohortes y cupos

Proyecto Integrador, Desarrollo de Soluciones Inteligentes (UBO), docente Enrique Pastene. Prototipo funcional (EVAL-01, 13-11-2026).
Integrantes: **Ivan Oliva y Bastian Gonzalez, Paralelo 2**

Dada una cohorte (programa y año de ingreso) matriculada en el año t, la aplicación estima qué parte seguirá en el mismo programa en t+1 y la convierte en estudiantes esperados. Con un CSV de cohortes, suma esos estudiantes por programa y año de estudio para anticipar cupos. Se usa desde una página local en el navegador. El modelo es una regresión Ridge entrenada con matrícula SIES 2017–2026 (muestra del 4% de los programas).

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

Con el caso que viene cargado en el formulario (`datos_ejemplo/caso_valido.json`: 10 estudiantes, instituto profesional, ingreso 2024 observado en 2025):

- Resultado: 52%, unos 5,2 estudiantes de 10 siguen en el programa el año siguiente.
- Error típico de referencia: ±13,3 puntos porcentuales.
- Valor real de esa cohorte en 2026: 50%.

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
2. `chmod +x iniciar.sh && ./iniciar.sh`

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
| `tipo_inst_1` | Tipo de institución | Universidades, Institutos Profesionales o Centros de Formación Técnica |
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
- Un error bloquea la predicción. Una advertencia la deja pasar y avisa (por ejemplo, cohorte de CFT, arancel fuera del rango de entrenamiento o campo opcional vacío).

## Pruebas

Con el Python local, desde la carpeta:

| Comando | Qué prueba | Debe terminar con | Demora |
|---|---|---|---|
| `casos_prueba.py` | Bitácora de 20 casos escritos a mano | `20 de 20 casos cumplen` | Segundos |
| `pruebas_escenarios.py` | 41.282 escenarios contra un verificador escrito aparte | `TOTAL 41282 \| cumplen 41282 \| fallas 0 \| excepciones 0` | Cerca de un minuto |
| `pruebas_adversarias.py` | 120 casos pensados para romper la aplicación | `TOTAL 120 \| cumplen 120 \| DEFECTOS 0` | Cerca de un minuto |

`ejecutar_validacion.py` regenera `evidencia/` con los datos reales. Necesita `pip install -r requirements-extra.txt` y el archivo `T04_muestra_SIES_2017_2026.zip` en la carpeta (no se incluye en el repositorio).

Los resultados guardados están en `evidencia/`. Casos para probar a mano: `ESCENARIOS_PARA_PROBAR.md`.

## Contenido

| Archivo | Para qué sirve |
|---|---|
| `iniciar.bat`, `iniciar.sh` | Crean el Python local la primera vez y abren la página |
| `cupos_app.py` | Aplicación: validación, predicción, lote, página web y línea de comandos |
| `modelo_continuidad.joblib`, `contrato_modelo.json` | Modelo entrenado y su contrato (variables, categorías, rangos, versiones, huellas) |
| `construir_modelo.py` | Entrena el modelo y escribe el contrato |
| `casos_prueba.py`, `pruebas_escenarios.py`, `pruebas_adversarias.py` | Los tres niveles de prueba |
| `ejecutar_validacion.py` | Regenera `evidencia/` |
| `PI06_Prototipo_Cupos.ipynb` | Demostración en notebook, ya ejecutada |
| `datos_ejemplo/`, `resultados_ejemplo/` | Un caso en JSON, 770 cohortes 2025 agregadas (sin personas) y la salida del modo lote |
| `evidencia/` | Métricas, retro-prueba de cupos, errores por grupo, figuras y resultados de pruebas |
| `requirements.txt`, `requirements-extra.txt` | Librerías de la aplicación y las adicionales para el notebook y la validación |
| `DATOS.md` | Origen, tratamiento y límites de los datos |
| `ESCENARIOS_PARA_PROBAR.md` | Casos para probar el formulario a mano, con su resultado esperado |

Requiere Python 3.11 a 3.13, pandas 2.2.3 y scikit-learn 1.8.0. El modelo guardado depende de esa versión de scikit-learn.

## Resultados

Prueba temporal: entrenamiento con cohortes observadas en 2019–2024 (4.731) y prueba en 2025 (774). Las cifras salen de `evidencia/`.

| | MAE | RMSE | R² |
|---|---|---|---|
| Modelo (Ridge) | 0,133 | 0,206 | 0,23 |
| Base: retención del año anterior | 0,154 | 0,241 | −0,05 |
| Base: media de entrenamiento | 0,168 | 0,235 | 0,00 |

- Retro-prueba de cupos (proyectar 2026 con datos de 2025 y comparar con la matrícula real): el error por cohorte es de 6,26 estudiantes con el modelo y 7,35 con la retención del año anterior. Por programa, 11,2 contra 12,6.
- Integración: 770 de 770 cohortes dan la misma predicción en la aplicación y en el pipeline de referencia.

## Límites

- Centros de formación técnica: el error es mayor (MAE 0,285). Muchos códigos de programa desaparecen de un año a otro y la base los cuenta como «no continúa». Si el código sigue existiendo en 2026, el MAE baja a 0,152.
- Cohortes pequeñas: de 5 a 9 estudiantes el MAE es 0,208; con 50 o más, 0,098.
- Ingreso nuevo: el modelo no estima el año 1 de t+1. Se entrega como dato o se asume igual al de t, y la salida lo marca.
- Los datos son una muestra del 4% de los programas. Origen y tratamiento: `DATOS.md`.
- Es una ayuda para planificar cupos, no una decisión sobre personas.

## Declaración de uso de IA

Se utilizó un asistente de IA generativa (Claude, de Anthropic) durante el desarrollo del proyecto, principalmente como apoyo en la estructuración y escritura del código, la corrección de errores y la mejora de la presentación de las pruebas, la documentación y el informe a partir del contenido elaborado por el equipo. Los objetivos, el alcance y las decisiones sobre el funcionamiento del sistema fueron definidos por el equipo. La implementación del código contó con asistencia de IA, cuya utilización estuvo orientada a facilitar el desarrollo y resolver problemas técnicos. Los resultados informados (métricas, pruebas y evidencias) corresponden a ejecuciones reales del código incluido en este repositorio.

**Revisión del equipo:** Revisamos el código y comprobamos la separación de los módulos, las validaciones de entradas y el funcionamiento de la aplicación web. Ejecutamos las pruebas y contrastamos las métricas del informe con los resultados guardados en la carpeta `evidencia/`. También verificamos que las instrucciones y la documentación coincidieran con el funcionamiento real del proyecto.

**Decisiones del equipo:** Definimos que la demostración debía ser ejecutable y permitir observar directamente cómo se realizan las predicciones, por lo que optamos por desarrollar una aplicación web local y mantener el notebook como respaldo. También solicitamos comprobar que la retención utilizada como objetivo estuviera respaldada por los datos. Establecimos probar distintos escenarios, incluidas entradas incorrectas y casos límite, para identificar y corregir posibles fallas. Finalmente, definimos adaptar el diseño de la aplicación para la presentación y organizar el repositorio con instrucciones que permitieran ejecutar el proyecto en los computadores de la universidad.
