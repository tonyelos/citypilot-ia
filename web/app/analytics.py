"""Generación de gráficos estadísticos en memoria sin JavaScript."""
import io
import matplotlib
matplotlib.use("Agg")  # Backend no interactivo sin entorno gráfico
import matplotlib.pyplot as plt


def generar_grafico_ciudades(top_ciudades: list[dict]) -> io.BytesIO:
    """Genera un gráfico de barras horizontales con las ciudades más consultadas."""
    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=100)

    if not top_ciudades:
        ax.text(
            0.5,
            0.5,
            "Sin datos suficientes aún",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=12,
            color="#666666",
        )
        ax.axis("off")
    else:
        ciudades = [str(item["ciudad"]) for item in reversed(top_ciudades)]
        totales = [int(item["total"]) for item in reversed(top_ciudades)]

        barras = ax.barh(ciudades, totales, color="#2b6cb0", height=0.55)
        ax.set_title("Ciudades más consultadas", fontsize=12, pad=10, weight="bold")
        ax.set_xlabel("Número de solicitudes", fontsize=10)
        ax.grid(axis="x", linestyle="--", alpha=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Etiquetas con el valor en cada barra
        for barra in barras:
            ancho = barra.get_width()
            ax.annotate(
                f"{ancho}",
                xy=(ancho, barra.get_y() + barra.get_height() / 2),
                xytext=(5, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=9,
            )

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer
