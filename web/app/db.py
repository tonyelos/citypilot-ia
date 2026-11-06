"""Acceso a PostgreSQL. Conexión mínima dada; funciones de negocio pendientes."""
import json
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "")
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None


def ping_db():
    if engine is None:
        raise RuntimeError("Falta DATABASE_URL")
    with engine.connect() as conn:
        return conn.execute(text("SELECT 1")).scalar_one()


def guardar_solicitud(registro: dict) -> int:
    """Inserta una solicitud en PostgreSQL de forma parametrizada y devuelve su ID."""
    if engine is None:
        raise RuntimeError("Falta DATABASE_URL")

    if "duracion_horas" not in registro or registro["duracion_horas"] is None:
        raise ValueError("El campo 'duracion_horas' es obligatorio.")
    try:
        duracion_horas = int(registro["duracion_horas"])
    except (TypeError, ValueError) as exc:
        raise ValueError("El campo 'duracion_horas' debe ser numérico.") from exc
    if duracion_horas not in (2, 4, 6):
        raise ValueError("La duración debe ser 2, 4 o 6 horas.")

    # Serialización segura a JSONB para estructuras complejas
    meteorologia_raw = registro.get("meteorologia") or {}
    lugares_raw = registro.get("lugares") or []

    meteorologia_json = (
        json.dumps(meteorologia_raw, ensure_ascii=False)
        if isinstance(meteorologia_raw, (dict, list))
        else str(meteorologia_raw)
    )
    lugares_json = (
        json.dumps(lugares_raw, ensure_ascii=False)
        if isinstance(lugares_raw, list)
        else str(lugares_raw)
    )

    consulta = text(
        """
        INSERT INTO solicitudes (
            ciudad, pais, tipo_turismo, duracion_horas, preferencias,
            latitud, longitud, meteorologia, lugares, prompt_usado,
            itinerario, estado, duracion_ms, error_resumido,
            modo_demo, modo_modelo
        ) VALUES (
            :ciudad, :pais, :tipo_turismo, :duracion_horas, :preferencias,
            :latitud, :longitud, CAST(:meteorologia AS jsonb), CAST(:lugares AS jsonb), :prompt_usado,
            :itinerario, :estado, :duracion_ms, :error_resumido,
            :modo_demo, :modo_modelo
        )
        RETURNING id;
        """
    )

    params = {
        "ciudad": str(registro.get("ciudad", "")),
        "pais": registro.get("pais"),
        "tipo_turismo": str(registro.get("tipo_turismo", "")),
        "duracion_horas": duracion_horas,
        "preferencias": str(registro.get("preferencias", "")),
        "latitud": float(registro["latitud"]) if registro.get("latitud") is not None else None,
        "longitud": float(registro["longitud"]) if registro.get("longitud") is not None else None,
        "meteorologia": meteorologia_json,
        "lugares": lugares_json,
        "prompt_usado": registro.get("prompt_usado"),
        "itinerario": registro.get("itinerario"),
        "estado": str(registro.get("estado", "pendiente")),
        "duracion_ms": int(registro["duracion_ms"]) if registro.get("duracion_ms") is not None else None,
        "error_resumido": registro.get("error_resumido"),
        "modo_demo": bool(registro.get("modo_demo", False)),
        "modo_modelo": registro.get("modo_modelo"),
    }

    with engine.begin() as conn:
        nuevo_id = conn.execute(consulta, params).scalar_one()
    return int(nuevo_id)


def obtener_estadisticas() -> dict:
    """Devuelve métricas agregadas de la tabla solicitudes."""
    if engine is None:
        raise RuntimeError("Falta DATABASE_URL")

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM solicitudes")).scalar_one() or 0
        ciudades_distintas = (
            conn.execute(text("SELECT COUNT(DISTINCT LOWER(ciudad)) FROM solicitudes")).scalar_one() or 0
        )
        errores = (
            conn.execute(text("SELECT COUNT(*) FROM solicitudes WHERE estado = 'error'")).scalar_one() or 0
        )

        filas_ciudades = conn.execute(
            text(
                """
                SELECT INITCAP(ciudad) AS ciudad, COUNT(*) AS total
                FROM solicitudes
                GROUP BY INITCAP(ciudad)
                ORDER BY total DESC, ciudad ASC
                LIMIT 5;
                """
            )
        ).mappings().all()
        top_ciudades = [dict(fila) for fila in filas_ciudades]

        filas_tipos = conn.execute(
            text(
                """
                SELECT tipo_turismo, COUNT(*) AS total
                FROM solicitudes
                GROUP BY tipo_turismo
                ORDER BY total DESC;
                """
            )
        ).mappings().all()
        por_tipo = [dict(fila) for fila in filas_tipos]

    return {
        "total": total,
        "ciudades_distintas": ciudades_distintas,
        "errores": errores,
        "top_ciudades": top_ciudades,
        "por_tipo": por_tipo,
    }


def obtener_ultimas_solicitudes(limite: int = 8) -> list[dict]:
    """Devuelve las últimas solicitudes registradas sin mostrar secretos."""
    if engine is None:
        raise RuntimeError("Falta DATABASE_URL")

    consulta = text(
        """
        SELECT id, fecha, ciudad, pais, tipo_turismo, duracion_horas,
               estado, modo_demo, duracion_ms, error_resumido
        FROM solicitudes
        ORDER BY fecha DESC
        LIMIT :limite;
        """
    )
    with engine.connect() as conn:
        filas = conn.execute(consulta, {"limite": limite}).mappings().all()
        return [dict(fila) for fila in filas]
