# Modelo Paramétrico Presupuestal — Casa de Moneda de México

Repositorio unificado para el trabajo de titulación **“Análisis Operativo y Financiero en la Producción de Moneda Metálica: Un Enfoque Actuarial”**.

## Objetivo

Integrar en una sola ejecución:

1. Modelos univariados de aluminio, cobre, níquel y zinc.
2. Regresión múltiple complementaria con tipo de cambio, petróleo e industria.
3. Comparación de desempeño fuera de muestra.
4. Selección configurable de precios de referencia.
5. Modelo paramétrico del presupuesto 2025.
6. Sensibilidad del presupuesto frente a cambios en producción.
7. Gráficas de síntesis para el Capítulo 7.
8. Escenarios presupuestales, una vez aprobados sus supuestos.

## Estructura

```text
modelo_presupuestal_parametrico_cmm/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── config/
│   └── parametros.py
├── datos/
│   ├── presupuesto/
│   │   └── presupuesto_cmm_2025.xlsx
│   ├── metales/
│   │   ├── aluminio_2015_2024.xlsx
│   │   ├── cobre_2015_2024.xlsx
│   │   ├── niquel_2015_2024.xlsx
│   │   └── zinc_2015_2024.xlsx
│   └── macroeconomicas/
│       ├── industria_2015_2024.xlsx
│       ├── petroleo_2015_2024.xlsx
│       └── tipo_cambio_2015_2024.xlsx
├── src/
│   ├── datos.py
│   ├── univariados.py
│   ├── multivariado.py
│   ├── presupuesto.py
│   ├── analisis.py
│   ├── escenarios.py
│   └── graficas.py
└── resultados/
    ├── tablas/
    └── graficas/
```

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Control de trazabilidad del presupuesto

El módulo `src/presupuesto.py` reproduce la lógica del Excel:

```text
Libranza ordinaria
= Acuñación variable
+ Cospeleo variable
+ Acero inoxidable
+ Bronce-Al
+ Alpaca

TOTAL PRESUPUESTO
= Libranza ordinaria
+ Personal eventual
+ Sobrecargos
+ Energía
+ Fijo acuñación
+ Fijo cospel
```

Como control de calidad, `main.py` vuelve a calcular primero el presupuesto con los precios almacenados en el Excel. El total debe reproducir:

**$10,173,317,991.55 MXN**

antes de calcular el presupuesto actualizado con los pronósticos del repositorio.

## Selección de precios

En `config/parametros.py`:

```python
MODO_SELECCION_PRECIOS = "univariado"
```

Opciones:

- `univariado`: A–D son el escenario central; E funciona como contraste.
- `auto_rmse`: toma por metal la alternativa con menor RMSE.
- `manual`: se define individualmente en `SELECCION_MANUAL`.

Para la versión actual de la tesis se recomienda mantener **univariado** como escenario central hasta documentar formalmente otro criterio.

## Gráficas del Capítulo 7

El programa genera automáticamente:

1. `01_arquitectura_modelo_parametrico.png`
2. `02_sensibilidad_presupuesto_produccion.png`
3. `03_pronosticos_cuatro_metales.png`
4. `04_univariado_vs_multivariado.png`
5. `05_pronostico_rodante.png`
6. `06_composicion_presupuesto_2025.png`

La figura 7 de escenarios se genera únicamente cuando:

```python
ACTIVAR_ESCENARIOS = True
```

No se activa por defecto para evitar introducir supuestos no justificados en la tesis.

## Nota metodológica importante

El RMSE de la regresión múltiple durante 2023–2024 está condicionado a las variables explicativas observadas en ese periodo. Por ello, la comparación con un modelo univariado debe interpretarse junto con sus diagnósticos y no únicamente como una competencia mecánica de RMSE.
