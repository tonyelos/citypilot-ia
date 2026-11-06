"""Rutas del servicio Flask. Esqueleto intencionalmente incompleto."""
from flask import Flask, jsonify, render_template, request, send_file

from app.analytics import generar_grafico_ciudades
from app.db import obtener_estadisticas, obtener_ultimas_solicitudes, ping_db
from app.orchestrator import procesar_solicitud


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def inicio():
        return render_template("index.html", valores={})

    @app.get("/api/health")
    def health():
        # Punto de salud proporcionado para verificar Compose y PostgreSQL.
        try:
            ping_db()
            return jsonify(servicio="citypilot", estado="ok", db="ok")
        except Exception:
            return jsonify(servicio="citypilot", estado="degradado", db="error"), 503

    @app.post("/planificar")
    def planificar_html():
        try:
            resultado = procesar_solicitud(
                ciudad=request.form.get("ciudad", ""),
                tipo_turismo=request.form.get("tipo_turismo", ""),
                duracion_horas=request.form.get("duracion_horas", ""),
                preferencias=request.form.get("preferencias", ""),
            )
        except ValueError as exc:
            return render_template("index.html", error=str(exc), valores=request.form), 400
        except Exception:
            # No mostrar el detalle técnico al usuario; queda en el log.
            app.logger.exception("Fallo al procesar la solicitud")
            return (
                render_template(
                    "index.html",
                    error="No se pudo completar la planificación. Inténtalo de nuevo más tarde.",
                    valores=request.form,
                ),
                502,
            )
        return render_template("resultado.html", **resultado)

    @app.post("/api/planificar")
    def planificar_api():
        # TODO(ALUMNADO): leer JSON, usar EL MISMO orquestador y devolver JSON.
        # Nunca duplicar la lógica de datos externos en las dos rutas.
        return jsonify(error="Pendiente: API propia"), 501

    @app.get("/analitica")
    def analitica():
        try:
            stats = obtener_estadisticas()
            ultimas = obtener_ultimas_solicitudes(limite=8)
            totales = {
                "total": stats["total"],
                "ciudades": stats["ciudades_distintas"],
                "errores": stats["errores"],
            }
            return render_template(
                "analitica.html",
                totales=totales,
                top_ciudades=stats["top_ciudades"],
                ultimas=ultimas,
            )
        except Exception as exc:
            app.logger.warning("No se pudo cargar la analítica: %s", exc)
            return render_template(
                "analitica.html",
                totales={"total": 0, "ciudades": 0, "errores": 0},
                top_ciudades=[],
                ultimas=[],
            )

    @app.get("/analitica/grafico.png")
    def grafico():
        try:
            stats = obtener_estadisticas()
            buf = generar_grafico_ciudades(stats.get("top_ciudades", []))
            return send_file(buf, mimetype="image/png")
        except Exception as exc:
            app.logger.warning("No se pudo generar la gráfica: %s", exc)
            buf = generar_grafico_ciudades([])
            return send_file(buf, mimetype="image/png")

    @app.get("/api/estadisticas")
    def estadisticas_api():
        try:
            stats = obtener_estadisticas()
            return jsonify(stats)
        except Exception as exc:
            app.logger.exception("Fallo al consultar estadísticas")
            return jsonify(error="No se pudieron obtener las estadísticas"), 500

    return app


app = create_app()
