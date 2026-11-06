"""Pruebas para el cliente de OpenStreetMap / Overpass (PR 2 - Estudiante 3)."""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import api_clients  # noqa: E402


class RespuestaFalsa:
    """Mock mínimo para simular respuestas de requests.Response."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_obtener_lugares_normaliza_nodos_y_ways(monkeypatch):
    llamada = {}

    def post_falso(url, data=None, headers=None, timeout=None):
        llamada.update(url=url, data=data, headers=headers, timeout=timeout)
        return RespuestaFalsa(
            {
                "elements": [
                    {
                        "type": "node",
                        "id": 1,
                        "lat": 39.47,
                        "lon": -0.38,
                        "tags": {"name": "Museo Bellas Artes", "tourism": "museum"},
                    },
                    {
                        "type": "way",
                        "id": 2,
                        "center": {"lat": 39.48, "lon": -0.37},
                        "tags": {"name": "Torres de Serranos", "historic": "monument"},
                    },
                    {
                        # Elemento sin nombre: debe ser descartado
                        "type": "node",
                        "id": 3,
                        "lat": 39.49,
                        "lon": -0.36,
                        "tags": {"tourism": "attraction"},
                    },
                    {
                        # Duplicado: debe ser descartado
                        "type": "node",
                        "id": 4,
                        "lat": 39.471,
                        "lon": -0.381,
                        "tags": {"name": "Museo Bellas Artes", "tourism": "museum"},
                    },
                ]
            }
        )

    monkeypatch.setattr(api_clients.requests, "post", post_falso)

    resultado = api_clients.obtener_lugares(39.47, -0.38, "cultural")

    assert len(resultado) == 2
    assert resultado[0] == {
        "nombre": "Museo Bellas Artes",
        "categoria": "museum",
        "lat": pytest.approx(39.47),
        "lon": pytest.approx(-0.38),
        "fuente": "OpenStreetMap",
        "demo": False,
    }
    assert resultado[1] == {
        "nombre": "Torres de Serranos",
        "categoria": "monument",
        "lat": pytest.approx(39.48),
        "lon": pytest.approx(-0.37),
        "fuente": "OpenStreetMap",
        "demo": False,
    }
    # Verificamos que no se inyectan datos libres en la QL
    assert "tourism" in llamada["data"]["data"]
    assert "around:2500,39.47,-0.38" in llamada["data"]["data"]


def test_obtener_lugares_fallback_fixture_en_error(monkeypatch):
    def post_timeout(*args, **kwargs):
        raise requests.Timeout("Timeout agotado en servidor Overpass")

    monkeypatch.setattr(api_clients.requests, "post", post_timeout)

    resultado = api_clients.obtener_lugares(39.47, -0.38, "naturaleza")

    # Debe devolver la lista del fixture y todos con demo=True
    assert len(resultado) > 0
    assert all(lugar["demo"] is True for lugar in resultado)


def test_obtener_lugares_rechaza_tipo_invalido():
    with pytest.raises(ValueError, match="no válido"):
        api_clients.obtener_lugares(39.47, -0.38, "tipo_inventado_sql_injection")
