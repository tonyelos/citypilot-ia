# Memoria individual de utilización de IA — CityPilot IA

## 1. Autoría y aportación individual

- **Estudiante:** Yiao TANG (Est.1)
- **Equipo:** Yiao TANG (Est.1), Marc (Est.2), Luis Wesinger (Est.3)
- **Repositorio GitHub:** https://github.com/tonyelos/citypilot-ia
- **Mis dos PR:**
  - **PR #1** — A1: geocodificación + meteorología (`feature/est1-geo-clima`), fusionado.
  - **PR #2** — Web/orquestador: formulario, resultado y orquestador compartido (`feature/est1-web-orquestacion`), fusionado.
- **Archivos y funciones de mi responsabilidad:**
  - `web/app/api_clients.py`: `geocodificar()` y `obtener_meteorologia()` (borrador inicial asistido por IA, revisado por mí) y validación del rango WMO (`0 <= weather_code <= 99`) añadida por mí.
  - `web/app/orchestrator.py`: `procesar_solicitud()` y validación de entrada.
  - `web/app/main.py`: ruta `POST /planificar` y manejo 400/502.
  - `web/app/templates/index.html` y `resultado.html`: formulario, resultados y aviso DEMO.
  - `web/tests/test_geo_clima.py`, `test_orchestrator.py` y `test_web_planificar.py`.
- **Pruebas ejecutadas:**
  - A1: `docker compose exec web python -m pytest -q` → **9 passed**.
  - PR #2: **15 passed** en el momento del merge.
  - Integración actual (con PR #4): **22 passed**.
  - Llamada real a Open-Meteo: Valencia → lat `39.47391`, lon `-0.37966`; temperatura `12.5 °C`, precipitación `0.0 mm`, código `1`, instante `2026-11-06T09:15`.

## 2. Herramientas y fuentes usadas

| Herramienta o fuente | Modelo/versión, si se conoce | Finalidad | ¿Se incorporó código o texto? |
|---|---|---|---|
| DeepSeek Chat | No indicado por la interfaz | Explicar el esqueleto de `api_clients.py` y los casos límite de A1 | No; solo explicación |
| Asistencia de IA generativa | No indicada | Borrador de funciones, tests, orquestador y HTML | Sí, revisado y adaptado en `api_clients.py`, `orchestrator.py`, `main.py`, `index.html`, `resultado.html` y tests |
| Guía docente **Module 0 — TALLER INTEGRADO** (`TALLER INTEGRADO/taller_bigdata_alumnado/GUIA.md`) | — | Referencia para `render_template`, Jinja, formularios GET/POST, `url_for`, bucles y `selected` | Sí; estructura adaptada, no copiada literalmente |
| Documentación Open-Meteo y `docs/APIS_Y_CONTRATOS.md` | — | URLs, parámetros y estructura de respuesta | No; consulta |
| `base.html` | Material del profesor | Plantilla base del sitio | No; se usó tal cual |

- Otras fuentes: `docs/TAREAS_Y_CRITERIOS.md`, `docs/COMPROBACIONES.md`, ejemplos de la asignatura.

## 3. Registro cronológico de uso relevante de IA y recursos externos

### Interacción 1 — Entender `api_clients.py` antes de implementar A1 (2026-11-06)

- **Qué intentaba resolver:** no tenía claro qué hacía el esqueleto ni qué casos límite exigía A1.
- **Herramienta/fuente y prompt o instrucción:** DeepSeek Chat; pedí una explicación en chino del módulo y de los casos timeout, HTTP, `results` vacío y bloque `current`.
- **Qué propuso o respondió:** que `api_clients.py` es una capa adaptadora; usar `params`, `timeout`, `raise_for_status()`; no rellenar campos ausentes con `0`; acordar con el orquestador la política de “sin resultados”.
- **Qué hice yo con ello:** contrasté la respuesta con `docs/APIS_Y_CONTRATOS.md`; acepté el uso de `params`/`timeout`/`raise_for_status` y la normalización; decidí que “sin resultados” lanzara `ValueError` y que un `current` incompleto lanzara un error controlado.
- **Resultado y verificación:** implementación posterior y pruebas con HTTP simulado.
- **Evidencia:** `entrega/evidencias/deepseek_A1_api_clients.md`; PR #1.

### Interacción 2 — Borrador inicial de implementación y tests de A1 (2026-11-06)

- **Qué intentaba resolver:** pasar de los contratos a una primera versión funcional de `geocodificar` y `obtener_meteorologia`.
- **Herramienta/fuente y prompt:** asistencia de IA generativa a partir de los contratos y del esqueleto.
- **Qué propuso:** una implementación con `requests.get(..., params=..., timeout=...)`, normalización a los cuatro campos y tests con `monkeypatch`.
- **Qué hice yo:** revisé el borrador; añadí la validación del código WMO (`0–99`) y su test `test_meteorologia_rechaza_codigo_wmo_fuera_de_rango`; ejecuté `pytest` (9 passed) y la llamada real a Open-Meteo; comprobé que una ciudad inexistente devuelve `ValueError` sin traceback.
- **Resultado y verificación:** 9 pruebas en verde y respuesta real coherente con el contrato.
- **Evidencia:** commits `b469455`, `78530f2` y `cc4f852`; PR #1; salida de terminal.

### Interacción 3 — Orquestador, formulario y página de resultado (PR #2, 2026-11-06)

- **Qué intentaba resolver:** construir el flujo web completo (formulario → orquestador → resultado) sin duplicar la lógica entre HTML y JSON.
- **Herramientas/fuentes y prompts:**
  - Guía docente Module 0, secciones 1, 2 y 3.3: `render_template`, Jinja, formulario GET/POST, `request.form`, `url_for`, bucles para `<option>`, `selected` y conservación de valores.
  - Asistencia de IA generativa para el borrador de `orchestrator.py`, la ruta `/planificar` y los dos HTML.
  - DeepSeek Chat para revisar el diseño del orquestador y el manejo de errores/fallback DEMO.
- **Qué propuso la IA:** un orquestador único con validación previa, llamada a geocodificación, meteorología, Overpass, LLM y base de datos; formulario con Jinja y página de resultado con aviso DEMO.
- **Qué hice yo con ello:**
  - Adapté la estructura HTML a la guía del Titanic: `action="{{ url_for('planificar_html') }}"`, bucles Jinja para tipo/duración, `selected` y `value` para conservar la entrada tras un error.
  - Añadí el manejo 400 (validación) / 502 (proveedor) y el aviso visible de `modo_demo`.
  - Ajusté la validación de preferencias y el fallback de Overpass para no ocultar errores de programación.
  - Ejecuté la suite y comprobé el renderizado con el cliente de pruebas de Flask.
- **Resultado y verificación:** PR #2 fusionado con **15 passed**; integración posterior con PR #4: **22 passed**.
- **Evidencia:** PR #2 (commits `c9c7e1b`, `e568e04`, `5beb0ad`, `1f1e620`, `b1f9582`, `7591d63`), `entrega/evidencias/deepseek_PR5_orquestador.md` y captura del flujo.

> **Nota sobre los HTML:** `index.html` y `resultado.html` se generaron con asistencia de IA tomando como referencia la guía docente Module 0; después se adaptaron al contrato de CityPilot. No son copia literal de la guía ni código escrito íntegramente a mano. `base.html` es material del profesor y `analitica.html` corresponde a Est.3 (Luis), documentado en su propia memoria.

## 4. Evolución del prompt de itinerarios (si utilicé el LLM)

No aplica a mis PRs: el prompt de itinerarios es responsabilidad de Est.2 (Marc) en `web/app/llm.py`. En el orquestador solo integro la llamada; no diseño el prompt. Si en la integración final ajusto algún texto, lo documentaré aquí.

## 5. Código o materiales externos incorporados

| Archivo/líneas aproximadas | Origen | ¿Copiado o adaptado? | ¿Qué cambio/validación hice? |
|---|---|---|---|
| `TALLER INTEGRADO/taller_bigdata_alumnado/GUIA.md` §1, §2, §3.3 | Material del profesor (Module 0) | Base estructural adaptada | Formulario, `url_for`, bucles, `selected`, conservación de valores |
| `web/app/templates/index.html`, `resultado.html` | Guía Module 0 + borrador asistido por IA | Adaptado | Ajuste al contrato, aviso DEMO, enlaces OSM, errores |
| `web/app/orchestrator.py` | Borrador asistido por IA + contratos | Adaptado | Validación, orden de llamadas, fallback, retorno único |
| `web/app/api_clients.py` (`geocodificar`, `obtener_meteorologia`) | Borrador asistido por IA + documentación Open-Meteo | Adaptado | Revisión del contrato, validación WMO añadida, pruebas con mock |
| `web/tests/test_geo_clima.py` | Borrador asistido por IA | Adaptado | Añadí el test de WMO y ejecuté toda la suite |
| `docs/APIS_Y_CONTRATOS.md` | Material del profesor | No copiado | Usado como contrato de referencia |

## 6. Balance personal

- **Decisiones técnicas que tomé yo:**
  1. Limitar la geocodificación a España (`countryCode=ES`) y tratar “sin resultados” como `ValueError` controlado.
  2. No convertir campos ausentes de meteorología en `0`; un `0` es un dato real y ocultaría un fallo.
  3. Usar un único `procesar_solicitud()` para HTML y JSON, y mapear `ValueError` a 400 y fallos de proveedor a 502.
- **Un error o solución que descarté:** descarté rellenar valores por defecto, reintentos automáticos y el `action` hardcodeado del formulario; preferí errores claros, timeout y `url_for`.
- **Qué código puedo explicar y demostrar:** `geocodificar`, `obtener_meteorologia`, `_obtener_json`, `procesar_solicitud`, la ruta `/planificar` y los HTML de formulario/resultado.
- **Qué sigue pendiente o limitado:** integración final con Cohere y PostgreSQL de los PR de Marc/Luis, y revisión de la memoria antes de la entrega.

**Declaración:** Confirmo que esta memoria describe fielmente las fuentes, la asistencia recibida, los cambios que introduje y mi aportación personal. — Yiao TANG, 2026-11-06
