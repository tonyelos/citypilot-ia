"""Pruebas de la ruta HTML /planificar con el orquestador simulado."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402


RESULTADO = {
    "solicitud_id": 7,
    "ciudad": "Valencia",
    "pais": "España",
    "tipo_turismo": "cultural",
    "duracion_horas": 4,
    "preferencias": "con niños",
    "lat": 39.47,
    "lon": -0.38,
    "meteorologia": {
        "temperatura_c": 19.5,
        "precipitacion_mm": 0.0,
        "codigo_tiempo": 1,
        "instante": "2026-11-06T09:00",
    },
    "lugares": [
        {
            "nombre": "Museo de ejemplo",
            "categoria": "museum",
            "lat": 39.47,
            "lon": -0.38,
            "fuente": "OpenStreetMap",
            "demo": False,
        }
    ],
    "itinerario": "Ruta de prueba",
    "modo_demo": False,
    "modo_modelo": "mock",
    "duracion_ms": 12,
}


def test_planificar_html_renderiza_resultado(monkeypatch):
    monkeypatch.setattr("app.main.procesar_solicitud", lambda **kwargs: RESULTADO)

    cliente = create_app().test_client()
    respuesta = cliente.post(
        "/planificar",
        data={
            "ciudad": "Valencia",
            "tipo_turismo": "cultural",
            "duracion_horas": "4",
            "preferencias": "con niños",
        },
    )

    assert respuesta.status_code == 200
    assert b"Valencia" in respuesta.data
    assert b"Itinerario" in respuesta.data


def test_planificar_html_devuelve_400_si_validacion_falla(monkeypatch):
    def fallar(**kwargs):
        raise ValueError("La ciudad es obligatoria.")

    monkeypatch.setattr("app.main.procesar_solicitud", fallar)

    cliente = create_app().test_client()
    respuesta = cliente.post(
        "/planificar",
        data={"ciudad": "", "tipo_turismo": "cultural", "duracion_horas": "4"},
    )

    assert respuesta.status_code == 400
    assert b"La ciudad es obligatoria" in respuesta.data
