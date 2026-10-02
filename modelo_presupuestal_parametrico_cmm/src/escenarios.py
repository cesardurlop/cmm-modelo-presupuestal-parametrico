from __future__ import annotations

import pandas as pd

from .presupuesto import calcular_presupuesto


def calcular_escenarios(
    demanda_base: pd.DataFrame,
    precios_base: pd.DataFrame,
    parametros,
    escenarios: dict,
) -> pd.DataFrame:
    """
    Los factores deben ser definidos y justificados por el usuario.
    Este módulo no inventa supuestos: simplemente propaga los que se le indiquen.
    """
    filas = []

    for nombre, cfg in escenarios.items():
        demanda = demanda_base * float(cfg["factor_produccion"])
        precios = precios_base * float(cfg["factor_metales"])

        # Ajuste del TC mediante una copia temporal de la serie.
        tc = pd.Series(
            parametros.tc_base * float(cfg["factor_tipo_cambio"]),
            index=demanda.index,
        )

        presupuesto = calcular_presupuesto(
            demanda=demanda,
            precios_metales=precios,
            parametros=parametros,
            tc_mensual=tc,
            factor_energia=float(cfg["factor_energia"]),
        )

        filas.append({
            "escenario": nombre,
            "presupuesto_anual": presupuesto["TOTAL PRESUPUESTO"].sum(),
            "piezas_anuales": demanda.sum().sum(),
            **cfg,
        })

    return pd.DataFrame(filas)
