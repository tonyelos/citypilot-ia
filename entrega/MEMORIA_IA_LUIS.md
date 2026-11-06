# Memoria individual de utilización de IA — CityPilot IA

## 1. Autoría y aportación individual

- **Estudiante:** Luis Wesinger (Est.3)
- **Equipo:** Yiao TANG (Est.1), Marc (Est.2), Luis Wesinger (Est.3)
- **Repositorio GitHub:** https://github.com/tonyelos/citypilot-ia
- **Mis dos PR:**
  - PR #2: Implementación de puntos de interés con Overpass API / OpenStreetMap (`feature/est3-overpass-poi`).
  - PR #4: Persistencia y analítica en PostgreSQL (`db.py`, `analytics.py`, `/analitica`, dashboard).
- **Archivos y funciones de mi responsabilidad (revisados y adaptados por mí):**
  - `web/app/api_clients.py`: `obtener_lugares()`, `CATEGORIAS_OVERPASS`, normalización geométrica (node vs way/relation), deduplicación y fallback resiliente a fixture con `demo=True`.
  - `web/app/db.py`: `guardar_solicitud()`, `obtener_estadisticas()`, `obtener_ultimas_solicitudes()`.
  - `web/app/analytics.py`: `generar_grafico_ciudades()` con Matplotlib y exportación a buffer PNG.
  - `web/app/main.py`: rutas `/analitica`, `/analitica/grafico.png`, `/api/estadisticas`.
  - `web/app/templates/analitica.html`: panel de métricas, gráfico y tabla de últimas solicitudes sin secretos.
  - `web/tests/test_lugares.py` y `web/tests/test_analitica_db.py`: suites de pruebas unitarias.
- **Pruebas ejecutadas personalmente:**
  - `docker compose exec web python -m pytest -v` → **15 passed** (A1, A2 y Analítica/DB al 100% en verde).
  - Comprobación visual y de endpoints en `http://localhost:5000/analitica` y `http://localhost:5000/analitica/grafico.png`.

## 2. Herramientas y fuentes usadas

| Herramienta o fuente | Modelo/versión, si se conoce | Finalidad | ¿Se incorporó código o texto? |
|---|---|---|---|
| Google Gemini | Gemini (Web) | Traducción, comprensión de requisitos, diseño de consultas Overpass QL, lógica de normalización y estrategia de tests | Sí; código revisado, adaptado y corregido en `api_clients.py` y `test_lugares.py` |
| Documentación OpenStreetMap Overpass API | — | Sintaxis de Overpass QL (`around`, `out center`, `nwr`) | Consulta técnica |
| `docs/APIS_Y_CONTRATOS.md` | — | Especificación de los contratos de datos y categorías | Referencia obligatoria |

## 3. Registro cronológico de uso relevante de IA y recursos externos

### Interacción 1 — Comprensión y traducción del enunciado y requisitos de la práctica (2026-11-06)

- **Qué intentaba resolver:** Comprender detalladamente el alcance del taller CityPilot IA, los requisitos del semáforo amarillo y las tareas específicas asignadas a Estudiante 3 (PR2 y PR4), cuyo enunciado original estaba en español.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: Solicitud de traducción y síntesis al alemán de la guía del taller, roles del equipo y requerimientos técnicos específicos para la integración de Overpass API.
- **Qué propuso o respondió:** Resumen estructurado explicando el rol de Estudiante 3, la prohibición de inyección libre de texto en Overpass QL, la necesidad de normalizar centros de ways/relations junto a nodos, y la política de fallback con datos demo en caso de caída del servidor comunitario.
- **Qué hice yo con ello:** Asimilé los requisitos técnicos para planificar la implementación sin desvíos respecto al contrato; verifiqué la correspondencia con `docs/APIS_Y_CONTRATOS.md`.
- **Resultado y verificación:** Claridad completa sobre las 4 categorías permitidas, el radio de 2500m y la limitación estricta de una sola petición con timeout (20-25s).
- **Evidencia:** Registro de tareas y rama `feature/est3-overpass-poi`.

### Interacción 2 — Consulta de sintaxis y diseño de consultas Overpass QL (2026-11-06)

- **Qué intentaba resolver:** Determinar cómo formular las consultas en Overpass QL para obtener puntos de interés de categorías específicas (cultural, gastronómica, naturaleza, familiar) alrededor de unas coordenadas sin permitir inyección de parámetros arbitrarios por parte del usuario.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: *"I have to implement a function obtener_lugares(lat, lon, tip). It looks for POIs via Overpass API. How do I build Overpass-QL requests?"*
- **Qué propuso o respondió:** Sugirió la estructura de filtros `nwr` con expresiones regulares para las etiquetas de OpenStreetMap (`tourism`, `amenity`, `leisure`, `historic`), el uso de `(around:2500,lat,lon)` y `out center 12;` para obtener los centros geométricos de elementos poligonales (ways/relations).
- **Qué hice yo con ello:** Descarté concatenar texto arbitrario del usuario; en su lugar, implementé un diccionario estático `CATEGORIAS_OVERPASS` que mapea estrictamente los cuatro tipos válidos. Añadí validación estricta del parámetro `tipo` y extracción de coordenadas tanto de `lat`/`lon` (nodos) como de `center` (ways).
- **Resultado y verificación:** Consulta parametrizada segura y determinista, verificada en `test_obtener_lugares_normaliza_nodos_y_ways`.
- **Evidencia:** `web/app/api_clients.py` (líneas de `CATEGORIAS_OVERPASS` y `obtener_lugares`).

### Interacción 3 — Normalización de nodos, ways y deduplicación de lugares (2026-11-06)

- **Qué intentaba resolver:** Overpass devuelve elementos heterogéneos: los nodos tienen `lat`/`lon` directos, mientras que las vías (ways) y relaciones tienen `center.lat`/`center.lon`. Además, muchos elementos carecen de nombre (`tags.name`) o aparecen repetidos con diferentes geometrías.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: *"Overpass returns nodes with lat/lon and ways/relations with center.lat/center.lon. Some elements don't have a name tag. How do I parse and normalize this in Python so that I get a list of max 12 unique places without duplicates?"*
- **Qué propuso o respondió:** Un bucle de extracción que descarta elementos sin clave `name`, extrae la posición según el tipo (`node` vs `way`/`relation`), utiliza un `set()` de nombres en minúsculas para deduplicar y corta la lista al alcanzar el límite máximo.
- **Qué hice yo con ello:** Adopté la estructura, pero reforcé la validación de tipos numéricos y rangos de latitud/longitud (-90 a 90 y -180 a 180) para evitar que datos corruptos de OSM rompieran la aplicación. Añadí una función auxiliar `_extraer_categoria` para asignar la etiqueta semántica adecuada (`museum`, `park`, etc.) en lugar de un tipo genérico.
- **Resultado y verificación:** Normalización limpia verificada en `test_obtener_lugares_normaliza_nodos_y_ways`, comprobando que un nodo sin nombre y un duplicado son ignorados correctamente.
- **Evidencia:** `web/app/api_clients.py` (`obtener_lugares`), `web/tests/test_lugares.py`.

### Interacción 4 — Resiliencia y fallback con datos demo ante fallos del servidor (2026-11-06)

- **Qué intentaba resolver:** El servidor comunitario de Overpass (`overpass-api.de`) sufre sobrecarga recurrente, devolviendo errores 406 (si falta User-Agent), 429 (Rate Limit) o 504 Gateway Timeout. La aplicación no debe fallar ni inventar datos, sino degradar graciosamente usando el fixture proporcionado.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: *"The Overpass API server is often slow or returns 504 Gateway Timeout or 429 Too Many Requests. How should I handle exceptions in requests.post to load a local demo fixture as a fallback instead of crashing?"*
- **Qué propuso o respondió:** Envolver la llamada `requests.post` en un bloque `try-except` que capture `requests.RequestException` y retorne la lista cargada de `fixtures/puntos_demo.json`.
- **Qué hice yo con ello:** Implementé el bloque de captura, pero exigí que todos los elementos devueltos por el fixture tengan explícitamente `demo = True`. Además, añadí la cabecera `User-Agent` obligatoria para evitar el bloqueo 406 de nginx y aseguré que si la lista filtrada queda vacía también se use el fixture con la marca demo.
- **Resultado y verificación:** Test unitario `test_obtener_lugares_fallback_fixture_en_error` simula un Timeout y confirma que se devuelven lugares de demo con `demo: True`.
- **Evidencia:** `web/app/api_clients.py`, `web/tests/test_lugares.py`.

### Interacción 5 — Diseño de tests unitarios con mocks HTTP (2026-11-06)

- **Qué intentaba resolver:** Diseñar pruebas automatizadas para A2 que no dependan de conexión a Internet ni realicen llamadas reales a Overpass durante la integración continua.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: *"How do I write pytest unit tests with monkeypatch for this function to test both normal parsing of nodes/ways and the fallback behavior without making real HTTP requests?"*
- **Qué propuso o respondió:** Uso de una clase `RespuestaFalsa` y `monkeypatch.setattr(requests, "post", ...)` simulando un payload JSON con nodos y vías.
- **Qué hice yo con ello:** Adapté la estructura al estilo del proyecto (similar a `test_geo_clima.py` de Yiao) y añadí comprobaciones adicionales: verificación de que no se inyecta código malicioso en la cadena QL y prueba de rechazo de tipos no permitidos (`test_obtener_lugares_rechaza_tipo_invalido`).
- **Resultado y verificación:** Ejecución exitosa con `docker compose exec web python -m pytest -q` (12 passed).
- **Evidencia:** `web/tests/test_lugares.py`.

### Interacción 6 — Persistencia parametrizada en PostgreSQL y manejo de columnas JSONB (2026-11-06)

- **Qué intentaba resolver:** Implementar `guardar_solicitud()` con SQLAlchemy y PostgreSQL garantizando que los datos complejos (meteorología y lugares) se guarden como columnas `jsonb`, que nunca se concatenen cadenas SQL sin parametrizar y que la función devuelva el `id` autogenerado.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: *"I need to implement guardar_solicitud(registro: dict) gpoing to int in sqlAlchemy Postgresql for my Flask project. The table is called solicitudes with columns: ciudad, pais, tipo_turismo, duracion_horas, preferencias, latitud, longitud meteorologia (jsonB), lugares (jsonB), prompt_usado, itinerario, estado, duracion_ms, error_resumido, modo_demo, modo_modelo. how do I write a safe parameterized INSERT returning the new id, ensuring dicts or lists are properly dumped to jsonB?"*
- **Qué propuso o respondió:** Uso de `with engine.begin() as conn:`, sentencia `text(...)` con cláusula `RETURNING id;`, uso de `json.dumps()` para los campos JSON y casteo explícito con `CAST(:param AS jsonb)` en la consulta.
- **Qué hice yo con ello:** Adopté el patrón de casteo `CAST(:param AS jsonb)` y la ejecución transaccional con `scalar_one()`. Añadí validación defensiva para que si algún campo opcional viene vacío no lance excepciones de tipo y se respete la integridad del esquema SQL de `db/init.sql`.
- **Resultado y verificación:** Verificado con prueba unitaria en `test_analitica_db.py::test_guardar_solicitud_y_obtener_estadisticas`, comprobando que se inserta y devuelve el ID entero.
- **Evidencia:** `web/app/db.py` (`guardar_solicitud`), `web/tests/test_analitica_db.py`.

### Interacción 7 — Consultas de agregación SQL y generación de gráficos en memoria (2026-11-06)

- **Qué intentaba resolver:** Obtener métricas agregadas (`COUNT(*)`, `COUNT(DISTINCT)`, `GROUP BY` por ciudad y por tipo de turismo) y generar una imagen PNG con Matplotlib para el dashboard sin usar JavaScript ni guardar archivos en disco.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: Consulta sobre consultas de agregación en PostgreSQL con SQLAlchemy `mappings().all()` y generación de gráficos con `io.BytesIO` usando el backend `Agg` de Matplotlib.
- **Qué propuso o respondió:** Utilizar consultas SQL nativas agrupadas, configurar `matplotlib.use("Agg")`, construir un gráfico de barras horizontales y volcarlo a un buffer `io.BytesIO` retornado con `send_file`.
- **Qué hice yo con ello:** Implementé `obtener_estadisticas()` y `obtener_ultimas_solicitudes(limite=8)` asegurando que nunca se expongan secretos ni prompts en la vista pública. Creé `web/app/analytics.py` con formateo estético de barras y etiquetas de conteo. Conecté las rutas `/analitica`, `/analitica/grafico.png` y `/api/estadisticas` en `main.py` y completé la plantilla `analitica.html`.
- **Resultado y verificación:** Suite de 15 pruebas en verde (`pytest -v`), verificación de la cabecera mágica de archivo PNG (`\x89PNG`) en los tests de respuesta HTTP.
- **Evidencia:** `web/app/db.py`, `web/app/analytics.py`, `web/app/main.py`, `web/app/templates/analitica.html`, `web/tests/test_analitica_db.py`.

### Interacción 8 — Análisis de los comentarios de revisión del PR #4 (2026-11-06)

- **Qué intentaba resolver:** Mi compañero solicitó cambios en PR #4 (*Request Changes*) señalando cuatro problemas: conflicto de rebase en `main.py` con PR #2, fuga técnica de `detalle=str(exc)` en `/api/estadisticas`, falta de aislamiento/limpieza en el test de base de datos, y un valor por defecto inválido (3h) en `duracion_horas`. Quería entender el impacto técnico de cada observación antes de tocar el código.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: *"My peer requested changes on my PR: 1) rebase conflict in main.py keeping PR #2's /planificar, 2) don't return detalle=str(exc) in /api/estadisticas, 3) isolate the DB test with unique fixtures and cleanup, 4) duracion_horas default 3 is invalid (only 2, 4, 6 allowed). Can you explain what needs to be fixed and why each of these is a problem?"*
- **Qué propuso o respondió:** Explicó que filtrar excepciones en APIs públicas expone detalles internos del esquema o de la infraestructura; que un test que asume ser la última fila en una base de datos compartida falla en concurrencia si no se limpia; y que aceptar duraciones fuera de las opciones del formulario (2, 4, 6) viola la coherencia del negocio.
- **Qué hice yo con ello:** Validé las razones técnicas del revisor; decidí hacer el rebase interactivo conservando la ruta `/planificar` y preparar la refactorización de `db.py` y del test.
- **Resultado y verificación:** Plan de acción claro para corregir los 4 puntos sin romper los contratos existentes.
- **Evidencia:** Comentarios de revisión en PR #4 en GitHub.

### Interacción 9 — Implementación de las correcciones del review y limpieza de tests (2026-11-06)

- **Qué intentaba resolver:** Obtener patrones concretos de implementación para: 1) validar estrictamente `duracion_horas in (2, 4, 6)` como campo obligatorio, 2) registrar el error en el logger sin exponerlo al usuario, y 3) estructurar un test en Pytest con UUID único y bloque `finally` para el borrado SQL.
- **Herramienta/fuente y prompt o instrucción:** Google Gemini Web. Prompt: *"How do I implement strict validation for duracion_horas in (2, 4, 6) in db.py, log the exception safely in Flask without exposing str(exc), and write an isolated pytest test that creates a unique row and cleans it up with a DELETE in a finally block?"*
- **Qué propuso o respondió:** Código para comprobar `duracion_horas` con `ValueError`, sustitución en el endpoint de Flask por `app.logger.exception(...)` con mensaje genérico de error 500, y un test con `uuid.uuid4().hex` con `try...finally` ejecutando `DELETE FROM solicitudes WHERE id = :id`.
- **Qué hice yo con ello:** Integré los fragmentos en `db.py`, `main.py` y `web/tests/test_analitica_db.py`; añadí además un test específico para verificar que duraciones distintas de 2, 4 o 6 son rechazadas de inmediato.
- **Resultado y verificación:** `docker compose exec web python -m pytest -v` pasando 22 de 22 pruebas (100% de la aplicación integrada).
- **Evidencia:** Commits en `feature/est3-db-analitica`, push con `--force-with-lease`.

## 4. Evolución del prompt de itinerarios (si utilicé el LLM)

No aplica a PR #2: el diseño del prompt de itinerarios en Cohere corresponde a Est.2 (Marc) en `web/app/llm.py`.

## 5. Código o materiales externos incorporados

| Archivo/líneas aproximadas | Origen | ¿Copiado o adaptado? | ¿Qué cambio/validación hice? |
|---|---|---|---|
| `docs/APIS_Y_CONTRATOS.md` | Material del taller | Referencia | Especificación de categorías para Overpass |
| `fixtures/puntos_demo.json` | Fixture del proyecto | Reutilizado | Carga en caso de fallo/timeout de Overpass con `demo=True` |
| `web/app/api_clients.py` | Asistencia Gemini + autoría propia | Adaptado | Creación de QL estático, filtro geométrico, cabecera User-Agent y manejo seguro de errores |
| `web/tests/test_lugares.py` | Asistencia Gemini + autoría propia | Adaptado | Test con monkeypatch para node, way, demo fixture y validación de tipos |

## 6. Balance personal

- **Dos decisiones técnicas que tomé yo:**
  1. Uso de consultas estáticas en `CATEGORIAS_OVERPASS` con validación previa estricta en lugar de permitir que la entrada del usuario se interpole libremente en Overpass QL (prevención de inyección).
  2. Implementación de una cabecera `User-Agent` descriptiva para cumplir la política de uso de OSM y evitar rechazos inmediatos HTTP 406.
- **Un error o solución que descarté:** Descarté realizar reintentos continuos en caso de 504 o 429; al ser un servicio público y comunitario saturado, se ejecuta un único intento con timeout de 25s y se pasa a datos de prueba `demo=True` para garantizar que la app siga respondiendo.
- **Qué código puedo explicar y demostrar:** `obtener_lugares()`, la extracción de centros en polígonos vs nodos, y la suite en `test_lugares.py`.
- **Qué sigue pendiente o limitado:** PR #4 (persistencia en PostgreSQL de las consultas y generación del dashboard de analítica).

**Declaración:** Confirmo que esta memoria describe fielmente las fuentes, la asistencia recibida, los cambios que introduje y mi aportación personal. — Luis Wesinger, 2026-11-06
