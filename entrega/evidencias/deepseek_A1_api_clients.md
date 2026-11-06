# Consulta IA — A1 CityPilot IA (geocodificación + meteorología)

- **Fecha:** 2026-11-06T08:03:37.936Z
- **Herramienta:** DeepSeek Chat (https://chat.deepseek.com)
- **URL de la conversación:** https://chat.deepseek.com/a/chat/s/77876cf9-3d91-42da-a075-677200c186bc
- **Uso previsto:** entender el esqueleto y los casos límite antes de implementar A1 (semáforo amarillo, memoria individual).

## Prompt enviado

```text
我在做 UEV 的 Flask + PostgreSQL 项目 CityPilot IA。下面是老师给的 api_clients.py 骨架，A1 任务要求我实现 geocodificar 和 obtener_meteorologia。请先用通俗中文解释这段代码整体在做什么、每个函数和常量的作用；然后说明：
1) geocodificar 必须处理哪些情况（timeout、HTTP 错误、results 为空、字段缺失）；
2) obtener_meteorologia 的 current 字段怎么取，字段缺失怎么办；
3) 常见错误和测试思路。
不要直接给完整最终代码，给思路、关键注意点和验收方法，最后用 5 行总结。

代码如下：
```python
"""Clientes HTTP de datos públicos. Se entregan los contratos, NO la solución."""
import json
import os
from pathlib import Path
import requests

GEO_URL = os.getenv("OPEN_METEO_GEO_URL", "https://geocoding-api.open-meteo.com/v1/search")
METEO_URL = os.getenv("OPEN_METEO_WEATHER_URL", "https://api.open-meteo.com/v1/forecast")
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")


def geocodificar(ciudad: str) -> dict:
    """TODO(ALUMNADO).

    Entrada: 'Valencia'. Salida normalizada: {'ciudad': 'Valencia',
    'pais': 'España', 'lat': 39.47, 'lon': -0.38} (números ilustrativos).
    Usar Open-Meteo Geocoding y controlar búsqueda sin resultados.
    Restricción: peticiones con timeout, filtrando countryCode='ES' si se
    decide limitar a España.
    """
    raise NotImplementedError("Implementa búsqueda de coordenadas")


def obtener_meteorologia(lat: float, lon: float) -> dict:
    """TODO(ALUMNADO).

    Devolver, como mínimo: temperatura_c, precipitacion_mm,
    codigo_tiempo, instante. Seleccionar current=temperature_2m,
    precipitation,weather_code e incluir timezone=auto.
    """
    raise NotImplementedError("Implementa consulta meteorológica")


def obtener_lugares(lat: float, lon: float, tipo: str) -> list[dict]:
    """TODO(ALUMNADO).

    Consultar un radio urbano acotado de Overpass/OSM (2-3 km).
    Filtrar según tipo: cultural, gastronomica, naturaleza, familiar.
    Normalizar a [{nombre, categoria, lat, lon, fuente, ...}], máximo
    8-12 lugares. Gestionar nodos (lat/lon) y ways/relations (center).
    Nunca introducir valores libres del usuario en una consulta QL.
    """
    raise NotImplementedError("Implementa consulta de puntos de interés")


def cargar_fixture_lugares() -> list[dict]:
    """Utilidad entregada para simular Overpass durante pruebas sin Internet.

    Los lugares son FICTICIOS y deben identificarse como DEMO en la UI.
    """
    file_path = Path("/fixtures/puntos_demo.json")
    if not file_path.exists():
        file_path = Path(__file__).resolve().parents[2] / "fixtures/puntos_demo.json"
    return json.loads(file_path.read_text(encoding="utf-8"))["lugares"]

```
```

## Respuesta de DeepSeek (transcripción de la ventana)

```text
已思考（用时 40 秒）

用户要求用通俗中文解释代码整体、每个函数和常量作用；然后说明 geocodificar 必须处理的情况；obtener_meteorologia 的 current 字段怎么取，字段缺失怎么办；常见错误和测试思路。不要给完整最终代码。最后 5 行总结。

我需要仔细分析。代码是 Flask+PostgreSQL 项目 CityPilot IA 的 api_clients.py 骨架。模块级 docstring 说"Clientes HTTP de datos públicos. Se entregan los contratos, NO la solución." 即"公共数据 HTTP 客户端。给出的是契约，不是解答"。

导入：json, os, pathlib.Path, requests。

常量：

GEO_URL: 从环境变量 OPEN_METEO_GEO_URL 读，默认 Open-Meteo Geocoding API search 端点。用于把城市名转经纬度。

METEO_URL: 从环境变量 OPEN_METEO_WEATHER_URL 读，默认 Open-Meteo forecast。用于查天气。

OVERPASS_URL: 从环境变量 OVERPASS_URL 读，默认 overpass-api.de interpreter。用于查 OSM 兴趣点。

函数：

geocodificar(ciudad: str) -> dict：TODO。输入城市名，输出规范化 dict：ciudad, pais, lat, lon。用 Open-Meteo Geocoding，控制无结果。超时，可选 countryCode='ES' 限制西班牙。

obtener_meteorologia(lat, lon) -> dict：TODO。返回至少 temperatura_c, precipitacion_mm, codigo_tiempo, instante。选 current=temperature_2m, precipitation, weather_code，timezone=auto。

obtener_lugares(lat, lon, tipo) -> list[dict]：TODO。Overpass/OSM 2-3km 半径。按 tipo 过滤 cultural/gastronomica/naturaleza/familiar。规范化 {nombre,categoria,lat,lon,fuente,...}，最多 8-12。处理 nodes 和 ways/relations 的 center。不要把用户自由值拼进 QL。

cargar_fixture_lugares() -> list[dict]：已给的实用函数。从 /fixtures/puntos_demo.json 或项目根 fixtures/puntos_demo.json 读，返回 ["lugares"]。用于无网测试模拟 Overpass。DEMO 标识。

需要解释整体：这个模块是外部数据访问层（adapter/client），把第三方公开 API 的原始 JSON 转成项目内部规范化结构，供 Flask 路由/服务层调用。好处：路由不直接依赖外部 API 细节；便于 mock/测试；环境变量可切换端点。

然后具体问题：

geocodificar 必须处理哪些情况：

输入清洗：ciudad 为空/空白/None/非字符串；strip；大小写/重音？URL 参数用 params 让 requests 编码。

timeout：requests.get(..., params=..., timeout=...) 必须设，捕获 requests.Timeout（Timeout 是 RequestException 子类）。

HTTP 错误：raise_for_status() 或检查 status_code；捕获 requests.HTTPError / RequestException。注意 4xx/5xx。

网络/连接错误：ConnectionError, RequestException。

JSON 解析错误：response.json() 可能 ValueError/JSONDecodeError（requests 抛 requests.exceptions.JSONDecodeError 继承 InvalidJSONError? 实际 requests 的 JSONDecodeError 继承 InvalidJSONError 和 json.JSONDecodeError）。用 try/except。

results 为空或缺失：data.get("results") 为 None/[] 时要明确返回什么？契约输出是 dict，但没有结果怎么办？需要项目约定，比如返回 None 或抛自定义异常/ValueError。老师要求"控制ar búsqueda sin resultados"。不能返回半成品。常见是 raise ValueError("Ciudad no encontrada") 或返回 None，取决于上层。要提到与路由/测试约定一致。

字段缺失：results[0] 里缺 latitude/longitude/name/country。缺经纬度必须报错/跳过；不能默认 0。字段名是 latitude, longitude, name, country, country_code, admin1 等。注意 Open-Meteo geocoding 返回 results[0].latitude/longitude/name/country/country_code。

countryCode='ES' 过滤：如果决定限制西班牙，在 params 里加 countryCode=ES（Open-Meteo Geocoding 参数名是 countryCode），并且要处理过滤后无结果。注意如果 API 不支持该参数？Open-Meteo geocoding 支持 countryCode。或者返回后过滤 country_code == 'ES'，但这样 results[0] 可能不是西班牙。建议用参数。

类型转换：lat/lon 转 float；检查范围（-90..90, -180..180）；NaN/Inf。

返回 dict 键名固定：ciudad, pais, lat, lon。pais 用 country 还是 country_code？示例 'España' 是 country 名称。如果 country 缺失可以用 country_code 或空字符串？契约要求国家，缺失要处理。

多结果：取第一个还是按 population 排序？Open-Meteo 返回可能多个同名城市；可考虑取 results[0]，或按 countryCode 和人口。要说明选择策略并测试。

超时单位秒；不要无限等待。

不要泄露异常细节给用户；日志记录。

编码：params 用 dict 自动编码，不要手动拼 URL。

重试？可选，不要过度。

obtener_meteorologia 的 current 字段怎么取，字段缺失怎么办：

请求 params: latitude=lat, longitude=lon, current="temperature_2m,precipitation,weather_code", timezone="auto"。可能还要 forecast_days=1 减小响应。

响应结构 Open-Meteo: {"latitude":..., "longitude":..., "timezone":..., "current_units": {...}, "current": {"time":"2024-...", "interval":900, "temperature_2m": 25.3, "precipitation": 0.0, "weather_code": 3}}

取 data["current"]，再取 current["temperature_2m"], current["precipitation"], current["weather_code"], current["time"]。

字段缺失：current 整个缺失/None -> 抛错或返回带 None 的 dict？契约说"至少"这些字段，建议明确：如果关键字段缺失，不能静默填 0（0 有物理意义，会误导）。可以返回 None 并让上层处理，或抛异常。验收时通常检查字段存在。若个别字段缺失，用 .get() 得到 None 并在返回 dict 中保留键，或者抛 ValueError。要区分：temperature 缺失 -> None；precipitation 缺失 -> None；weather_code 缺失 -> None；time 缺失 -> None 或当前时间？不要伪造 instante。最好保留 None 并记录。但如果测试要求数值，则抛异常。建议与项目约定一致，至少不要 KeyError 崩溃。

类型转换：float(temp), float(precip), int(weather_code)；注意 None 不转。

current 可能是 dict 但字段为 null；Open-Meteo 一般会给。

也要处理 HTTP/timeout/JSON 错误，同 geocodificar。

参数校验 lat/lon 数值和范围。

timezone=auto 让 time 带本地时区偏移；instante 用 current["time"]。

单位：temperature_2m 默认 °C，precipitation mm，weather_code WMO。current_units 可用来确认。

不要用 hourly/daily 误取；current 是当前时刻。

返回键名固定：temperatura_c, precipitacion_mm, codigo_tiempo, instante。

常见错误和测试思路：
常见错误：

忘记 timeout 或 timeout 太短/太长。

直接 response.json()["results"][0] 导致 KeyError/IndexError。

不检查 status_code，把错误页当 JSON。

手动字符串拼 URL，城市名含空格/重音/& 出错；应使用 params。

把 countryCode 大小写写错（参数名 countryCode，值 ES）。

字段名写错：latitude/longitude vs lat/lon；temperature_2m；weather_code；precipitation。

把缺失值填 0 或空字符串，掩盖问题。

返回键名与契约不一致（temperatura_c vs temperatura）。

未处理 requests 异常导致 Flask 500。

未关闭 response？requests.get 返回 Response，用完可 with 或不用显式关闭（连接池会处理），但可提。

环境变量默认值拼写错误。

测试依赖真实网络导致不稳定；应 mock requests.get。

fixture 路径：/fixtures 绝对路径在容器外可能不存在，已给回退；测试时注意。

在 Overpass QL 拼接用户输入（虽然本题前两个不涉及，但整体模块注意）。

日志打印敏感信息？不。

类型注解与返回 None 不一致。

测试思路：

单元测试 mock requests.get，构造 fake Response（status_code, json(), raise_for_status）。

geocodificar 正常：返回 results 一条，断言返回 dict 键和值，断言调用 params 含 name、count、language?、format=json、countryCode=ES、timeout。

无结果：results=[] 或缺失 -> 断言抛 ValueError/返回 None（按约定）。

HTTP 500：raise_for_status 抛 HTTPError -> 断言抛自定义/ValueError，不返回脏数据。

timeout：mock 抛 requests.Timeout -> 断言被捕获并转成项目异常。

字段缺失：results[0] 缺 latitude -> 断言报错而不是 0。

多结果：两个结果，断言选择策略（第一个或西班牙）。

obtener_meteorologia 正常：current 完整，断言返回键和单位/值；断言 params current 字符串、timezone=auto、timeout。

current 缺失：{} 或 None -> 断言抛错/None 字段。

current 部分字段缺失：断言不 KeyError，按约定 None 或异常。

类型：字符串数字转 float。

集成测试：可选用真实 API 标记 slow/network，不放进 CI 默认。

契约测试：用 jsonschema 或断言键集合。

Flask 层测试：用 test_client，mock client 层，验证 200/404/502 映射。

用 fixture 测试 cargar_fixture_lugares 路径和 DEMO 标识。

测试环境变量覆盖：monkeypatch.setenv 后 reload 模块？常量在 import 时读取，测试时注意。可以 monkeypatch 模块常量。

还要注意：这是教育任务，不要给完整代码。可以给伪代码思路和断言清单。

需要通俗中文解释每个函数和常量。结构清晰。

最终 5 行总结。注意"最后用 5 行总结"——可以 5 个短行，每行一句。

我要确保不直接给完整最终代码。可以给关键片段？最好不给完整函数代码，只给参数名、伪代码、断言。可给 params 示例 dict 和返回结构示例，这不算完整代码。可以给异常处理顺序的伪代码列表。

关于 Open-Meteo Geocoding 参数：name, count, language, format=json, countryCode。默认 format=json? API 默认 json。可以提 count=1 或 5。countryCode=ES。返回 results 数组，字段：id, name, latitude, longitude, elevation, feature_code, country_code, admin1_id, timezone, population, country_id, country, admin1。所以 country 是名称。country_code 是 "ES"。示例返回 pais 'España' 来自 country。

Open-Meteo forecast 参数：latitude, longitude, current=temperature_2m,precipitation,weather_code, timezone=auto。返回 current.time。可能还需要 forecast_days=1。current_units。

异常：requests.exceptions.Timeout, ConnectionError, HTTPError, RequestException, JSONDecodeError。顺序：先 Timeout/ConnectionError 可归 RequestException；raise_for_status 后 HTTPError。注意 Timeout 是 RequestException 子类；HTTPError 也是。如果先捕获 RequestException 再捕获 HTTPError 就捕不到具体。建议先具体后宽泛。

geocodificar 无结果返回什么：契约是 dict，不能返回 None 如果类型注解 dict。可以抛 ValueError 或自定义 CityNotFoundError。要跟老师/上层约定。可以说"若项目约定允许 Optional 则返回 None，否则抛业务异常；关键是不要返回伪造坐标"。类型注解是 dict，建议抛异常。测试时要断言异常类型。

字段缺失 country：可以用 country_code 兜底？但契约 pais 是 'España'，最好 country；缺 country 可报错或用 country_code。注意不要静默空字符串？可以提策略需明确。

obtener_meteorologia 字段缺失：返回 dict 中键存在但值为 None 是较稳的契约；但"至少"可能测试要求数值。建议：若 current 整体缺失 -> 抛异常（上游 502/503）；若单个可选字段缺失 -> None 并在日志警告；若 temperature 缺失可能也抛。需要明确项目约定。验收方法：断言键总存在；对缺失字段测试不崩溃。

常见错误还包括：response.json() 在非 JSON 时抛异常；应该先检查 content-type? 不一定，try/except 即可。status_code 204? 不。

测试 mock：可以用 unittest.mock.patch("api_clients.requests.get")，返回 Mock(status_code=200, json.return_value=...)。raise_for_status 在 Mock 上默认返回 Mock 不抛；需要配置 side_effect。或者实现 FakeResponse 类。断言调用参数：requests.get.assert_called_once(); kwargs 包含 params, timeout。注意 params 里不要断言 dict 顺序。

测试超时：patch requests.get side_effect=requests.Timeout。断言抛项目异常。

测试 fixture：cargar_fixture_lugares 读取 JSON，断言是 list，每个有 nombre 等，标识 DEMO 可能不在函数里，而是在 UI 层根据 fuente 判断。注意 fixture 文件是虚构的。

整体架构解释：这是"端口/适配器"里的适配器；Flask 路由/服务层调用这些函数；PostgreSQL 存用户/行程；外部 API 提供地理、天气、POI。环境变量便于部署和测试替换。cargar_fixture_lugares 是测试替身。

还要解释 docstring "Se entregan los contratos, NO la solución"：老师给的是接口契约和骨架，学生实现，不能改签名/返回结构。

每个常量作用：

GEO_URL：地理编码端点，把文本城市名解析为坐标。

METEO_URL：天气预报端点，按坐标取当前天气。

OVERPASS_URL：OSM 查询端点，按坐标/半径取 POI。

环境变量：部署时可换镜像/代理/测试服务器；默认值保证开箱即用。注意常量在模块导入时求值，测试改环境变量需 reload 或 monkeypatch 常量。

函数 cargar_fixture_lugares：已实现，读取 fixtures/puntos_demo.json；先试绝对 /fixtures（容器挂载），再试项目根 fixtures（本地开发）；返回 ["lugares"]；用于无网测试；DEMO 标识需 UI 显示。注意路径 parents[2]：file 是 .../src/.../api_clients.py? parents[0]=目录, [1]=上级, [2]=上上级。项目结构可能 api_clients.py 在 app/ 下，parents[2] 是项目根。解释即可。

需要"通俗中文"——避免太学术。用类比：这个文件像"翻译官/外卖前台"。

现在组织答案：

开头：整体一句话 + 模块结构。

模块整体：外部数据客户端层；三个外部服务；统一规范化；环境变量可配置；fixture 离线测试。

常量逐个。

函数逐个（包括 TODO 和已实现）。

然后 1) geocodificar 情况清单。可以用表格式：情况/要做什么/验收断言。不要完整代码。

obtener_meteorologia current 取法：响应结构示例（JSON 片段可以），params，取 current，缺失策略。给一个返回 dict 示例。注意"字段缺失怎么办"分层次：current 缺失、current 为 null、单字段缺失、类型不对。建议策略 + 测试。

常见错误和测试思路：分"实现常见坑"和"测试清单"。测试用 mock；给断言点。可给伪代码步骤，不是完整代码。

最后 5 行总结，每行一句，编号或短句。

需要控制长度但足够详细。Desired oververbosity 5。中文。不要给完整最终代码。可以给参数和返回结构示例。

注意不要写"完整最终代码"，但可以给类似：

text
复制
下载
params = {"name": ciudad, "count": 1, "language": "es", "format": "json", "countryCode": "ES"}

这算关键注意点，不是完整函数。可以。

异常处理伪代码：

校验输入

try: r = requests.get(GEO_URL, params=..., timeout=5)

r.raise_for_status()

data = r.json()

results = data.get("results") or []

if not results: raise ...

item = results[0]; 取字段...
这不是完整代码，是步骤。可以。

geocodificar 字段缺失：name 缺失可以用输入 ciudad 兜底？契约 ciudad 输出应该是规范化名称。如果 name 缺失，用输入 ciudad 作为 ciudad 也可以，但要明确。lat/lon 缺失绝不能默认。country 缺失可用 country_code 或空？建议报错/None。测试断言。

countryCode 过滤：如果加 countryCode=ES，API 只返回西班牙；如果结果空，说明西班牙找不到。若不限制，返回第一个可能不是西班牙。任务说"filtrando countryCode='ES' si se decide limitar a España"，即可选。要说明决策并测试。

obtener_meteorologia 的 current 字段怎么取：current 是响应里的对象；不是 current_weather（旧 API）。参数 current 是逗号分隔字符串。取 current["time"] 等。timezone=auto 影响 time 的时区。current_units 可用于断言单位。字段缺失：用 current.get；不要用 current["x"] 直接索引；但要在返回前校验关键字段。可以建议返回 None 而不是 0。测试：current={} 时返回四个键值为 None 或抛异常；取决于约定。验收：不出现 KeyError；不把 None 当 0。

常见错误：把 current 参数写成列表？requests params 可以列表? 最好字符串。把 weather_code 写成 weathercode。把 precipitation 写成 precipitation_mm。把 temperature_2m 写成 temperature。timezone 不设导致 instante 是 UTC，契约可能要求本地。不设 timeout。不检查 results。用 results[0]。把 countryCode 写成 country_code（API 参数是 countryCode）。用 response.json 不加括号。异常捕获太宽 except: 吞掉。把 HTTP 错误当成功。日志打印完整响应。测试真实网络。测试只测 happy path。mock 时没有配置 raise_for_status 导致没测 HTTP 错误。测试断言过严（依赖真实温度）。环境变量常量在 import 时读取，monkeypatch 不生效。

测试思路详细：

用 pytest + monkeypatch/mock。

FakeResponse 类：status_code, payload, json(), raise_for_status()。

正常 geocoding：payload results 一条；断言返回 dict 精确等于；断言 timeout 存在；断言 params["name"]=="Valencia"；params["countryCode"]=="ES"（若采用）。

空 results：payload {"results": []} 或 {}；断言 raises ValueError/自定义；断言没有返回 lat=0。

HTTP 500：raise_for_status side_effect=requests.HTTPError；断言转换异常。

timeout：requests.get side_effect=requests.Timeout；断言。

字段缺失：results[0] 缺 latitude；断言异常。

天气正常：current 完整；断言返回键和值；断言 params["current"] 包含三个字段；params["timezone"]=="auto"。

天气 current 缺失：payload {"current": {}} 或 {}；断言不 KeyError，按约定。

天气字段 null：断言 None 或异常。

天气 HTTP/timeout 同。

集成 smoke：真实调用标记 network，手动跑，不默认 CI。

契约测试：断言键集合；类型 float/int/str。

Flask 路由测试：mock api_clients 函数，验证 200 和错误映射（404/502）。

fixture 测试：临时目录/项目根；断言读取 list；断言 DEMO 来源标识。

最后 5 行总结：

这个文件是 CityPilot IA 的外部数据适配层，统一封装地理编码、天气和 OSM POI。

常量是可被环境变量覆盖的三个 API 地址，函数负责把原始响应规范化成项目契约。

geocodificar 要防输入、超时、HTTP/JSON 错误、空 results、缺经纬度，不能伪造坐标。

obtener_meteorologia 从响应的 current 对象取四个字段，缺失时按约定返回 None 或抛业务异常，绝不默认 0。

测试用 mock 覆盖正常/空/异常/缺字段，断言参数、返回键、异常类型，真实网络只做手动 smoke。

要确保"5 行"就是 5 行。可以用 1-5 列表。

开始写答案。要通俗。注意中文术语。可加小标题。

关于"每个函数和常量的作用"要覆盖所有。cargar_fixture_lugares 已给，解释。

还可能要解释 Path(__file__).resolve().parents[2]。简单提。

关于 requests 的 JSONDecodeError：requests.exceptions.JSONDecodeError 在较新版本；也可捕获 ValueError。提"JSON 解析失败（ValueError/JSONDecodeError）"。

geocodificar 输入校验：ciudad 不是 str 或 strip 为空 -> ValueError。不要请求。测试。

输出契约：{'ciudad': ..., 'pais': ..., 'lat': float, 'lon': float}。多结果选择：可 count=1 或取 results[0]；如果同名多国，countryCode=ES 可减少歧义。若不加 countryCode，测试要覆盖多结果策略。建议教育项目限制西班牙以稳定测试；但任务说"si se decide"，所以说明两种。

关于 countryCode 参数值大小写：Open-Meteo 文档是 countryCode 参数，值如 ES。返回字段 country_code 是 ES。注意区分。

obtener_meteorologia 返回示例：

text
复制
下载
{
  "temperatura_c": 24.5,
  "precipitacion_mm": 0.0,
  "codigo_tiempo": 3,
  "instante": "2026-11-06T12:00"
}

instante 来自 current["time"]。timezone=auto 时可能带偏移，如 2026-11-06T12:00+01:00？Open-Meteo current time 格式 2024-06-11T12:15 可能不带偏移但按 timezone 本地时间。不要过度断言格式，只断言非空/可解析。测试时用固定 payload。

缺失策略建议：

响应没有 current 或不是 dict：抛 ValueError("Respuesta meteorológica inválida") 或项目异常，让路由返回 502。

current 存在但单字段缺失/null：返回 None 并保留键；记录 warning；上层决定展示"暂无数据"。如果项目要求数值，则抛异常。关键：测试要固定约定。

temperature_2m 是 0 是合法值，不能把 0 当缺失（用 in 或 is not None 判断，不要 or，因为 0 or None 会变成 None）。这是一个重要坑！要提。precipitation 0 同理。weather_code 0 是"晴"，合法。所以用 current.get("temperature_2m")，判断 is None，不要 or 默认值。这个很关键。测试要覆盖 0 值。好点。

geocodificar 的 lat/lon 0 也是合法（赤道/本初子午线），但西班牙不涉及；不要用 or 判断。提一下。

测试零值：temperature=0, precipitation=0, weather_code=0 应正常返回，不被当作缺失。这是常见错误。

常见错误还包括：if not temperature: 把 0 当缺失。好。

请求超时值：建议 3-5 秒或 5-10 秒；测试不依赖具体值，只断言传了 timeout。不要给太具体？可以给"比如 5 秒，按项目要求"。

HTTP 错误处理：raise_for_status() 在 4xx/5xx 抛 HTTPError；如果手动检查 status_code，要覆盖。建议 raise_for_status 简单。测试 mock 时配置。

JSON 解析：r.json() 失败要捕获。注意 raise_for_status 先于 json，避免对错误页解析。

重试：可选，不建议初学；如果加，限制次数和退避，测试复杂。提"非必需"。

日志：用 logging，不要 print；异常日志带城市名/坐标但不带密钥（无密钥）。

安全：城市名不拼 URL；Overpass 不拼用户输入。本题前两个用 params 自动编码。提一下整体。

模块导入时读环境变量：测试要 monkeypatch 模块常量或 reload。提。

Flask 集成：这些函数不应直接 abort，应抛业务异常由路由映射 404/502；或返回 None。教育项目可能简单。提"与上层约定"。

现在写。需要"不要直接给完整最终代码"——我不会给完整函数。参数示例和伪步骤可以。语气通俗。

结构：

整体在做什么

常量/函数逐个

geocodificar 必须处理

obtener_meteorologia current

常见错误和测试思路

5 行总结

可以加"验收清单"表格。长度适中。

写中文。注意术语：地理编码、规范化、契约、适配器、夹具/fixture、打桩/mock。

开始。

一、这段代码整体在做什么

一句话：这是 CityPilot IA 的“外部数据翻译层”。Flask 路由/业务层不直接调 Open-Meteo、OSM，而是调用这个文件里的函数；函数负责发 HTTP 请求、处理异常、把第三方返回的“原始 JSON”翻译成项目内部统一的字典/列表格式。

老师开头写的 Se entregan los contratos, NO la solución 意思是：接口签名和返回格式是契约，具体实现要你写。所以你最好不要改函数名、参数、返回键名。

整体分工：

地理编码：城市名 → 经纬度；

天气：经纬度 → 当前温度、降水、天气代码、时间；

POI：经纬度 + 类型 → 附近文化/美食/自然/亲子地点；

fixture：没网时用假数据测试，不依赖 Overpass。

二、常量和函数逐个解释
常量
常量	作用
GEO_URL	Open-Meteo 地理编码接口地址。把 "Valencia" 这类文本解析成纬度/经度。
METEO_URL	Open-Meteo 天气预报接口地址。按经纬度查当前天气。
OVERPASS_URL	Overpass/OSM 查询接口。按坐标和半径查兴趣点。

三个都写成：

python
复制
下载
os.getenv("环境变量名", "默认地址")

意思是：部署时可以用环境变量换地址，比如换镜像、代理、测试服务器；没设置就用默认公网地址。注意：这些常量在模块被 import 时就已经算好了，测试时如果改环境变量，可能要重新加载模块或直接 monkeypatch 模块里的常量。

geocodificar(ciudad: str) -> dict

契约：输入城市名，返回规范化字典：

python
复制
下载
{"ciudad": "Valencia", "pais": "España", "lat": 39.47, "lon": -0.38}

内部要做的事：调 GEO_URL，把城市名作为查询参数，取 results 里的第一条，把 name/latitude/longitude/country 映射成 ciudad/lat/lon/pais。如果决定只限西班牙，可以传 countryCode="ES"。

obtener_meteorologia(lat: float, lon: float) -> dict

契约：返回至少：

python
复制
下载
{
    "temperatura_c": ...,
    "precipitacion_mm": ...,
    "codigo_tiempo": ...,
    "instante": ...
}

内部调 METEO_URL，请求参数里要有 current=temperature_2m,precipitation,weather_code 和 timezone=auto，然后从响应的 current 对象里取值并改键名。

obtener_lugares(lat, lon, tipo) -> list[dict]

查 Overpass，半径控制在 2–3 km，按 cultural / gastronomica / naturaleza / familiar 过滤，规范成 {nombre, categoria, lat, lon, fuente, ...}，最多 8–12 条。要处理 OSM 的 node 有 lat/lon，而 way/relation 可能只有 center 的情况。不能把用户输入直接拼进 Overpass QL，否则是注入风险。

cargar_fixture_lugares() -> list[dict]

这是老师已经写好的“离线测试工具”。它先找容器里的 /fixtures/puntos_demo.json，找不到再找项目根目录下的 fixtures/puntos_demo.json，读取 JSON 里的 "lugares" 列表。里面的地点是虚构的 DEMO 数据，UI 上要标识为 DEMO，不能冒充真实 OSM 数据。

三、geocodificar 必须处理哪些情况

建议按下面的顺序想，不要一上来就 results[0]：

1. 输入本身

ciudad 是 None、不是字符串、或者 strip() 后为空：直接报业务错误，不要发请求。

城市名里有空格、重音、&：用 params 字典交给 requests 编码，不要手动拼 URL。

2. 网络和 HTTP 层

必须设 timeout，比如 5 秒（按项目要求）。要处理：

requests.Timeout：超时；

requests.ConnectionError：连不上、DNS 失败；

requests.HTTPError：4xx/5xx，建议先 raise_for_status()；

其他 requests.RequestException：兜底；

response.json() 失败：返回的不是 JSON，捕获 ValueError / requests.exceptions.JSONDecodeError。

注意捕获顺序：先具体异常，再 RequestException 宽泛兜底，不要一个裸 except: 全吞掉。

3. results 为空或缺失

Open-Meteo 查不到时可能返回 {"results": []}，也可能没有 results 键。要写成：

取 data.get("results")；

如果是 None 或空列表，按项目约定处理：抛 ValueError/自定义“城市未找到”异常，或返回 None。关键是不能继续取 [0]，也不能伪造坐标。

因为函数注解是 -> dict，教育项目里更常见的是抛业务异常，由 Flask 路由映射成 404 或提示信息；如果项目约定允许 Optional[dict]，返回 None 也可以。测试要围绕你选的约定写。

4. 字段缺失

results[0] 里重点字段：

latitude、longitude：缺任何一个都不能默认 0，应报错；

name：缺失时可以用输入城市名兜底，但要明确；

country：缺失时可以用 country_code 兜底或报错，不要静默变空字符串；

类型转换：float(latitude)、float(longitude)，并检查范围：纬度 [-90, 90]，经度 [-180, 180]；

注意 0 是合法经纬度，不要用 if not lat 判断缺失。

5. 多结果和 countryCode

如果传 countryCode="ES"，API 只返回西班牙结果，过滤后为空就按“无结果”处理。如果不传，就要决定取第一条还是按人口/国家再筛。决策要写进测试，否则同名城市会导致结果不稳定。

验收断言示例

正常时断言返回键恰好是 ciudad/pais/lat/lon，lat/lon 是 float；无结果时断言抛指定异常；缺 latitude 时断言不返回 lat=0；HTTP 500 和 timeout 时断言被转换成项目统一异常。

四、obtener_meteorologia 的 current 怎么取

Open-Meteo 当前天气的响应大概长这样：

json
复制
下载
{
  "latitude": 39.47,
  "longitude": -0.38,
  "timezone": "Europe/Madrid",
  "current_units": {
    "temperature_2m": "°C",
    "precipitation": "mm",
    "weather_code": "wmo code"
  },
  "current": {
    "time": "2026-11-06T12:00",
    "interval": 900,
    "temperature_2m": 24.5,
    "precipitation": 0.0,
    "weather_code": 3
  }
}
请求参数

关键点：

python
复制
下载
params = {
    "latitude": lat,
    "longitude": lon,
    "current": "temperature_2m,precipitation,weather_code",
    "timezone": "auto",
}

current 是逗号分隔的字符串，不是列表。timezone=auto 让 current.time 按地点本地时区返回。还可以加 forecast_days=1 减小响应，但不是契约必需。

取值映射

temperatura_c ← current["temperature_2m"]

precipitacion_mm ← current["precipitation"]

codigo_tiempo ← current["weather_code"]

instante ← current["time"]

不要取 current_weather（旧字段），也不要从 hourly/daily 里猜当前值。

字段缺失怎么办

建议分层次：

整个 current 缺失或不是 dict：说明响应结构不对，抛业务异常，让上层返回 502/503，不要返回四个 None 假装成功。

current 存在但单个字段缺失或为 null：用 current.get(...)，返回的字典里保留键，值为 None，并记录日志。这样 UI 可以显示“暂无数据”。

如果项目测试要求四个字段必须是数值：那就在缺关键字段时抛异常。两种约定都行，但必须固定并写测试。

特别重要的坑：0 是合法值

温度 0°C、降水 0 mm、天气代码 0（晴）都是正常值。不要写：

python
复制
下载
temp = current.get("temperature_2m") or 0

这会把合法的 0 变成 0，也会把缺失变成 0，掩盖问题。应该判断 is None，并决定是返回 None 还是抛异常。测试一定要覆盖 temperature_2m=0, precipitation=0, weather_code=0 的情况。

类型和单位

温度、降水转 float；天气代码转 int；

可用 current_units 在测试里确认单位，但返回契约固定用 _c 和 _mm；

instante 保留 API 返回的字符串即可，测试不要过度断言具体时区格式，除非项目明确要求。

五、常见错误和测试思路
常见错误清单

忘记 timeout，或超时时间太短导致误报。

不调 raise_for_status()，把 500 错误页当 JSON 解析。

直接 response.json()["results"][0]，遇到空结果就 IndexError/KeyError。

手动拼 URL：城市名带空格、重音、& 就坏；应使用 params。

countryCode 参数名写成 country_code，或值写成小写 es。

天气字段名写错：temperature_2m、precipitation、weather_code、current。

用 or 给 0 值兜底，把合法 0 当缺失。

缺经纬度时默认 0，产生“几内亚湾”假坐标。

返回键名和契约不一致，比如 temperatura、precipitacion。

异常处理太宽，except Exception: pass，导致上层拿到脏数据。

测试只测正常路径，不测空结果、HTTP 错误、超时、缺字段。

测试依赖真实网络，CI 不稳定；应 mock requests.get。

模块常量在 import 时读取环境变量，测试里 monkeypatch.setenv 后没 reload，导致没生效。

cargar_fixture_lugares 的路径在本地/容器不同，测试时注意项目根目录和 /fixtures 的回退逻辑。

在 Overpass QL 里拼接用户输入（虽然本题前两个函数不涉及，但整个模块要注意）。

测试思路

建议用 
pytest
 + 
unittest.mock.patch("api_cl
ients.requests.get")
，或者自己写一个 
Fake
Response
：

有 
status_code
；

json()
 返回固定 payload；

raise_for_status()
 可以正常返回或抛 
requests.HTTPError
。

geocodificar
 测试
```

## Nota de honestidad

Esta consulta se realizó realmente en la ventana de DeepSeek. El estudiante debe contrastar la explicación con `docs/APIS_Y_CONTRATOS.md`, implementar A1 por su cuenta y anotar en su `MEMORIA_IA` qué aceptó, qué descartó y cómo lo verificó. No se debe presentar esta respuesta como código propio ni inventar pruebas no ejecutadas.
