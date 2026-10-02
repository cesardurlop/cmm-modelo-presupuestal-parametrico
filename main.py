from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from config.parametros import (
    ACTIVAR_ESCENARIOS,
    ARCHIVOS_MACRO,
    ARCHIVOS_METALES,
    ESCENARIOS,
    EXPLICATIVAS,
    FACTORES_SENSIBILIDAD_PRODUCCION,
    HORIZONTE_PRONOSTICO,
    INICIO_VALIDACION,
    METALES,
    MODO_SELECCION_PRECIOS,
    ORDENES_ARIMA,
    PERIODO_FIN,
    PERIODO_INICIO,
    PRESUPUESTO_XLSX,
    RESULTADOS,
    SELECCION_MANUAL,
)
from src.analisis import (
    comparar_fuentes_precio,
    construir_pronosticos_seleccionados,
    sensibilidad_produccion,
)
from src.datos import construir_base_historica
from src.escenarios import calcular_escenarios
from src.graficas import (
    arquitectura_modelo,
    composicion_presupuesto,
    contraste_aluminio_cobre,
    escenarios_presupuesto,
    pronostico_rodante,
    pronosticos_cuatro_metales,
    sensibilidad_presupuesto,
)
from src.multivariado import analizar_multivariado
from src.presupuesto import (
    calcular_presupuesto,
    cargar_demanda,
    composicion_anual,
    extraer_parametros,
    leer_pronosticos_excel_referencia,
)
from src.univariados import analizar_univariado


def crear_carpetas() -> dict[str, Path]:
    rutas = {
        "tab_uni": RESULTADOS / "tablas" / "univariados",
        "tab_multi": RESULTADOS / "tablas" / "multivariado",
        "tab_pres": RESULTADOS / "tablas" / "presupuesto",
        "fig_cap7": RESULTADOS / "graficas" / "capitulo7",
    }
    for p in rutas.values():
        p.mkdir(parents=True, exist_ok=True)
    return rutas


def main() -> None:
    rutas = crear_carpetas()

    print("=" * 78)
    print("MODELO PARAMÉTRICO PRESUPUESTAL - CASA DE MONEDA DE MÉXICO")
    print("=" * 78)

    # --------------------------------------------------------
    # 1. Base histórica 2015-2024
    # --------------------------------------------------------
    print("\n[1/8] Cargando series históricas...")
    base = construir_base_historica(
        ARCHIVOS_METALES,
        ARCHIVOS_MACRO,
        PERIODO_INICIO,
        PERIODO_FIN,
    )
    base.to_csv(rutas["tab_multi"] / "base_historica_unificada.csv")

    # --------------------------------------------------------
    # 2. Modelos univariados A-D
    # --------------------------------------------------------
    print("[2/8] Estimando modelos univariados...")
    resultados_uni = {}

    for metal in METALES:
        res = analizar_univariado(
            base[metal],
            ORDENES_ARIMA,
            horizonte_prueba=24,
            horizonte_pronostico=HORIZONTE_PRONOSTICO,
        )
        resultados_uni[metal] = res

        res["comparacion"].to_csv(
            rutas["tab_uni"] / f"comparacion_modelos_{metal}.csv",
            index=False,
        )
        pd.DataFrame({
            "Fecha": res["pronostico"].index,
            "Precio pronosticado": res["pronostico"].values,
        }).to_csv(
            rutas["tab_uni"] / f"pronostico_{metal}_2025.csv",
            index=False,
        )

        print(
            f"  {metal:10s} -> {res['modelo_ganador']}"
            f" | RMSE={res['metricas_ganador']['RMSE']:.4f}"
        )

    # --------------------------------------------------------
    # 3. Regresión múltiple (Anexo E)
    # --------------------------------------------------------
    print("\n[3/8] Estimando regresión múltiple...")
    multi = analizar_multivariado(
        base,
        METALES,
        EXPLICATIVAS,
        inicio_validacion=INICIO_VALIDACION,
        horizonte=HORIZONTE_PRONOSTICO,
    )
    multi["metricas"].to_csv(
        rutas["tab_multi"] / "metricas_regresion_multiple.csv",
        index=False,
    )
    multi["coeficientes"].to_csv(
        rutas["tab_multi"] / "coeficientes_regresion_multiple.csv",
        index=False,
    )
    multi["vif"].to_csv(
        rutas["tab_multi"] / "vif_regresion_multiple.csv",
        index=False,
    )
    multi["escenario_macro"].to_csv(
        rutas["tab_multi"] / "escenario_macro_2025.csv",
    )
    multi["pronosticos"].to_csv(
        rutas["tab_multi"] / "pronosticos_regresion_2025.csv",
    )

    # --------------------------------------------------------
    # 4. Comparación de fuentes de precios
    # --------------------------------------------------------
    print("[4/8] Comparando univariado vs. multivariado...")
    comparacion = comparar_fuentes_precio(
        resultados_uni,
        multi,
        MODO_SELECCION_PRECIOS,
        SELECCION_MANUAL,
    )
    comparacion.to_csv(
        rutas["tab_pres"] / "comparacion_fuentes_precios.csv",
        index=False,
    )

    pronosticos_sel = construir_pronosticos_seleccionados(
        resultados_uni,
        multi,
        comparacion,
    )
    pronosticos_sel.to_csv(
        rutas["tab_pres"] / "precios_seleccionados_2025.csv",
    )

    # --------------------------------------------------------
    # 5. Modelo presupuestal: trazabilidad y versión actualizada
    # --------------------------------------------------------
    print("[5/8] Calculando modelo presupuestal...")
    demanda = cargar_demanda(PRESUPUESTO_XLSX)
    parametros = extraer_parametros(PRESUPUESTO_XLSX)

    # 5A: prueba de trazabilidad contra el Excel original
    precios_excel = leer_pronosticos_excel_referencia(PRESUPUESTO_XLSX)
    pres_ref = calcular_presupuesto(
        demanda,
        precios_excel,
        parametros,
    )
    pres_ref.to_csv(
        rutas["tab_pres"] / "presupuesto_referencia_excel_2025.csv",
    )

    total_ref = pres_ref["TOTAL PRESUPUESTO"].sum()
    objetivo_excel = 10_173_317_991.549788
    diferencia = total_ref - objetivo_excel

    print(
        "  QA Excel: "
        f"${total_ref:,.2f} | diferencia vs consolidado = ${diferencia:,.6f}"
    )

    # 5B: presupuesto con pronósticos seleccionados por el repositorio
    precios_para_presupuesto = pronosticos_sel.copy()
    precios_para_presupuesto.index = demanda.index

    pres_modelo = calcular_presupuesto(
        demanda,
        precios_para_presupuesto,
        parametros,
    )
    pres_modelo.to_csv(
        rutas["tab_pres"] / "presupuesto_modelo_2025.csv",
    )

    composicion = composicion_anual(pres_modelo)
    composicion.rename("importe_anual").to_csv(
        rutas["tab_pres"] / "composicion_presupuesto_2025.csv",
    )

    # --------------------------------------------------------
    # 6. Sensibilidad producción
    # --------------------------------------------------------
    print("[6/8] Calculando sensibilidad a producción...")
    sens = sensibilidad_produccion(
        demanda,
        precios_para_presupuesto,
        parametros,
        FACTORES_SENSIBILIDAD_PRODUCCION,
    )
    sens.to_csv(
        rutas["tab_pres"] / "sensibilidad_produccion.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 7. Gráficas del Capítulo 7
    # --------------------------------------------------------
    print("[7/8] Generando gráficas del Capítulo 7...")
    arquitectura_modelo(
        rutas["fig_cap7"] / "01_arquitectura_modelo_parametrico.png"
    )
    sensibilidad_presupuesto(
        sens,
        rutas["fig_cap7"] / "02_sensibilidad_presupuesto_produccion.png",
    )
    pronosticos_cuatro_metales(
        base,
        pronosticos_sel,
        rutas["fig_cap7"] / "03_pronosticos_cuatro_metales.png",
    )
    contraste_aluminio_cobre(
        base,
        resultados_uni,
        multi,
        rutas["fig_cap7"] / "04_univariado_vs_multivariado.png",
    )
    pronostico_rodante(
        rutas["fig_cap7"] / "05_pronostico_rodante.png"
    )
    composicion_presupuesto(
        composicion,
        rutas["fig_cap7"] / "06_composicion_presupuesto_2025.png",
    )

    # --------------------------------------------------------
    # 8. Escenarios (solo si fueron aprobados)
    # --------------------------------------------------------
    print("[8/8] Escenarios presupuestales...")
    if ACTIVAR_ESCENARIOS:
        escenarios = calcular_escenarios(
            demanda,
            precios_para_presupuesto,
            parametros,
            ESCENARIOS,
        )
        escenarios.to_csv(
            rutas["tab_pres"] / "escenarios_presupuesto.csv",
            index=False,
        )
        escenarios_presupuesto(
            escenarios,
            rutas["fig_cap7"] / "07_escenarios_presupuesto.png",
        )
        print("  Escenarios generados.")
    else:
        print(
            "  OMITIDO: ACTIVAR_ESCENARIOS=False. "
            "Defina primero supuestos académicamente justificables en config/parametros.py."
        )

    print("\n" + "=" * 78)
    print("PROCESO TERMINADO")
    print("=" * 78)
    print(
        f"Presupuesto de referencia Excel: ${total_ref:,.2f}\n"
        f"Presupuesto con precios seleccionados: "
        f"${pres_modelo['TOTAL PRESUPUESTO'].sum():,.2f}\n"
        f"Resultados: {RESULTADOS.resolve()}"
    )


if __name__ == "__main__":
    main()
