"""Pruebas para persistencia en PostgreSQL y analítica (PR 4 - Estudiante 3)."""
import io
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import analytics, db, main  # noqa: E402


@pytest.fixture
def cliente_flask():
    app = main.create_app()
    app.config["TESTING"] = True
    with app.test_client() as cliente:
        yield cliente


def test_guardar_solicitud_valida_duracion_horas():
    with pytest.raises(ValueError, match="obligatorio"):
        db.guardar_solicitud({"ciudad": "Valencia", "tipo_turismo": "cultural"})

    with pytest.raises(ValueError, match="2, 4 o 6"):
        db.guardar_solicitud(
            {"ciudad": "Valencia", "tipo_turismo": "cultural", "duracion_horas": 3}
        )


def test_guardar_solicitud_y_obtener_estadisticas_aislado():
    # Usar nombre de ciudad único para aislar completamente el test
    ciudad_test = f"CiudadTest_{uuid.uuid4().hex[:8]}"

    registro = {
        "ciudad": ciudad_test,
        "pais": "España",
        "tipo_turismo": "cultural",
        "duracion_horas": 4,
        "preferencias": "visitar museos de arte",
        "latitud": 39.4699,
        "longitud": -0.3763,
        "meteorologia": {"temperatura_c": 18.5, "precipitacion_mm": 0.0},
        "lugares": [{"nombre": "Museo Bellas Artes", "categoria": "museum"}],
        "prompt_usado": "Generar ruta cultural",
        "itinerario": "10:00 Museo Bellas Artes",
        "estado": "ok",
        "duracion_ms": 120,
        "error_resumido": None,
        "modo_demo": False,
        "modo_modelo": "mock",
    }

    nuevo_id = None
    try:
        nuevo_id = db.guardar_solicitud(registro)
        assert isinstance(nuevo_id, int)
        assert nuevo_id > 0

        stats = db.obtener_estadisticas()
        assert stats["total"] >= 1
        assert stats["ciudades_distintas"] >= 1

        ultimas = db.obtener_ultimas_solicitudes(limite=50)
        coincidencias = [s for s in ultimas if s["id"] == nuevo_id]
        assert len(coincidencias) == 1
        fila = coincidencias[0]
        assert fila["ciudad"] == ciudad_test
        assert fila["duracion_horas"] == 4
        assert "prompt_usado" not in fila  # Garantizamos que no se filtran secretos/prompts
    finally:
        # Limpieza estricta para no dejar datos residuales en la BD compartida
        if nuevo_id and db.engine:
            with db.engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM solicitudes WHERE id = :id"),
                    {"id": nuevo_id},
                )


def test_generar_grafico_ciudades_retorna_png():
    datos = [
        {"ciudad": "Valencia", "total": 5},
        {"ciudad": "Madrid", "total": 3},
    ]
    buf = analytics.generar_grafico_ciudades(datos)
    assert isinstance(buf, io.BytesIO)
    contenido = buf.getvalue()
    # Cabecera mágica de archivo PNG: \x89PNG\r\n\x1a\n
    assert contenido.startswith(b"\x89PNG\r\n\x1a\n")


def test_rutas_analitica_responden_ok(cliente_flask):
    resp_html = cliente_flask.get("/analitica")
    assert resp_html.status_code == 200
    assert "Peticiones totales" in resp_html.get_data(as_text=True)

    resp_png = cliente_flask.get("/analitica/grafico.png")
    assert resp_png.status_code == 200
    assert resp_png.mimetype == "image/png"
    assert resp_png.data.startswith(b"\x89PNG\r\n\x1a\n")

    resp_api = cliente_flask.get("/api/estadisticas")
    assert resp_api.status_code == 200
    datos = resp_api.get_json()
    assert "total" in datos
    assert "ciudades_distintas" in datos
