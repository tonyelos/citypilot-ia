"""Punto ÚNICO de integración para web y API JSON. Pendiente del alumnado."""
import logging
import time

from app import api_clients, db, llm

TIPOS_VALIDOS = {"cultural", "gastronomica", "naturaleza", "familiar"}
DURACIONES_VALIDAS = {2, 4, 6}
MAX_CIUDAD = 80
MAX_PREFERENCIAS = 200

logger = logging.getLogger(__name__)


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
    except (RuntimeError, ValueError, NotImplementedError) as exc:
        # Fallback explícito para demostrar el flujo si Overpass no responde.
        logger.warning("Overpass no disponible; se usa el fixture demo: %s", exc)
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
