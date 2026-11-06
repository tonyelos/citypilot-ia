# Consulta IA — PR5 CityPilot IA (orquestador web)

- **Fecha:** 2026-11-06T08:38:27.195Z
- **Herramienta:** DeepSeek Chat
- **URL:** https://chat.deepseek.com/a/chat/s/117ade63-5d17-4efb-9fd6-053c483c2a20
- **Uso:** revisar el diseño del orquestador compartido y los riesgos de manejo de errores/fallback demo.

## Prompt

```text
我在做 CityPilot IA（Flask + PostgreSQL + APIs públicas + Cohere）。下面是我写的 orchestrator.py 草稿：它把 HTML 表单和 JSON API 的请求串起来（验证 → 地理编码 → 天气 → Overpass → LLM → DB）。请用通俗中文解释整体流程，并指出：
1) 异常分层是否合理（ValueError → 400，供应商错误 → 502）；
2) 返回的 dict 是否足够 HTML 和 JSON 共用；
3) Overpass 失败时用 fixture 并标记 demo 的风险；
4) 测试应该覆盖哪些点。
不要给完整重写代码，只给思路和风险提示，最后 5 行总结。

```python
"""Punto ÚNICO de integración para web y API JSON. Pendiente del alumnado."""
import time

from app import api_clients, db, llm

TIPOS_VALIDOS = {"cultural", "gastronomica", "naturaleza", "familiar"}
DURACIONES_VALIDAS = {2, 4, 6}
MAX_CIUDAD = 80
MAX_PREFERENCIAS = 200


def _validar_entrada(ciudad, tipo_turismo, duracion_horas, preferencias):
    """Normaliza y valida antes de consumir ningún servicio externo."""
    if not isinstance(ciudad, str) or not ciudad.strip():
        raise ValueError("La ciudad es obligatoria.")
    ciudad = ciudad.strip()
    if len(ciudad) > MAX_CIUDAD:
        raise ValueError(f"La ciudad no puede superar los {MAX_CIUDAD} caracteres.")

    if tipo_turismo not in TIPOS_VALIDOS:
        raise ValueError(
            "El tipo de turismo debe ser cultural, gastronomica, naturaleza o familiar."
        )

    try:
        duracion = int(duracion_horas)
    except (TypeError, ValueError) as exc:
        raise ValueError("La duración debe ser un número entero.") from exc
    if duracion not in DURACIONES_VALIDAS:
        raise ValueError("La duración debe ser 2, 4 o 6 horas.")

    preferencias = (preferencias or "").strip()
    if len(preferencias) > MAX_PREFERENCIAS:
        raise ValueError(
            f"Las preferencias no pueden superar los {MAX_PREFERENCIAS} caracteres."
        )

    return ciudad, tipo_turismo, duracion, preferencias


def procesar_solicitud(ciudad: str, tipo_turismo: str, duracion_horas: int, preferencias: str = "") -> dict:
    """Valida, consulta datos, pide el itinerario, guarda y devuelve el contrato.

    El HTML y la API JSON deben llamar SIEMPRE a esta función: así no se
    duplican reglas ni llamadas a proveedores.
    """
    inicio = time.perf_counter()
    ciudad, tipo_turismo, duracion, preferencias = _validar_entrada(
        ciudad, tipo_turismo, duracion_horas, preferencias
    )

    geocodificacion = api_clients.geocodificar(ciudad)
    meteorologia = api_clients.obtener_meteorologia(
        geocodificacion["lat"], geocodificacion["lon"]
    )

    modo_demo = False
    try:
        lugares = api_clients.obtener_lugares(
            geocodificacion["lat"], geocodificacion["lon"], tipo_turismo
        )
        if not lugares:
            lugares = []
    except Exception:
        # Fallback explícito para demostrar el flujo si Overpass no responde.
        lugares = api_clients.cargar_fixture_lugares()
        modo_demo = True

    contexto = {
        "ciudad": geocodificacion["ciudad"],
        "pais": geocodificacion["pais"],
        "tipo_turismo": tipo_turismo,
        "duracion_horas": duracion,
        "preferencias": preferencias,
        "meteorologia": meteorologia,
        "lugares": lugares,
    }
    itinerario, prompt_usado = llm.generar_itinerario(contexto)

    duracion_ms = int((time.perf_counter() - inicio) * 1000)
    registro = {
        "ciudad": geocodificacion["ciudad"],
        "pais": geocodificacion["pais"],
        "tipo_turismo": tipo_turismo,
        "duracion_horas": duracion,
        "preferencias": preferencias,
        "latitud": geocodificacion["lat"],
        "longitud": geocodificacion["lon"],
        "meteorologia": meteorologia,
        "lugares": lugares,
        "prompt_usado": prompt_usado,
        "itinerario": itinerario,
        "estado": "ok",
        "duracion_ms": duracion_ms,
        "error_resumido": None,
        "modo_demo": modo_demo,
        "modo_modelo": llm.LLM_MODE,
    }
    solicitud_id = db.guardar_solicitud(registro)

    return {
        "solicitud_id": solicitud_id,
        "ciudad": geocodificacion["ciudad"],
        "pais": geocodificacion["pais"],
        "tipo_turismo": tipo_turismo,
        "duracion_horas": duracion,
        "preferencias": preferencias,
        "lat": geocodificacion["lat"],
        "lon": geocodificacion["lon"],
        "meteorologia": meteorologia,
        "lugares": lugares,
        "itinerario": itinerario,
        "modo_demo": modo_demo,
        "modo_modelo": llm.LLM_MODE,
        "duracion_ms": duracion_ms,
    }

```
```

## Respuesta (transcripción de la ventana)

```text
已思考（用时 13 秒）

用户想要用通俗中文解释整体流程，并指出4个问题。不要完整重写代码，只给思路和风险提示，最后5行总结。

让我分析这个 orchestrator.py：

整体流程：

记录开始时间

验证输入（_validar_entrada）：城市、类型、时长、偏好

地理编码 geocodificar

获取天气 obtener_meteorologia

获取地点 obtener_lugares（Overpass），失败时用 fixture

组装 contexto

调用 LLM 生成行程

记录耗时

保存到 DB

返回 dict

问题1：异常分层

ValueError → 400 合理，因为输入验证在调用外部服务之前

供应商错误 → 502 合理，但代码里没有显式处理。geocodificar 和 obtener_meteorologia 的异常会直接冒泡。llm 的异常也会冒泡。db 的异常也会冒泡。

风险：Overpass 的 except Exception 太宽泛，会吞掉编程错误（如 AttributeError、TypeError），把真正的 bug 伪装成 demo 模式。而且它捕获了所有异常，包括 KeyboardInterrupt 之外的（实际上 Exception 不包含 KeyboardInterrupt/SystemExit）。

另外，geocodificar 失败时（城市不存在）应该是什么错误？可能是 404 或 422，而不是 502。当前代码没有区分"城市找不到"和"供应商挂了"。

LLM 失败、DB 失败没有处理，会冒泡成 500，但应该可能是 502/503。

异常分层没有在 orchestrator 里统一处理，依赖上层（Flask 路由）来映射。需要确保上层有统一的错误处理器。

问题2：返回 dict 是否够 HTML 和 JSON 共用

返回的 dict 包含 solicitud_id、城市、国家、类型、时长、偏好、lat/lon、天气、地点、行程、modo_demo、modo_modelo、duracion_ms

对于 JSON API 够用

对于 HTML 模板，需要额外的东西：表单回填值、错误信息、提示文本、格式化后的天气/行程（LLM 返回可能是 markdown 或纯文本）、lugares 可能需要展示名称/地址等。返回的 dict 没有 error 字段，HTML 渲染错误时需要单独处理。

缺少：输入的原样值（用于回填）、错误消息、状态码信息、是否可重试。

lugares 的结构取决于 api_clients，HTML 需要知道如何渲染。itinerario 可能是字符串，HTML 需要 markdown 渲染或分段。

契约没有版本化，HTML 和 JSON 共用同一个 dict 没问题，但 HTML 通常需要额外的展示层字段（如 formatted_weather、map_url 等）。

缺少"验证失败时的返回"——目前验证失败直接抛 ValueError，HTML 需要捕获并渲染表单，JSON 需要 400 响应体。返回 dict 只覆盖成功路径。

问题3：Overpass 失败时用 fixture 并标记 demo 的风险

风险：

掩盖真实故障：except Exception 吞掉所有异常，运维看不到 Overpass 挂了，监控失效。应该记录日志并区分异常类型。

数据误导用户：demo 数据可能和真实城市不匹配（fixture 是固定的），用户可能以为是真的。需要 UI 上明确提示。

污染 DB：demo 数据被持久化，后续分析/报表会混入假数据。需要在 DB 里标记并考虑是否入库。

LLM 基于假地点生成行程，结果看似合理但实际不可用，用户按图索骥会失败。

测试时 fixture 可能让测试"永远通过"，掩盖集成问题。

安全/合规：如果 fixture 包含真实地点信息但过期，可能误导。

except Exception 还会捕获 KeyError、TypeError 等编程错误，让 bug 静默。

没有区分"Overpass 返回空"和"Overpass 报错"——空结果用 [] 是合理的，但空结果也可能意味着查询有问题。

没有重试/超时策略的体现（可能在 api_clients 里）。

modo_demo 只标记了 Overpass，但 LLM 也可能降级（modo_modelo），需要统一。

问题4：测试应该覆盖哪些点

验证层：

城市空/空白/超长/非字符串

类型非法

时长非整数/不在 {2,4,6}

偏好超长/None

正常输入归一化（strip、int 转换）

成功路径：

调用顺序（地理编码→天气→Overpass→LLM→DB）

contexto 内容正确

返回值字段完整

duracion_ms 合理

DB 保存被调用且参数正确

异常路径：

地理编码失败（城市找不到 vs 供应商错误）

天气失败

Overpass 失败 → fixture + modo_demo=True

Overpass 返回空列表 → 不触发 demo（当前代码是这样）

LLM 失败

DB 失败

确认外部服务在验证失败时未被调用（mock 断言）

降级标记：

modo_demo 和 modo_modelo 正确传递到返回和 DB

性能/计时：

duracion_ms 计算

契约测试：

返回 dict 的键稳定，HTML 和 JSON 都能消费

幂等/重复请求？可能不需要。

边界：ciudad 恰好 80 字符、preferencias 恰好 200。

安全：输入包含特殊字符（SQL 注入由 ORM 处理，但 XSS 需要在模板层）。

mock 所有外部依赖（api_clients、llm、db），不真实调用。

集成测试：用真实 fixture 跑通。

并发/超时？可能超出范围。

现在组织答案。用户要求通俗中文，不要完整重写代码，给思路和风险提示，最后5行总结。

我应该先解释整体流程（通俗），然后分4点回答，最后5行总结。

注意：用户说"不要给完整重写代码"，所以只给思路。

让我写答案。

整体流程解释：

入口只有一个 procesar_solicitud，HTML 和 JSON 都走这里，避免规则重复。

第一步验证：在调用任何外部服务前，把输入清洗、校验，非法就抛 ValueError。

第二步地理编码：把城市名变成经纬度和标准城市/国家名。

第三步天气：用经纬度查天气。

第四步 Overpass：用经纬度+类型查兴趣点；失败就加载本地 fixture 并标记 demo。

第五步组装 contexto，交给 LLM 生成行程和 prompt。

第六步计时、组装 DB 记录、保存，返回给调用方。

异常分层：

ValueError → 400：合理，因为验证发生在外部调用之前，属于客户端错误。

供应商错误 → 502：方向对，但代码里没有显式分层。geocodificar/天气/LLM/DB 的异常会原样冒泡，需要上层（Flask errorhandler）统一映射。要区分：城市不存在（404/422）vs 供应商 5xx/超时（502/503）vs DB 失败（500/503）。

Overpass 的 except Exception 太宽，会吞掉编程错误，让 500 变成"成功但 demo"，这是最大的分层问题。

建议定义自定义异常类（如 ValidationError、ProviderError、NotFoundError），在 api_clients/llm 层抛出，orchestrator 不吞或只捕获特定异常。

返回 dict：

对 JSON 基本够，对 HTML 不够。缺错误字段、表单回填、格式化展示字段、是否可重试、提示文案。

成功路径统一没问题，但失败路径没有统一契约（抛异常 vs 返回 dict）。HTML 和 JSON 对错误的消费方式不同，需要上层统一。

lugares/itinerario 的结构对 HTML 渲染不友好，可能需要展示层适配器。

建议保持"核心数据"共用，HTML 用模板层加展示字段，或返回一个包含 data + meta + error 的信封结构。

fixture 风险：

静默失败、监控缺失、数据误导、污染 DB、LLM 基于假数据生成看似合理的行程、测试假阳性、吞掉编程 bug。

需要在 UI 明确标识、记录日志/指标、DB 标记、考虑是否入库、区分异常类型、加超时/重试。

测试点：如上列表，分组。

最后5行总结。

注意语言：通俗中文，但技术术语保留。可以适当用比喻。

让我写一个结构清晰的回答。长度适中，不要太啰嗦。用户要的是思路和风险提示。

我会用 markdown 格式。

整体流程（通俗版）

procesar_solicitud 是唯一入口，HTML 表单和 JSON API 都调它，避免两套规则。流程像一条流水线：

先验货：_validar_entrada 在碰任何外部服务之前，把城市、类型、时长、偏好清洗并校验，不合法直接抛 ValueError。

城市变坐标：geocodificar 把城市名换成经纬度 + 标准城市/国家名。

查天气：用经纬度拿天气。

找地点：用经纬度 + 类型查 Overpass；失败就加载本地 fixture，并打上 modo_demo=True。

组装上下文：把城市、天气、地点、偏好等拼成 contexto。

让 LLM 写行程：返回 itinerario 和实际用的 prompt_usado。

计时 + 落库 + 返回：组装 DB 记录，db.guardar_solicitud 保存，最后返回一个 dict 给调用方。

1) 异常分层是否合理

方向对，但当前代码没有真正“分层”，只是“抛出去”。

ValueError → 400：合理。验证发生在任何外部调用之前，属于客户端错误，而且能保证“验证失败时不消耗供应商配额”。

供应商错误 → 502：方向对，但代码里没有显式处理。geocodificar、天气、LLM、DB 的异常会原样冒泡，最终靠 Flask 上层 errorhandler 映射。需要确认上层确实有统一映射，否则会变成 500。

最大的问题：Overpass 的 except Exception 太宽。它会把 KeyError、TypeError、AttributeError 这类编程错误也吞掉，伪装成“demo 成功”。真正的供应商故障反而应该被记录和告警。

建议区分三类：

输入错误 → ValueError / 自定义 ValidationError → 400；

城市找不到 → 404 或 422（不是 502）；

供应商超时/5xx/限流 → 自定义 ProviderError → 502/503；

DB 失败 → 500/503，且不应把“已生成但没存上”当成成功返回。

不建议在 orchestrator 里到处 try/except；让 api_clients/llm 抛出自定义异常，orchestrator 只决定“哪些能降级、哪些必须冒泡”。

2) 返回的 dict 是否够 HTML 和 JSON 共用

成功路径基本够，失败路径和展示层不够。

对 JSON API：字段比较完整（solicitud_id、modo_demo、modo_modelo、duracion_ms 都有），可以直接序列化。

对 HTML 模板：缺几类东西——

错误契约：验证失败是抛异常，不是返回 dict；HTML 需要回填表单 + 错误提示，JSON 需要 {error: ...} 结构。两条路径没有统一“信封”。

展示字段：天气、lugares、itinerario 的原始结构未必适合直接渲染（LLM 可能返回 Markdown，地点可能需要名称/地址/距离）。HTML 通常需要展示层适配，而不是把原始 dict 硬塞进模板。

元信息：是否可重试、提示文案、请求 ID、时间戳，JSON 客户端和前端都常用。

建议：核心数据共用一份，HTML 在模板层做“展示适配”；或者返回 {data, meta, error} 信封，成功/失败都走同一结构。关键是别让 HTML 和 JSON 各自去猜异常怎么处理。

3) Overpass 失败用 fixture 并标记 demo 的风险

风险不小，主要有这些：

静默故障：except Exception 让 Overpass 挂了也“看起来成功”，监控和日志拿不到信号，运维不会知道。

吞掉编程 bug：KeyError/TypeError 也会进 demo 分支，真正的代码错误被掩盖。

数据误导：fixture 是固定的，可能和用户查的城市完全不匹配；LLM 基于假地点生成的行程看起来合理，用户照着走会踩空。

污染 DB：demo 数据被持久化，后续统计、报表、模型评估会混入假数据。至少要在 DB 里显式标记，并考虑是否入库。

测试假阳性：fixture 让集成测试永远“通过”，掩盖 Overpass 契约变化。

边界没区分：“Overpass 返回空列表”和“Overpass 报错”是两回事。空结果用 [] 合理，但空结果也可能是查询写错，不能一律当正常。

建议：只捕获明确的供应商异常；记录日志和指标；UI 上显著提示“演示数据”；DB 标记 modo_demo 并在查询时过滤；给 Overpass 加超时/重试；fixture 只用于本地开发和显式演示开关，不要默认兜底。

4) 测试应该覆盖哪些点

按层分组：

验证层（不碰外部服务）

城市空、纯空白、非字符串、超长（80/81 边界）；

类型非法、大小写/空格；

时长非整数、"4"、4.0、不在 {2,4,6}；

偏好 None、超长（200/201 边界）、strip 归一化；

断言验证失败时 geocodificar/天气/Overpass/LLM/DB 都没被调用（mock 断言）。

成功路径

调用顺序：地理编码 → 天气 → Overpass → LLM → DB；

contexto 字段正确（城市、国家、天气、地点、偏好）；

返回 dict 字段完整、类型正确；

duracion_ms 为正且合理；

db.guardar_solicitud 收到的记录包含 modo_demo、modo_modelo、prompt_usado、error_resumido。

异常/降级路径

地理编码失败（城市找不到 vs 供应商 5xx 要分开测）；

天气失败；

Overpass 抛供应商异常 → fixture + modo_demo=True；

Overpass 返回 [] → 不触发 demo（当前逻辑如此，要测清楚）；

Overpass 抛 TypeError 之类的编程错误 → 应该冒泡而不是被吞（如果保留宽 except，这条会失败，正好暴露问题）；

LLM 失败、DB 失败 → 上层映射正确；

modo_modelo 降级时返回值一致。

契约/集成

返回 dict 的键稳定，HTML 模板和 JSON 序列化都能消费；

用 fixture 跑通端到端（但明确标记这是 demo 路径）；

特殊字符输入（XSS 在模板层测，SQL 注入靠 ORM）；

并发/重复请求是否产生重复记录（看业务要求）。

原则：外部依赖全部 mock，测试不真实调用 Cohere/Overpass/天气/DB；另有一组少量集成测试验证真实契约。

5 行总结

流程清晰：验证 → 地理编码 → 天气 → Overpass → LLM → DB，单入口避免 HTML/JSON 规则分裂。

异常分层方向对，但缺自定义异常和统一映射；except Exception 吞掉编程错误是最大隐患。

返回 dict 对 JSON 够用，对 HTML 缺错误契约和展示字段，建议用信封结构 + 模板层适配。

fixture 兜底会静默故障、误导用户、污染 DB，必须记日志、显眼提示、DB 标记，且只捕获明确供应商异常。

测试重点：验证层不触外部、成功路径字段与顺序、各类供应商失败与降级标记、demo 与空结果区分、契约稳定性。

本回答由 AI 生成，内容仅供参考，请仔细甄别
```

## Nota de honestidad

Consulta real. El estudiante debe contrastar las recomendaciones con el código y anotar en su memoria qué aceptó, qué descartó y cómo lo verificó.
