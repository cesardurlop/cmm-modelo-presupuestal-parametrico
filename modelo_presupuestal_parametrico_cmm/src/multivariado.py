from __future__ import annotations

import math

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import jarque_bera
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.holtwinters import Holt


def _mape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = np.abs(y_true) > 1e-12
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _metricas(y_true, y_pred) -> dict:
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(math.sqrt(mean_squared_error(y_true, y_pred))),
        "MAPE_pct": _mape(y_true, y_pred),
    }


def _vif(X: pd.DataFrame) -> pd.DataFrame:
    Xc = sm.add_constant(X)
    filas = []
    for i, col in enumerate(Xc.columns):
        if col == "const":
            continue
        filas.append({
            "variable": col,
            "VIF": variance_inflation_factor(Xc.values, i),
        })
    return pd.DataFrame(filas)


def _reconstruir_nivel(ultimo_nivel: float, diferencias: pd.Series) -> pd.Series:
    valores = []
    actual = float(ultimo_nivel)
    for d in diferencias:
        actual += float(d)
        valores.append(actual)
    return pd.Series(valores, index=diferencias.index)


def generar_escenario_macro_holt(
    base: pd.DataFrame,
    explicativas: list[str],
    horizonte: int = 12,
) -> pd.DataFrame:
    fechas = pd.date_range(
        base.index.max() + pd.offsets.MonthBegin(1),
        periods=horizonte,
        freq="MS",
    )
    salida = {}
    for col in explicativas:
        fit = Holt(
            base[col],
            damped_trend=True,
            initialization_method="estimated",
        ).fit(optimized=True)
        fc = pd.Series(np.asarray(fit.forecast(horizonte)), index=fechas)
        salida[col] = fc
    return pd.DataFrame(salida, index=fechas)


def analizar_multivariado(
    base: pd.DataFrame,
    metales: list[str],
    explicativas: list[str],
    inicio_validacion: str = "2023-01-01",
    horizonte: int = 12,
) -> dict:
    """
    Cuatro ecuaciones OLS separadas:
    ΔMetal_t = b0 + b1 ΔTC_t + b2 ΔPetróleo_t + b3 ΔIndustria_t + error_t
    """
    diff = base.diff().dropna()
    train = diff.loc[diff.index < inicio_validacion]
    test = diff.loc[diff.index >= inicio_validacion]

    metricas_rows = []
    validaciones = {}
    coeficientes = []
    vifs = []
    modelos = {}

    for metal in metales:
        y = train[metal]
        X = sm.add_constant(train[explicativas])
        model = sm.OLS(y, X).fit()
        modelos[metal] = model

        X_test = sm.add_constant(test[explicativas], has_constant="add")
        pred_diff = pd.Series(model.predict(X_test), index=test.index)

        ultimo = base.loc[base.index < pd.Timestamp(inicio_validacion), metal].iloc[-1]
        pred_nivel = _reconstruir_nivel(ultimo, pred_diff)
        real = base.loc[pred_nivel.index, metal]
        validaciones[metal] = pd.DataFrame({"real": real, "regresion": pred_nivel})

        met = _metricas(real.values, pred_nivel.values)
        jb = jarque_bera(model.resid)
        bp = het_breuschpagan(model.resid, model.model.exog)

        metricas_rows.append({
            "metal": metal,
            **met,
            "R2_train": float(model.rsquared),
            "R2_adj_train": float(model.rsquared_adj),
            "F_pvalue": float(model.f_pvalue),
            "Durbin_Watson": float(durbin_watson(model.resid)),
            "Jarque_Bera_pvalue": float(jb.pvalue),
            "Breusch_Pagan_pvalue": float(bp[1]),
        })

        for variable, valor in model.params.items():
            coeficientes.append({
                "metal": metal,
                "variable": variable,
                "coeficiente": float(valor),
                "p_value": float(model.pvalues[variable]),
            })

        vif_m = _vif(train[explicativas])
        vif_m.insert(0, "metal", metal)
        vifs.append(vif_m)

    escenario = generar_escenario_macro_holt(base, explicativas, horizonte)

    pronosticos = {}
    for metal in metales:
        model = sm.OLS(
            diff[metal],
            sm.add_constant(diff[explicativas]),
        ).fit()

        x_full = pd.concat([base[explicativas].iloc[[-1]], escenario])
        x_diff = x_full.diff().iloc[1:]
        X_fut = sm.add_constant(x_diff, has_constant="add")
        pred_diff = pd.Series(model.predict(X_fut), index=escenario.index)
        pronosticos[metal] = _reconstruir_nivel(base[metal].iloc[-1], pred_diff)

    return {
        "base_diferencias": diff,
        "metricas": pd.DataFrame(metricas_rows),
        "coeficientes": pd.DataFrame(coeficientes),
        "vif": pd.concat(vifs, ignore_index=True),
        "validaciones": validaciones,
        "escenario_macro": escenario,
        "pronosticos": pd.DataFrame(pronosticos, index=escenario.index),
    }
