# Memoria individual de utilización de IA — CityPilot IA

## 1. Autoría y aportación individual

- **Estudiante:** Yiao TANG (Est.1)
- **Equipo:** Yiao TANG (Est.1), Marc (Est.2), Luis Wesinger (Est.3)
- **Repositorio GitHub:** https://github.com/tonyelos/citypilot-ia
- **Mis dos PR:** PR #1 (A1: geocodificación + meteorología) y mi segundo PR (web/orquestación, pendiente de abrir)
- **Archivos y funciones de mi responsabilidad (revisados y adaptados por mí):**
  - `web/app/api_clients.py`: `geocodificar()` y `obtener_meteorologia()` (borrador inicial asistido por IA, revisado por mí) y validación del rango WMO (`0 <= weather_code <= 99`) añadida por mí.
  - `web/tests/test_geo_clima.py`: pruebas de normalización, resultados vacíos, timeout, bloque `current`, campos ausentes y código WMO fuera de rango.
- **Pruebas ejecutadas personalmente:**
  - `docker compose exec web python -m pytest -q` → **9 passed**.
  - Llamada real a Open-Meteo: Valencia → lat `39.47391`, lon `-0.37966`; temperatura `12.5 °C`, precipitación `0.0 mm`, código `1`, instante `2026-11-06T09:15`.

## 2. Herramientas y fuentes usadas

| Herramienta o fuente | Modelo/versión, si se conoce | Finalidad | ¿Se incorporó código o texto? |
|---|---|---|---|
| DeepSeek Chat | No indicado por la interfaz | Explicar el esqueleto de `api_clients.py` y los casos límite de A1 | No; solo explicación |
| Asistencia de IA generativa | No indicada | Primer borrador de las funciones y de varios tests | Sí, revisado y adaptado en `api_clients.py` y `test_geo_clima.py` |
| Documentación Open-Meteo y `docs/APIS_Y_CONTRATOS.md` | — | URLs, parámetros y estructura de respuesta | No; consulta |

- Otras fuentes: `docs/TAREAS_Y_CRITERIOS.md`, `docs/COMPROBACIONES.md`, ejemplos de la asignatura.

## 3. Registro cronológico de uso relevante de IA y recursos externos

### Interacción 1 — Entender `api_clients.py` antes de implementar A1 (2026-11-06)

- **Qué intentaba resolver:** no tenía claro qué hacía el esqueleto ni qué casos límite exigía A1.
- **Herramienta/fuente y prompt o instrucción:** DeepSeek Chat; pedí una explicación en chino del módulo y de los casos timeout, HTTP, `results` vacío y bloque `current`.
- **Qué propuso o respondió:** que `api_clients.py` es una capa adaptadora; usar `params`, `timeout`, `raise_for_status()`; no rellenar campos ausentes con `0`; acordar con el orquestador la política de “sin resultados”.
- **Qué hice yo con ello:** contrasté la respuesta con `docs/APIS_Y_CONTRATOS.md`; acepté el uso de `params`/`timeout`/`raise_for_status` y la normalización; decidí que “sin resultados” lanzara `ValueError` y que un `current` incompleto lanzara un error controlado.
- **Resultado y verificación:** implementación posterior y pruebas con HTTP simulado.
- **Evidencia:** `entrega/evidencias/deepseek_A1_api_clients.md`; PR #1.

### Interacción 2 — Borrador inicial de implementación y tests (2026-11-06)

- **Qué intentaba resolver:** pasar de los contratos a una primera versión funcional de `geocodificar` y `obtener_meteorologia`.
- **Herramienta/fuente y prompt:** asistencia de IA generativa a partir de los contratos y del esqueleto.
- **Qué propuso:** una implementación con `requests.get(..., params=..., timeout=...)`, normalización a los cuatro campos y tests con `monkeypatch`.
- **Qué hice yo:** revisé el borrador; añadí la validación del código WMO (`0–99`) y su test `test_meteorologia_rechaza_codigo_wmo_fuera_de_rango`; ejecuté `pytest` (9 passed) y la llamada real a Open-Meteo; comprobé que una ciudad inexistente devuelve `ValueError` sin traceback.
- **Resultado y verificación:** 9 pruebas en verde y respuesta real coherente con el contrato.
- **Evidencia:** commits `b469455`, `78530f2` y `cc4f852`; PR #1; salida de terminal.

## 4. Evolución del prompt de itinerarios (si utilicé el LLM)

No aplica a A1: el prompt de itinerarios es responsabilidad de Est.2 (Marc) en `web/app/llm.py`. En mi segundo PR integraré la llamada al orquestador, pero no diseñaré el prompt. Si finalmente ajusto algún texto para la integración, lo documentaré aquí.

## 5. Código o materiales externos incorporados

| Archivo/líneas aproximadas | Origen | ¿Copiado o adaptado? | ¿Qué cambio/validación hice? |
|---|---|---|---|
| `web/app/api_clients.py` (`geocodificar`, `obtener_meteorologia`) | Borrador asistido por IA + documentación Open-Meteo | Adaptado | Revisión del contrato, validación WMO añadida, pruebas con mock |
| `web/tests/test_geo_clima.py` | Borrador asistido por IA | Adaptado | Añadí el test de WMO y ejecuté toda la suite |
| `docs/APIS_Y_CONTRATOS.md` | Material del profesor | No copiado | Usado como contrato de referencia |

## 6. Balance personal

- **Dos decisiones técnicas que tomé yo:**
  1. Limitar la geocodificación a España (`countryCode=ES`) y tratar “sin resultados” como `ValueError` controlado.
  2. No convertir campos ausentes de meteorología en `0`; un `0` es un dato real y ocultaría un fallo.
- **Un error o solución que descarté:** descarté rellenar valores por defecto y reintentos automáticos; preferí un error claro y un solo intento con timeout.
- **Qué código puedo explicar y demostrar:** `geocodificar`, `obtener_meteorologia`, el helper `_obtener_json` y los tests de `test_geo_clima.py`.
- **Qué sigue pendiente o limitado:** PR #5 (orquestador + formulario + resultado) y la integración final con Overpass, Cohere y PostgreSQL.

**Declaración:** Confirmo que esta memoria describe fielmente las fuentes, la asistencia recibida, los cambios que introduje y mi aportación personal. — Yiao TANG, 2026-11-06
