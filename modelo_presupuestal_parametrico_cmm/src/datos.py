from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd


def normalizar_texto(texto: str) -> str:
    texto = str(texto).strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )


def _detectar_columnas(df: pd.DataFrame) -> tuple[str, str]:
    columnas = list(df.columns)

    fecha = None
    for c in columnas:
        n = normalizar_texto(c)
        if any(k in n for k in ["fecha", "date", "periodo", "mes"]):
            fecha = c
            break

    if fecha is None:
        for c in columnas:
            prueba = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
            if prueba.notna().mean() >= 0.80:
                fecha = c
                break

    if fecha is None:
        raise ValueError(f"No se detectó columna de fecha. Columnas: {columnas}")

    valor = None
    preferidas = ["precio", "valor", "indice", "total", "tipo de cambio", "imai"]
    for palabra in preferidas:
        for c in columnas:
            if c == fecha:
                continue
            if palabra in normalizar_texto(c):
                numerica = pd.to_numeric(df[c], errors="coerce")
                if numerica.notna().mean() >= 0.70:
                    valor = c
                    break
        if valor is not None:
            break

    if valor is None:
        for c in columnas:
            if c == fecha:
                continue
            numerica = pd.to_numeric(df[c], errors="coerce")
            if numerica.notna().mean() >= 0.70:
                valor = c
                break

    if valor is None:
        raise ValueError(f"No se detectó columna numérica. Columnas: {columnas}")

    return fecha, valor


def leer_serie_mensual(
    archivo: Path,
    nombre: str,
    inicio: str = "2015-01-01",
    fin: str = "2024-12-01",
) -> pd.Series:
    """Lee una serie mensual buscando automáticamente una hoja válida."""
    if not archivo.exists():
        raise FileNotFoundError(archivo)

    xls = pd.ExcelFile(archivo)
    ultimo_error = None

    for hoja in xls.sheet_names:
        try:
            df = pd.read_excel(archivo, sheet_name=hoja)
            df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
            if df.empty:
                continue

            fecha_col, valor_col = _detectar_columnas(df)

            out = df[[fecha_col, valor_col]].copy()
            out.columns = ["fecha", nombre]
            out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce", dayfirst=True)
            out[nombre] = pd.to_numeric(out[nombre], errors="coerce")
            out = out.dropna(subset=["fecha", nombre])
            out["fecha"] = out["fecha"].dt.to_period("M").dt.to_timestamp()
            out = out.drop_duplicates("fecha").set_index("fecha").sort_index()[nombre]
            out = out.loc[inicio:fin]

            esperado = pd.date_range(inicio, fin, freq="MS")
            out = out.reindex(esperado)
            out.index.name = "fecha"

            if out.isna().any():
                raise ValueError(
                    f"{archivo.name}/{hoja}: faltan meses o valores en {nombre}."
                )

            out.name = nombre
            return out.astype(float)

        except Exception as exc:
            ultimo_error = exc
            continue

    raise ValueError(
        f"No se pudo leer una serie mensual válida de {archivo.name}. "
        f"Último error: {ultimo_error}"
    )


def construir_base_historica(
    archivos_metales: dict[str, Path],
    archivos_macro: dict[str, Path],
    inicio: str,
    fin: str,
) -> pd.DataFrame:
    series = {}
    for nombre, archivo in {**archivos_metales, **archivos_macro}.items():
        series[nombre] = leer_serie_mensual(archivo, nombre, inicio, fin)

    base = pd.concat(series.values(), axis=1)
    esperado = pd.date_range(inicio, fin, freq="MS")
    base = base.reindex(esperado)
    base.index.name = "fecha"

    if base.isna().any().any():
        raise ValueError(
            "La base histórica unificada contiene faltantes. "
            f"{base.isna().sum().to_dict()}"
        )

    return base
