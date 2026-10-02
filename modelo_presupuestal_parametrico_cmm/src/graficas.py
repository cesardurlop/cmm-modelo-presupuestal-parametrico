from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def arquitectura_modelo(salida: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axis("off")

    cajas = [
        (0.08, 0.72, "Demanda y producción\npor denominación"),
        (0.38, 0.72, "Capacidad, personal\ny reglas operativas"),
        (0.68, 0.72, "Metales y variables\nmacroeconómicas"),
        (0.68, 0.45, "Modelos de precios\nUnivariados + regresión"),
        (0.38, 0.30, "Modelo presupuestal\nparamétrico"),
        (0.10, 0.08, "Presupuesto\nmensual"),
        (0.38, 0.08, "Presupuesto\nanual"),
        (0.66, 0.08, "Escenarios y\naños posteriores"),
    ]

    for x, y, txt in cajas:
        ax.text(
            x, y, txt,
            ha="center", va="center",
            fontsize=11,
            bbox=dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="black"),
            transform=ax.transAxes,
        )

    flechas = [
        ((0.13, 0.67), (0.34, 0.36)),
        ((0.40, 0.67), (0.40, 0.36)),
        ((0.68, 0.67), (0.68, 0.51)),
        ((0.65, 0.43), (0.46, 0.33)),
        ((0.36, 0.25), (0.15, 0.13)),
        ((0.40, 0.25), (0.40, 0.13)),
        ((0.44, 0.25), (0.66, 0.13)),
    ]
    for (x1, y1), (x2, y2) in flechas:
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", lw=1.5),
            xycoords=ax.transAxes,
        )

    ax.set_title("Arquitectura general del modelo presupuestal paramétrico", fontsize=14)
    fig.tight_layout()
    fig.savefig(salida, dpi=180, bbox_inches="tight")
    plt.close(fig)


def pronostico_rodante(salida: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.axis("off")

    textos = [
        "Datos observados\nhasta año y",
        "Recalibración\nde modelos",
        "Pronóstico\ny+1 … y+h",
        "Datos reales\nobservados",
        "Nueva\nrecalibración",
    ]
    xs = [0.08, 0.28, 0.50, 0.72, 0.91]

    for x, txt in zip(xs, textos):
        ax.text(
            x, 0.52, txt,
            ha="center", va="center",
            fontsize=11,
            bbox=dict(boxstyle="round,pad=0.55", facecolor="white", edgecolor="black"),
            transform=ax.transAxes,
        )

    for a, b in zip(xs[:-1], xs[1:]):
        ax.annotate(
            "", xy=(b - 0.07, 0.52), xytext=(a + 0.07, 0.52),
            arrowprops=dict(arrowstyle="->", lw=1.5),
            xycoords=ax.transAxes,
        )

    ax.annotate(
        "El proceso se repite conforme se incorpora nueva información",
        xy=(0.50, 0.20), ha="center", va="center",
        fontsize=10, xycoords=ax.transAxes,
    )

    ax.set_title("Esquema de pronóstico rodante y actualización anual", fontsize=14)
    fig.tight_layout()
    fig.savefig(salida, dpi=180, bbox_inches="tight")
    plt.close(fig)


def sensibilidad_presupuesto(df: pd.DataFrame, salida: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(
        df["variacion_produccion_pct"],
        df["presupuesto_anual"] / 1e9,
        marker="o",
    )
    ax.set_xlabel("Variación de producción (%)")
    ax.set_ylabel("Presupuesto anual (miles de millones MXN)")
    ax.set_title("Sensibilidad del presupuesto ante variaciones en producción")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(salida, dpi=180)
    plt.close(fig)


def composicion_presupuesto(composicion: pd.Series, salida: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    valores = composicion / 1e9
    ax.bar(valores.index, valores.values)
    ax.set_ylabel("Miles de millones MXN")
    ax.set_title("Composición del presupuesto anual")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(salida, dpi=180)
    plt.close(fig)


def pronosticos_cuatro_metales(
    base: pd.DataFrame,
    pronosticos: pd.DataFrame,
    salida: Path,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, metal in zip(axes.ravel(), ["aluminio", "cobre", "niquel", "zinc"]):
        hist = base[metal].loc["2022-01-01":]
        ax.plot(hist.index, hist.values, label="Histórico")
        ax.plot(pronosticos.index, pronosticos[metal].values, label="Pronóstico 2025")
        ax.set_title(metal.capitalize())
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.suptitle("Pronósticos finales seleccionados para los cuatro metales")
    fig.tight_layout()
    fig.savefig(salida, dpi=180)
    plt.close(fig)


def contraste_aluminio_cobre(
    base: pd.DataFrame,
    resultados_univariados: dict,
    resultado_multivariado: dict,
    salida: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for ax, metal in zip(axes, ["aluminio", "cobre"]):
        real = resultados_univariados[metal]["prueba_real"]
        uni = resultados_univariados[metal]["validacion"]
        multi = resultado_multivariado["validaciones"][metal]["regresion"]

        ax.plot(real.index, real.values, label="Real", linewidth=2)
        ax.plot(uni.index, uni.values, label="Univariado")
        ax.plot(multi.index, multi.values, label="Regresión múltiple")
        ax.set_title(metal.capitalize())
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)

    fig.suptitle("Contraste univariado vs. multivariado, validación 2023–2024")
    fig.tight_layout()
    fig.savefig(salida, dpi=180)
    plt.close(fig)


def escenarios_presupuesto(df: pd.DataFrame, salida: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df["escenario"], df["presupuesto_anual"] / 1e9)
    ax.set_ylabel("Miles de millones MXN")
    ax.set_title("Escenarios del presupuesto")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(salida, dpi=180)
    plt.close(fig)
