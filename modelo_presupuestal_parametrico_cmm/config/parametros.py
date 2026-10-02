from pathlib import Path

# ============================================================
# CONFIGURACIÓN GENERAL DEL PROYECTO
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "datos"
RESULTADOS = ROOT / "resultados"

PRESUPUESTO_XLSX = DATOS / "presupuesto" / "presupuesto_cmm_2025.xlsx"

ARCHIVOS_METALES = {
    "aluminio": DATOS / "metales" / "aluminio_2015_2024.xlsx",
    "cobre": DATOS / "metales" / "cobre_2015_2024.xlsx",
    "niquel": DATOS / "metales" / "niquel_2015_2024.xlsx",
    "zinc": DATOS / "metales" / "zinc_2015_2024.xlsx",
}

ARCHIVOS_MACRO = {
    "tipo_cambio": DATOS / "macroeconomicas" / "tipo_cambio_2015_2024.xlsx",
    "petroleo": DATOS / "macroeconomicas" / "petroleo_2015_2024.xlsx",
    "industria": DATOS / "macroeconomicas" / "industria_2015_2024.xlsx",
}

METALES = ["aluminio", "cobre", "niquel", "zinc"]
EXPLICATIVAS = ["tipo_cambio", "petroleo", "industria"]

PERIODO_INICIO = "2015-01-01"
PERIODO_FIN = "2024-12-01"
INICIO_VALIDACION = "2023-01-01"
HORIZONTE_PRONOSTICO = 12

# ARIMA evaluados de forma homogénea para los cuatro metales.
ORDENES_ARIMA = [
    (0, 1, 0),
    (1, 1, 0),
    (0, 1, 1),
    (1, 1, 1),
]

# ------------------------------------------------------------------
# Fuente de precios que alimenta el presupuesto.
#
# "univariado": usa siempre el ganador ARIMA/Holt de A-D.
# "auto_rmse": compara RMSE univariado vs regresión y toma el menor.
# "manual": usa SELECCION_MANUAL.
#
# Para la tesis se recomienda empezar con "univariado" y usar
# la regresión múltiple como contraste, salvo que se documente
# explícitamente otro criterio.
# ------------------------------------------------------------------
MODO_SELECCION_PRECIOS = "univariado"

SELECCION_MANUAL = {
    "aluminio": "univariado",
    "cobre": "univariado",
    "niquel": "univariado",
    "zinc": "univariado",
}

# Sensibilidad del presupuesto ante producción.
FACTORES_SENSIBILIDAD_PRODUCCION = [-0.10, 0.00, 0.05, 0.10, 0.15]

# Escenarios presupuestales:
# Se dejan desactivados hasta acordar supuestos académicamente defendibles.
ACTIVAR_ESCENARIOS = False

# Ejemplo de estructura. No usar en tesis sin validar estos supuestos.
ESCENARIOS = {
    "favorable": {
        "factor_produccion": 1.00,
        "factor_metales": 0.95,
        "factor_tipo_cambio": 0.98,
        "factor_energia": 0.95,
    },
    "base": {
        "factor_produccion": 1.00,
        "factor_metales": 1.00,
        "factor_tipo_cambio": 1.00,
        "factor_energia": 1.00,
    },
    "presion": {
        "factor_produccion": 1.00,
        "factor_metales": 1.10,
        "factor_tipo_cambio": 1.05,
        "factor_energia": 1.15,
    },
}
