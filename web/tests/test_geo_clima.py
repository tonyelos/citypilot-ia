"""Pruebas de A1: geocodificación y meteorología con HTTP simulado."""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import api_clients  # noqa: E402


class RespuestaFalsa:
    """Doble de prueba mínimo de requests.Response."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_geocodificar_normaliza_y_filtra_espana(monkeypatch):
    llamada = {}

    def get_falso(url, params=None, timeout=None):
        llamada.update(url=url, params=params, timeout=timeout)
        return RespuestaFalsa(
            {
                "results": [
                    {
                        "name": "Valencia",
                        "country": "España",
                        "latitude": 39.4699,
                        "longitude": -0.3763,
                    }
                ]
            }
        )

    monkeypatch.setattr(api_clients.requests, "get", get_falso)

    resultado = api_clients.geocodificar("  Valencia  ")

    assert resultado == {
        "ciudad": "Valencia",
        "pais": "España",
        "lat": pytest.approx(39.4699),
        "lon": pytest.approx(-0.3763),
    }
    assert llamada["params"]["countryCode"] == "ES"
    assert llamada["params"]["name"] == "Valencia"
    assert llamada["timeout"] == api_clients.TIMEOUT_SEGUNDOS


def test_geocodificar_sin_resultados_lanza_valueerror(monkeypatch):
    monkeypatch.setattr(
        api_clients.requests,
        "get",
        lambda *args, **kwargs: RespuestaFalsa({"results": []}),
    )

    with pytest.raises(ValueError, match="No se encontró la ciudad"):
        api_clients.geocodificar("Ciudad Inventada")


def test_geocodificar_timeout_se_convierte_en_runtimeerror(monkeypatch):
    def get_timeout(*args, **kwargs):
        raise requests.Timeout("agotado")

    monkeypatch.setattr(api_clients.requests, "get", get_timeout)

    with pytest.raises(RuntimeError, match="Tiempo de espera"):
        api_clients.geocodificar("Valencia")


def test_meteorologia_mapea_el_bloque_current(monkeypatch):
    monkeypatch.setattr(
        api_clients.requests,
        "get",
        lambda *args, **kwargs: RespuestaFalsa(
            {
                "current": {
                    "time": "2026-11-06T09:00",
                    "temperature_2m": 19.5,
                    "precipitation": 0.0,
                    "weather_code": 3,
                }
            }
        ),
    )

    resultado = api_clients.obtener_meteorologia(39.47, -0.38)

    assert resultado == {
        "temperatura_c": 19.5,
        "precipitacion_mm": 0.0,
        "codigo_tiempo": 3,
        "instante": "2026-11-06T09:00",
    }


def test_meteorologia_sin_current_lanza_error_controlado(monkeypatch):
    monkeypatch.setattr(
        api_clients.requests,
        "get",
        lambda *args, **kwargs: RespuestaFalsa({"hourly": {}}),
    )

    with pytest.raises(RuntimeError, match="current"):
        api_clients.obtener_meteorologia(39.47, -0.38)


def test_meteorologia_con_campo_ausente_no_lo_convierte_en_cero(monkeypatch):
    monkeypatch.setattr(
        api_clients.requests,
        "get",
        lambda *args, **kwargs: RespuestaFalsa(
            {
                "current": {
                    "time": "2026-11-06T09:00",
                    "temperature_2m": 19.5,
                    "weather_code": 3,
                }
            }
        ),
    )

    with pytest.raises(RuntimeError, match="precipitation"):
        api_clients.obtener_meteorologia(39.47, -0.38)


def test_meteorologia_rechaza_codigo_wmo_fuera_de_rango(monkeypatch):
    monkeypatch.setattr(
        api_clients.requests,
        "get",
        lambda *args, **kwargs: RespuestaFalsa(
            {
                "current": {
                    "time": "2026-11-06T09:00",
                    "temperature_2m": 19.5,
                    "precipitation": 0.0,
                    "weather_code": 999,
                }
            }
        ),
    )

    with pytest.raises(RuntimeError, match="WMO"):
        api_clients.obtener_meteorologia(39.47, -0.38)
