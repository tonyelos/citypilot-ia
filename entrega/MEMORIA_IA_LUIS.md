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
  - `web/tests/test_lugares.py`: suite de pruebas unitarias cubriendo normalización de nodos y ways, descarte de elementos sin nombre, deduplicación, validación de categorías y fallback ante 504/timeout.
- **Pruebas ejecutadas personalmente:**
  - `docker compose exec web python -m pytest -q` → **12 passed** (9 de A1 + 3 de A2 en `test_lugares.py`).
  - Comprobación de comportamiento real frente a caídas/latencia del servidor público `overpass-api.de`: activación correcta del fixture DEMO (`demo=True`).

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
