# Metodología del repositorio

## Nivel 1 — Modelación univariada por metal

Para cada metal se comparan:

- ARIMA(0,1,0)
- ARIMA(1,1,0)
- ARIMA(0,1,1)
- ARIMA(1,1,1)
- Holt con tendencia amortiguada

Los últimos 24 meses (2023–2024) se reservan como muestra de validación. El ganador se selecciona mediante RMSE fuera de muestra y después se reajusta con 2015–2024 para obtener el pronóstico 2025.

## Nivel 2 — Regresión múltiple complementaria

Se estima para cada metal:

ΔP(m,t) = β0,m + β1,m ΔTC(t) + β2,m ΔPetróleo(t) + β3,m ΔIndustria(t) + ε(m,t)

La validación usa 2023–2024. El escenario 2025 de las variables explicativas se obtiene mediante Holt amortiguado.

## Nivel 3 — Modelo presupuestal paramétrico

Los precios seleccionados alimentan el costo mensual de aleaciones y, junto con la demanda por denominación y las demás partidas, producen el presupuesto mensual y anual.

La implementación de Python replica primero el presupuesto del Excel original como prueba de trazabilidad antes de sustituir los precios por los pronósticos seleccionados.

## Reutilización anual

La arquitectura está diseñada para actualización rodante:

datos observados → recalibración → pronóstico → presupuesto → incorporación de datos nuevos → nueva recalibración.
