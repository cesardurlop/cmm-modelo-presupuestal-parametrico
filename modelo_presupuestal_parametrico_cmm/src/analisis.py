from __future__ import annotations

import pandas as pd

from .presupuesto import calcular_presupuesto


def comparar_fuentes_precio(
    resultados_univariados: dict,
    resultado_multivariado: dict,
    modo: str,
    seleccion_manual: dict,
) -> pd.DataFrame:
    metricas_multi = resultado_multivariado["metricas"].set_index("metal")
    filas = []

    for metal, ru in resultados_univariados.items():
        rmse_u = float(ru["metricas_ganador"]["RMSE"])
        rmse_m = float(metricas_multi.loc[metal, "RMSE"])

        if modo == "auto_rmse":
            fuente = "univariado" if rmse_u <= rmse_m else "multivariado"
        elif modo == "manual":
            fuente = seleccion_manual[metal]
        else:
            fuente = "univariado"

        filas.append({
            "metal": metal,
            "modelo_univariado": ru["modelo_ganador"],
            "RMSE_univariado": rmse_u,
            "RMSE_multivariado": rmse_m,
            "fuente_presupuesto": fuente,
        })

    return pd.DataFrame(filas)


def construir_pronosticos_seleccionados(
    resultados_univariados: dict,
    resultado_multivariado: dict,
    comparacion: pd.DataFrame,
) -> pd.DataFrame:
    fechas = next(iter(resultados_univariados.values()))["pronostico"].index
    out = pd.DataFrame(index=fechas)

    multi = resultado_multivariado["pronosticos"]

    for _, fila in comparacion.iterrows():
        metal = fila["metal"]
        if fila["fuente_presupuesto"] == "multivariado":
            out[metal] = multi[metal].values
        else:
            out[metal] = resultados_univariados[metal]["pronostico"].values

    return out


def sensibilidad_produccion(
    demanda_base: pd.DataFrame,
    precios: pd.DataFrame,
    parametros,
    factores_variacion: list[float],
) -> pd.DataFrame:
    filas = []

    for variacion in factores_variacion:
        factor = 1.0 + variacion
        demanda = demanda_base * factor
        presupuesto = calcular_presupuesto(
            demanda=demanda,
            precios_metales=precios,
            parametros=parametros,
        )

        filas.append({
            "variacion_produccion_pct": variacion * 100,
            "factor_produccion": factor,
            "piezas_anuales": demanda.sum().sum(),
            "presupuesto_anual": presupuesto["TOTAL PRESUPUESTO"].sum(),
            "costo_promedio_pieza": (
                presupuesto["TOTAL PRESUPUESTO"].sum()
                / demanda.sum().sum()
            ),
        })

    df = pd.DataFrame(filas)

    base = df.loc[df["factor_produccion"].eq(1.0)].iloc[0]
    df["variacion_presupuesto_pct"] = (
        df["presupuesto_anual"] / base["presupuesto_anual"] - 1
    ) * 100

    df["elasticidad_aprox"] = df.apply(
        lambda r: (
            r["variacion_presupuesto_pct"] / r["variacion_produccion_pct"]
            if abs(r["variacion_produccion_pct"]) > 1e-12
            else float("nan")
        ),
        axis=1,
    )

    return df
