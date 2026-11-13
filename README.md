# Continuidad de cohortes y cupos

Proyecto Integrador, Desarrollo de Soluciones Inteligentes (UBO), prototipo funcional.
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

## Sin internet en el PC

Las librerías se descargan una vez en otro PC con internet y se llevan en la carpeta.

1. En un PC con internet, con la misma versión de Python (por ejemplo 3.12) y Windows, abrir una terminal en esta carpeta.
2. Escribir `py -m pip download -r requirements.txt -d wheels`.
   Comprobar: aparece la carpeta `wheels` con archivos `.whl`.
3. Copiar la carpeta completa (con `wheels`) al PC sin internet.
4. Hacer doble clic en `iniciar.bat`. Detecta `wheels` y instala desde ahí.

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

El arancel va en pesos chilenos por año, no en UF. Los números pueden escribirse como `2000000`, `2.000.000`, `$2.000.000` o `50%`.

## Pruebas

- `casos_prueba.py`: bitácora de 20 casos (debe terminar con «20 de 20 casos cumplen»).
- `pruebas_escenarios.py`: 41.282 escenarios contra un verificador escrito aparte.
- `pruebas_adversarias.py`: 120 casos pensados para romper la aplicación.
- `ejecutar_validacion.py`: regenera `evidencia/` con los datos reales. Necesita `pip install -r requirements-extra.txt` y el archivo `T04_muestra_SIES_2017_2026.zip` en la carpeta (no se incluye en el repositorio).

Los resultados guardados están en `evidencia/`. Casos para probar a mano: `ESCENARIOS_PARA_PROBAR.md`.

## Contenido

| Archivo | Para qué sirve |
|---|---|
| `iniciar.bat`, `iniciar.sh` | Crean el Python local la primera vez y abren la página |
| `cupos_app.py` | Aplicación: validación, predicción, lote, página web y línea de comandos |
| `modelo_continuidad.joblib`, `contrato_modelo.json` | Modelo entrenado y su contrato (variables, categorías, rangos, versiones, huellas) |
| `PI06_Prototipo_Cupos.ipynb` | Demostración en notebook, ya ejecutada |
| `construir_modelo.py` | Entrena el modelo y escribe el contrato |
| `datos_ejemplo/`, `resultados_ejemplo/` | Un caso en JSON, 770 cohortes 2025 agregadas (sin personas) y la salida del modo lote |
| `evidencia/` | Métricas, retro-prueba de cupos, errores por grupo, figuras y resultados de pruebas |
| `DATOS.md` | Origen, tratamiento y límites de los datos |

## Resultados y límites

- Prueba temporal (entrenamiento con t de 2019 a 2024, prueba en t = 2025): error absoluto medio 0,133 contra 0,154 de la línea base «retención anterior» y 0,168 de la media.
- En centros de formación técnica el error es mayor (0,285): muchos códigos de programa desaparecen de un año a otro y la base los cuenta como «no continúa».
- El modelo no estima el ingreso nuevo (año 1 de t+1): se entrega como dato o se asume igual al de t, y la salida lo marca.
- Es una ayuda para planificar cupos, no una decisión sobre personas.

## Declaración de uso de IA

## Declaración de uso de IA

Se utilizó un asistente de IA generativa (Claude, de Anthropic) durante el desarrollo del proyecto, principalmente como apoyo en la estructuración y escritura del código, la corrección de errores y la mejora de la presentación de las pruebas, la documentación y el informe a partir del contenido elaborado por el equipo. Los objetivos, el alcance y las decisiones sobre el funcionamiento del sistema fueron definidos por el equipo. La implementación del código contó con asistencia de IA, cuya utilización estuvo orientada a facilitar el desarrollo y resolver problemas técnicos. Los resultados informados (métricas, pruebas y evidencias) corresponden a ejecuciones reales del código incluido en este repositorio.

**Revisión del equipo:** Revisamos el código y comprobamos la separación de los módulos, las validaciones de entradas y el funcionamiento de la aplicación web. Ejecutamos las pruebas y contrastamos las métricas del informe con los resultados guardados en la carpeta `evidencia/`. También verificamos que las instrucciones y la documentación coincidieran con el funcionamiento real del proyecto.

**Decisiones del equipo:** Definimos que la demostración debía ser ejecutable y permitir observar directamente cómo se realizan las predicciones, por lo que optamos por desarrollar una aplicación web local y mantener el notebook como respaldo. También solicitamos comprobar que la retención utilizada como objetivo estuviera respaldada por los datos. Establecimos probar distintos escenarios, incluidas entradas incorrectas y casos límite, para identificar y corregir posibles fallas. Finalmente, definimos adaptar el diseño de la aplicación para la presentación y organizar el repositorio con instrucciones que permitieran ejecutar el proyecto en los computadores de la universidad.