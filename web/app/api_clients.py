"""Clientes HTTP de datos públicos. Se entregan los contratos, NO la solución."""
import json
import os
from pathlib import Path

import requests

GEO_URL = os.getenv("OPEN_METEO_GEO_URL", "https://geocoding-api.open-meteo.com/v1/search")
METEO_URL = os.getenv("OPEN_METEO_WEATHER_URL", "https://api.open-meteo.com/v1/forecast")
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

# Tiempo máximo de espera para no bloquear Flask si un proveedor tarda.
TIMEOUT_SEGUNDOS = float(os.getenv("API_TIMEOUT", "8"))
OVERPASS_TIMEOUT_SEGUNDOS = float(os.getenv("OVERPASS_TIMEOUT", "25"))

CATEGORIAS_OVERPASS = {
    "cultural": """
        nwr["tourism"~"^(museum|attraction|gallery)$"](around:2500,{lat},{lon});
        nwr["historic"~"^(monument|castle|memorial)$"](around:2500,{lat},{lon});
    """,
    "gastronomica": """
        nwr["amenity"~"^(restaurant|cafe|food_court)$"](around:2500,{lat},{lon});
    """,
    "naturaleza": """
        nwr["leisure"~"^(park|garden)$"](around:2500,{lat},{lon});
    """,
    "familiar": """
        nwr["tourism"~"^(attraction|zoo)$"](around:2500,{lat},{lon});
        nwr["leisure"~"^(park|playground)$"](around:2500,{lat},{lon});
    """,
}


def _extraer_categoria(tags: dict, tipo: str) -> str:
    """Extrae la subcategoría o etiqueta más representativa."""
    for clave in ("tourism", "historic", "amenity", "leisure"):
        if clave in tags:
            return str(tags[clave])
    return tipo


def _obtener_json(url: str, parametros: dict, timeout: float | None = None) -> dict:
    """GET con timeout y errores homogéneos para los tres proveedores."""
    try:
        respuesta = requests.get(
            url,
            params=parametros,
            timeout=timeout or TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
    except requests.Timeout as exc:
        raise RuntimeError("Tiempo de espera agotado al consultar un servicio externo.") from exc
    except requests.RequestException as exc:
        raise RuntimeError("No se pudo consultar un servicio externo.") from exc

    try:
        datos = respuesta.json()
    except ValueError as exc:
        raise RuntimeError("El servicio externo no devolvió un JSON válido.") from exc

    if not isinstance(datos, dict):
        raise RuntimeError("El servicio externo devolvió una respuesta inesperada.")
    return datos


def geocodificar(ciudad: str) -> dict:
    """Convierte una ciudad en coordenadas normalizadas.

    Contrato: {'ciudad': str, 'pais': str, 'lat': float, 'lon': float}.
    """
    if not isinstance(ciudad, str) or not ciudad.strip():
        raise ValueError("La ciudad es obligatoria.")
    ciudad = ciudad.strip()
    if len(ciudad) > 80:
        raise ValueError("La ciudad no puede superar los 80 caracteres.")

    datos = _obtener_json(
        GEO_URL,
        {
            "name": ciudad,
            "count": 1,
            "language": "es",
            "countryCode": "ES",
            "format": "json",
        },
    )

    resultados = datos.get("results")
    if not isinstance(resultados, list) or not resultados:
        raise ValueError(f"No se encontró la ciudad: {ciudad}")

    primero = resultados[0]
    try:
        lat = float(primero["latitude"])
        lon = float(primero["longitude"])
        nombre = str(primero["name"]).strip()
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("La geocodificación devolvió datos incompletos.") from exc

    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("La geocodificación devolvió coordenadas fuera de rango.")
    if not nombre:
        raise ValueError("La geocodificación no devolvió un nombre de ciudad.")

    pais = str(primero.get("country") or primero.get("country_code") or "").strip()
    if not pais:
        raise ValueError("La geocodificación no devolvió el país.")

    return {"ciudad": nombre, "pais": pais, "lat": lat, "lon": lon}


def obtener_meteorologia(lat: float, lon: float) -> dict:
    """Devuelve el tiempo actual normalizado para unas coordenadas.

    Contrato: {'temperatura_c': float, 'precipitacion_mm': float,
               'codigo_tiempo': int, 'instante': str}.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError) as exc:
        raise ValueError("La latitud y la longitud deben ser numéricas.") from exc

    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("La latitud o la longitud están fuera de rango.")

    datos = _obtener_json(
        METEO_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation,weather_code",
            "timezone": "auto",
        },
    )

    actual = datos.get("current")
    if not isinstance(actual, dict):
        raise RuntimeError("La respuesta meteorológica no contiene el bloque 'current'.")

    campos = ("temperature_2m", "precipitation", "weather_code", "time")
    faltantes = [campo for campo in campos if actual.get(campo) is None]
    if faltantes:
        raise RuntimeError(
            "La respuesta meteorológica está incompleta: faltan "
            + ", ".join(faltantes)
            + "."
        )

    try:
        temperatura = float(actual["temperature_2m"])
        precipitacion = float(actual["precipitation"])
        codigo = int(actual["weather_code"])
        instante = str(actual["time"])
    except (TypeError, ValueError) as exc:
        raise RuntimeError("La respuesta meteorológica tiene campos no numéricos.") from exc
    if not 0 <= codigo <= 99:
        raise RuntimeError("El código meteorológico WMO está fuera de rango.")
    return {
        "temperatura_c": temperatura,
        "precipitacion_mm": precipitacion,
        "codigo_tiempo": codigo,
        "instante": instante,
    }


def obtener_lugares(lat: float, lon: float, tipo: str) -> list[dict]:
    """Consulta Overpass/OSM en un radio de 2500m y devuelve lugares normalizados.

    Si Overpass falla por timeout, 429 o error de servidor, recurre a datos
    de prueba marcados obligatoriamente con demo=True.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError) as exc:
        raise ValueError("La latitud y la longitud deben ser numéricas.") from exc

    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("La latitud o la longitud están fuera de rango.")

    if not isinstance(tipo, str) or tipo.strip().lower() not in CATEGORIAS_OVERPASS:
        raise ValueError(
            f"Tipo de turismo '{tipo}' no válido. Permitidos: {', '.join(sorted(CATEGORIAS_OVERPASS.keys()))}."
        )

    tipo_normalizado = tipo.strip().lower()
    cuerpo_ql = CATEGORIAS_OVERPASS[tipo_normalizado].format(lat=lat, lon=lon)
    consulta_ql = f"[out:json][timeout:25];(\n{cuerpo_ql});\nout center 12;"

    headers = {
        "User-Agent": "CityPilotIA/1.0 (Classroom Workshop Project; https://github.com/tonyelos/citypilot-ia)"
    }

    try:
        respuesta = requests.post(
            OVERPASS_URL,
            data={"data": consulta_ql},
            headers=headers,
            timeout=OVERPASS_TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
        elementos = datos.get("elements", [])
    except (requests.RequestException, ValueError, KeyError):
        # Fallback de resiliencia: servidor Overpass caído, timeout o 429/504
        fixture = cargar_fixture_lugares()
        for lugar in fixture:
            lugar["demo"] = True
        return fixture

    lugares = []
    nombres_vistos = set()

    for elem in elementos:
        tags = elem.get("tags")
        if not isinstance(tags, dict):
            continue

        nombre = tags.get("name")
        if not nombre or not isinstance(nombre, str):
            continue
        nombre = nombre.strip()
        if not nombre or nombre.lower() in nombres_vistos:
            continue

        # Coordenadas: lat/lon directos en node; center en way/relation
        tipo_elem = elem.get("type")
        elem_lat = None
        elem_lon = None

        if tipo_elem == "node":
            elem_lat = elem.get("lat")
            elem_lon = elem.get("lon")
        elif tipo_elem in ("way", "relation"):
            centro = elem.get("center")
            if isinstance(centro, dict):
                elem_lat = centro.get("lat")
                elem_lon = centro.get("lon")

        try:
            if elem_lat is None or elem_lon is None:
                continue
            pos_lat = float(elem_lat)
            pos_lon = float(elem_lon)
        except (TypeError, ValueError):
            continue

        if not -90 <= pos_lat <= 90 or not -180 <= pos_lon <= 180:
            continue

        categoria = _extraer_categoria(tags, tipo_normalizado)

        lugares.append(
            {
                "nombre": nombre,
                "categoria": categoria,
                "lat": pos_lat,
                "lon": pos_lon,
                "fuente": "OpenStreetMap",
                "demo": False,
            }
        )
        nombres_vistos.add(nombre.lower())

        if len(lugares) >= 12:
            break

    # Si Overpass responde vacío, usamos el fixture avisando claramente de que es demo
    if not lugares:
        fixture = cargar_fixture_lugares()
        for lugar in fixture:
            lugar["demo"] = True
        return fixture

    return lugares


def cargar_fixture_lugares() -> list[dict]:
    """Utilidad entregada para simular Overpass durante pruebas sin Internet.

    Los lugares son FICTICIOS y deben identificarse como DEMO en la UI.
    """
    file_path = Path("/fixtures/puntos_demo.json")
    if not file_path.exists():
        file_path = Path(__file__).resolve().parents[2] / "fixtures" / "puntos_demo.json"
    return json.loads(file_path.read_text(encoding="utf-8"))["lugares"]
