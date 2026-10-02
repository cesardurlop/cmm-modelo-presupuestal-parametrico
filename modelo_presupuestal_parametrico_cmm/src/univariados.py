from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import Holt

warnings.filterwarnings("ignore")


def metricas(reales, predichos) -> dict:
    y = np.asarray(reales, dtype=float)
    p = np.asarray(predichos, dtype=float)
    mae = float(np.mean(np.abs(y - p)))
    rmse = float(np.sqrt(np.mean((y - p) ** 2)))
    mask = np.abs(y) > 1e-12
    mape = float(np.mean(np.abs((y[mask] - p[mask]) / y[mask])) * 100)
    return {"MAE": mae, "RMSE": rmse, "MAPE_pct": mape}


def analizar_univariado(
    serie: pd.Series,
    ordenes_arima: list[tuple[int, int, int]],
    horizonte_prueba: int = 24,
    horizonte_pronostico: int = 12,
) -> dict:
    """
    Metodología común A-D:
    - últimos 24 meses como validación;
    - ARIMA definidos + Holt amortiguado;
    - selección por menor RMSE fuera de muestra;
    - reajuste con toda la serie;
    - pronóstico final.
    """
    serie = serie.astype(float).copy()
    entrenamiento = serie.iloc[:-horizonte_prueba]
    prueba = serie.iloc[-horizonte_prueba:]

    resultados = []
    validaciones = {}

    for orden in ordenes_arima:
        nombre = f"ARIMA{orden}"
        try:
            fit = ARIMA(entrenamiento, order=orden).fit()
            pred = pd.Series(
                np.asarray(fit.forecast(horizonte_prueba), dtype=float),
                index=prueba.index,
                name=nombre,
            )
            m = metricas(prueba.values, pred.values)
            resultados.append({
                "Modelo": nombre,
                "AIC": float(fit.aic),
                "BIC": float(fit.bic),
                **m,
            })
            validaciones[nombre] = pred
        except Exception:
            continue

    try:
        fit_holt = Holt(
            entrenamiento,
            damped_trend=True,
            initialization_method="estimated",
        ).fit(optimized=True)
        pred = pd.Series(
            np.asarray(fit_holt.forecast(horizonte_prueba), dtype=float),
            index=prueba.index,
            name="Holt amortiguado",
        )
        m = metricas(prueba.values, pred.values)
        resultados.append({
            "Modelo": "Holt amortiguado",
            "AIC": float(fit_holt.aic),
            "BIC": float(fit_holt.bic),
            **m,
        })
        validaciones["Holt amortiguado"] = pred
    except Exception:
        pass

    tabla = pd.DataFrame(resultados)
    if tabla.empty:
        raise RuntimeError("No se pudo ajustar ningún modelo univariado.")

    tabla = tabla.sort_values(["RMSE", "MAPE_pct"]).reset_index(drop=True)
    ganador = str(tabla.iloc[0]["Modelo"])
    pred_validacion = validaciones[ganador]

    if ganador.startswith("ARIMA"):
        orden = tuple(int(x.strip()) for x in ganador.replace("ARIMA(", "").replace(")", "").split(","))
        fit_final = ARIMA(serie, order=orden).fit()
    else:
        fit_final = Holt(
            serie,
            damped_trend=True,
            initialization_method="estimated",
        ).fit(optimized=True)

    fechas = pd.date_range(
        serie.index.max() + pd.offsets.MonthBegin(1),
        periods=horizonte_pronostico,
        freq="MS",
    )
    pronostico = pd.Series(
        np.asarray(fit_final.forecast(horizonte_pronostico), dtype=float),
        index=fechas,
        name="pronostico_univariado",
    )

    return {
        "comparacion": tabla,
        "modelo_ganador": ganador,
        "metricas_ganador": tabla.iloc[0].to_dict(),
        "prueba_real": prueba,
        "validacion": pred_validacion,
        "pronostico": pronostico,
    }
