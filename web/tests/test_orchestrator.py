"""Pruebas del orquestador compartido con dependencias simuladas."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import api_clients, db, llm, orchestrator  # noqa: E402

GEO = {"ciudad": "Valencia", "pais": "España", "lat": 39.47, "lon": -0.38}
METEO = {
    "temperatura_c": 19.5,
    "precipitacion_mm": 0.0,
    "codigo_tiempo": 1,
    "instante": "2026-11-06T09:00",
}
LUGARES = [
    {
        "nombre": "Museo de ejemplo",
        "categoria": "museum",
        "lat": 39.47,
        "lon": -0.38,
        "fuente": "OpenStreetMap",
        "demo": False,
    }
]


def _montar_dependencias(monkeypatch, lugares=None, fallo_lugares=None):
    monkeypatch.setattr(api_clients, "geocodificar", lambda ciudad: GEO)
    monkeypatch.setattr(api_clients, "obtener_meteorologia", lambda lat, lon: METEO)
    if fallo_lugares:
        def lanzar(*args, **kwargs):
            raise fallo_lugares
        monkeypatch.setattr(api_clients, "obtener_lugares", lanzar)
    else:
        monkeypatch.setattr(api_clients, "obtener_lugares", lambda lat, lon, tipo: lugares or LUGARES)
    monkeypatch.setattr(api_clients, "cargar_fixture_lugares", lambda: LUGARES)
    monkeypatch.setattr(llm, "generar_itinerario", lambda contexto: ("Ruta de prueba", "prompt de prueba"))
    monkeypatch.setattr(db, "guardar_solicitud", lambda registro: 42)


def test_procesar_solicitud_feliz(monkeypatch):
    _montar_dependencias(monkeypatch)

    resultado = orchestrator.procesar_solicitud("  Valencia  ", "cultural", 4, "con niños")

    assert resultado["solicitud_id"] == 42
    assert resultado["ciudad"] == "Valencia"
    assert resultado["tipo_turismo"] == "cultural"
    assert resultado["duracion_horas"] == 4
    assert resultado["preferencias"] == "con niños"
    assert resultado["meteorologia"] == METEO
    assert resultado["lugares"] == LUGARES
    assert resultado["itinerario"] == "Ruta de prueba"
    assert resultado["modo_demo"] is False
    assert resultado["duracion_ms"] >= 0


def test_solicitud_invalida_no_consume_servicios(monkeypatch):
    def no_debe_llamarse(*args, **kwargs):
        raise AssertionError("No se debe llamar a un proveedor con entrada inválida")

    monkeypatch.setattr(api_clients, "geocodificar", no_debe_llamarse)
    monkeypatch.setattr(api_clients, "obtener_meteorologia", no_debe_llamarse)
    monkeypatch.setattr(api_clients, "obtener_lugares", no_debe_llamarse)
    monkeypatch.setattr(llm, "generar_itinerario", no_debe_llamarse)
    monkeypatch.setattr(db, "guardar_solicitud", no_debe_llamarse)

    with pytest.raises(ValueError, match="tipo de turismo"):
        orchestrator.procesar_solicitud("Valencia", "invalido", 4, "")


def test_overpass_fallido_usa_fixture_y_marca_demo(monkeypatch):
    _montar_dependencias(monkeypatch, fallo_lugares=RuntimeError("Overpass 504"))

    resultado = orchestrator.procesar_solicitud("Valencia", "cultural", 2, "")

    assert resultado["modo_demo"] is True
    assert resultado["lugares"] == LUGARES
