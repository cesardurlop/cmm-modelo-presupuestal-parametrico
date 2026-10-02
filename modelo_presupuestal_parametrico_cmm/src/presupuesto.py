from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


DENOMINACIONES = ["0.50", "1", "2", "5", "10", "20"]
COLUMNAS_DEMANDA = ["$0.50", "$1.00", "$2.00", "$5.00", "$10.00", "$20.00"]


@dataclass
class ParametrosPresupuesto:
    tc_base: float
    faa: float
    recuperacion_scrap: float
    inflacion: float
    energia_unitaria_2025: float
    personal_eventual_mensual: float
    sobrecargos_mensuales: float
    fijo_acunacion_mensual: float
    fijo_cospel_mensual: float
    acu_tarifas: np.ndarray
    cospel_tarifas: np.ndarray
    acero_usd_pieza: np.ndarray
    bronze: dict
    bronze_denoms: pd.DataFrame
    alpaca: dict
    alpaca_denoms: pd.DataFrame


def cargar_demanda(archivo: str) -> pd.DataFrame:
    df = pd.read_excel(
        archivo,
        sheet_name="DEMANDA BANXICO 2025",
        header=3,
        nrows=12,
    )
    demanda = df[COLUMNAS_DEMANDA].astype(float) * 1_000_000
    demanda.columns = DENOMINACIONES
    demanda.index = df["Mes"].astype(str)
    return demanda


def _valor_por_etiqueta(df: pd.DataFrame, etiqueta: str) -> float:
    for i in range(len(df)):
        if str(df.iloc[i, 0]).strip() == etiqueta:
            return float(df.iloc[i, 1])
    raise KeyError(etiqueta)


def extraer_parametros(archivo: str) -> ParametrosPresupuesto:
    consolidado = pd.read_excel(archivo, sheet_name="CONSOLIDADO", header=None)
    met = pd.read_excel(archivo, sheet_name="METALES 2025 BUENO", header=None)
    meses = pd.read_excel(archivo, sheet_name="MESES 2025", header=None)

    tc = float(met.iloc[4, 1])
    faa = float(met.iloc[5, 1])
    recuperacion = float(met.iloc[6, 1])
    inflacion = float(met.iloc[7, 1])

    energia_base = _valor_por_etiqueta(
        consolidado, "Costo unitario energía base 2024"
    )
    incremento_energia = _valor_por_etiqueta(
        consolidado, "Incremento energía"
    )

    personal = _valor_por_etiqueta(
        consolidado, "Personal eventual mensual"
    )
    sobrecargos = _valor_por_etiqueta(
        consolidado, "Sobrecargos mensuales"
    )
    fijo_acu_base = _valor_por_etiqueta(
        consolidado, "Costo fijo acuñación base mensual"
    )
    fijo_cospel_base = _valor_por_etiqueta(
        consolidado, "Costo fijo cospel base mensual"
    )
    factor_fijos = _valor_por_etiqueta(
        consolidado, "Factor actualización costos fijos"
    )

    acu_base = meses.iloc[22, 1:7].astype(float).to_numpy()
    cospel_base = meses.iloc[25, 1:7].astype(float).to_numpy()

    bronze = {
        "comp_cu": float(met.iloc[19, 1]),
        "comp_al": float(met.iloc[20, 1]),
        "comp_ni": float(met.iloc[21, 1]),
        "prem_cu": float(met.iloc[22, 1]),
        "prem_al_pct": float(met.iloc[23, 1]),
        "prem_ni": float(met.iloc[24, 1]),
        "transformacion": float(met.iloc[25, 1]),
        "base_enero_sin_faa": float(met.iloc[26, 1]),
    }

    bronze_denoms = pd.DataFrame({
        "gramos": met.iloc[40, 1:7].astype(float).to_numpy(),
        "scrap": met.iloc[41, 1:7].astype(float).to_numpy(),
        "rendimiento": met.iloc[42, 1:7].astype(float).to_numpy(),
    }, index=DENOMINACIONES)

    alpaca = {
        "comp_cu": float(met.iloc[64, 1]),
        "comp_ni": float(met.iloc[65, 1]),
        "comp_zn": float(met.iloc[66, 1]),
        "prem_cu": float(met.iloc[67, 1]),
        "prem_ni": float(met.iloc[68, 1]),
        "prem_zn": float(met.iloc[69, 1]),
        "transformacion": float(met.iloc[70, 1]),
    }

    alpaca_denoms = pd.DataFrame({
        "gramos": met.iloc[82, 1:7].astype(float).to_numpy(),
        "scrap": met.iloc[83, 1:7].astype(float).to_numpy(),
        "rendimiento": met.iloc[84, 1:7].astype(float).to_numpy(),
    }, index=DENOMINACIONES)

    acero_usd_pieza = met.iloc[107, 1:7].astype(float).to_numpy()

    return ParametrosPresupuesto(
        tc_base=tc,
        faa=faa,
        recuperacion_scrap=recuperacion,
        inflacion=inflacion,
        energia_unitaria_2025=energia_base * (1 + incremento_energia),
        personal_eventual_mensual=personal,
        sobrecargos_mensuales=sobrecargos,
        fijo_acunacion_mensual=fijo_acu_base * factor_fijos,
        fijo_cospel_mensual=fijo_cospel_base * factor_fijos,
        acu_tarifas=acu_base * (1 + inflacion),
        cospel_tarifas=cospel_base * (1 + inflacion),
        acero_usd_pieza=acero_usd_pieza,
        bronze=bronze,
        bronze_denoms=bronze_denoms,
        alpaca=alpaca,
        alpaca_denoms=alpaca_denoms,
    )


def leer_pronosticos_excel_referencia(archivo: str) -> pd.DataFrame:
    """
    Lee los pronósticos ya almacenados en el Excel.
    Sirve únicamente como prueba de trazabilidad: con estos precios el
    modelo Python debe reproducir exactamente el consolidado actual.
    """
    met = pd.read_excel(archivo, sheet_name="METALES 2025 BUENO", header=None)
    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    return pd.DataFrame({
        "cobre": met.iloc[11, 2:14].astype(float).to_numpy(),
        "aluminio": met.iloc[12, 2:14].astype(float).to_numpy(),
        "niquel": met.iloc[13, 2:14].astype(float).to_numpy(),
        "zinc": met.iloc[14, 2:14].astype(float).to_numpy(),
    }, index=meses)


def _tarifas_bronce(
    precios: pd.DataFrame,
    tc: pd.Series,
    p: ParametrosPresupuesto,
) -> pd.DataFrame:
    b = p.bronze

    cu = (precios["cobre"] + b["prem_cu"]) * b["comp_cu"]
    al = (precios["aluminio"] * (1 + b["prem_al_pct"])) * b["comp_al"]
    ni = (precios["niquel"] + b["prem_ni"]) * b["comp_ni"]

    indice = cu + al + ni
    valor_sin_faa = b["base_enero_sin_faa"] + (indice - indice.iloc[0])
    valor_con_faa = valor_sin_faa * (1 + p.faa)

    out = pd.DataFrame(index=precios.index, columns=DENOMINACIONES, dtype=float)

    for d in DENOMINACIONES:
        gramos = p.bronze_denoms.loc[d, "gramos"]
        scrap = p.bronze_denoms.loc[d, "scrap"]
        rendimiento = p.bronze_denoms.loc[d, "rendimiento"]

        tarifa = (
            (b["transformacion"] * tc)
            + (
                (valor_con_faa * tc)
                - p.recuperacion_scrap * (valor_sin_faa * tc) * scrap
            )
        ) / rendimiento * gramos / 1000

        # El Excel original redondea las tarifas de aleación a 6 decimales.
        out[d] = np.round(tarifa, 6)

    return out


def _tarifas_alpaca(
    precios: pd.DataFrame,
    tc: pd.Series,
    p: ParametrosPresupuesto,
) -> pd.DataFrame:
    a = p.alpaca

    valor_sin_faa = (
        (precios["cobre"] + a["prem_cu"]) * a["comp_cu"]
        + (precios["niquel"] + a["prem_ni"]) * a["comp_ni"]
        + (precios["zinc"] + a["prem_zn"]) * a["comp_zn"]
    )
    valor_con_faa = valor_sin_faa * (1 + p.faa)

    out = pd.DataFrame(index=precios.index, columns=DENOMINACIONES, dtype=float)

    for d in DENOMINACIONES:
        gramos = p.alpaca_denoms.loc[d, "gramos"]
        scrap = p.alpaca_denoms.loc[d, "scrap"]
        rendimiento = p.alpaca_denoms.loc[d, "rendimiento"]

        tarifa = (
            (a["transformacion"] * tc)
            + (
                (valor_con_faa * tc)
                - p.recuperacion_scrap * (valor_sin_faa * tc) * scrap
            )
        ) / rendimiento * gramos / 1000

        out[d] = np.round(tarifa, 6)

    return out


def calcular_presupuesto(
    demanda: pd.DataFrame,
    precios_metales: pd.DataFrame,
    parametros: ParametrosPresupuesto,
    tc_mensual: pd.Series | None = None,
    factor_energia: float = 1.0,
) -> pd.DataFrame:
    """
    Reproduce la lógica de MESES 2025:
    Libranza = acuñación + cospeleo + acero + bronce-Al + alpaca
    Total = Libranza + PEV + sobrecargos + energía + fijos
    """
    demanda = demanda.copy()
    precios_metales = precios_metales.copy()

    if len(demanda) != len(precios_metales):
        raise ValueError("Demanda y precios deben tener el mismo número de meses.")

    precios_metales.index = demanda.index

    if tc_mensual is None:
        tc = pd.Series(parametros.tc_base, index=demanda.index, dtype=float)
    else:
        tc = pd.Series(np.asarray(tc_mensual, dtype=float), index=demanda.index)

    acu = pd.DataFrame(
        np.tile(parametros.acu_tarifas, (len(demanda), 1)),
        index=demanda.index,
        columns=DENOMINACIONES,
    )
    cospel = pd.DataFrame(
        np.tile(parametros.cospel_tarifas, (len(demanda), 1)),
        index=demanda.index,
        columns=DENOMINACIONES,
    )

    acero = pd.DataFrame(
        np.outer(tc.values, parametros.acero_usd_pieza),
        index=demanda.index,
        columns=DENOMINACIONES,
    )

    bronce = _tarifas_bronce(precios_metales, tc, parametros)
    alpaca = _tarifas_alpaca(precios_metales, tc, parametros)

    out = pd.DataFrame(index=demanda.index)
    out["Total piezas"] = demanda.sum(axis=1)
    out["Acuñación variable"] = (demanda * acu).sum(axis=1)
    out["Cospeleo variable"] = (demanda * cospel).sum(axis=1)
    out["Acero inoxidable"] = (demanda * acero).sum(axis=1)
    out["Bronce-Al"] = (demanda * bronce).sum(axis=1)
    out["Alpaca"] = (demanda * alpaca).sum(axis=1)

    out["Libranza ordinaria"] = out[
        [
            "Acuñación variable",
            "Cospeleo variable",
            "Acero inoxidable",
            "Bronce-Al",
            "Alpaca",
        ]
    ].sum(axis=1)

    out["Personal eventual"] = parametros.personal_eventual_mensual
    out["Sobrecargos"] = parametros.sobrecargos_mensuales
    out["Energía"] = (
        out["Total piezas"]
        * parametros.energia_unitaria_2025
        * factor_energia
    )
    out["Fijo acuñación"] = parametros.fijo_acunacion_mensual
    out["Fijo cospel"] = parametros.fijo_cospel_mensual

    out["TOTAL PRESUPUESTO"] = out[
        [
            "Libranza ordinaria",
            "Personal eventual",
            "Sobrecargos",
            "Energía",
            "Fijo acuñación",
            "Fijo cospel",
        ]
    ].sum(axis=1)

    return out


def composicion_anual(presupuesto_mensual: pd.DataFrame) -> pd.Series:
    columnas = [
        "Libranza ordinaria",
        "Personal eventual",
        "Sobrecargos",
        "Energía",
        "Fijo acuñación",
        "Fijo cospel",
    ]
    return presupuesto_mensual[columnas].sum()
