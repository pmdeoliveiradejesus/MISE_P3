#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis de Irradiancia GHI - Riohacha, La Guajira
Vectores: Promedio, Máximo y Mínimo Real
"""

import pvlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. Configuración de Coordenadas
lat, lon = 11.546, -72.896 # Riohacha, Colombia

try:
    print(f"Consultando PVGIS 5.3 para: Lat {lat}, Lon {lon}...")
    
    # 2. Obtención de datos TMY
    output = pvlib.iotools.get_pvgis_tmy(
        lat, lon, 
        map_variables=True, 
        startyear=2005, 
        endyear=2023, 
        url='https://re.jrc.ec.europa.eu/api/v5_3/'
    )
    
    data = output[0]
    
    # 3. Ajuste de Zona Horaria (Colombia UTC-5)
    if data.index.tz is None:
        data = data.tz_localize('UTC')
    ghi_series = data.tz_convert('America/Bogota')['ghi']

    # --- 4. PROCESAMIENTO FILTRADO (Evitar días incompletos) ---
    # Contamos horas por día para ignorar el 31-Dic o 1-Ene que quedan mochos por el TZ
    conteo_horas = ghi_series.resample('D').count()
    dias_completos = conteo_horas[conteo_horas == 24].index
    ghi_limpio = ghi_series[ghi_series.index.normalize().isin(dias_completos)]

    # A. Vector Promedio (Media horaria anual)
    ghi_promedio = ghi_limpio.groupby(ghi_limpio.index.hour).mean()

    # B. Identificar Días Extremos Reales
    energia_diaria = ghi_limpio.resample('D').sum()
    f_max = energia_diaria.idxmax()
    f_min = energia_diaria.idxmin()

    # C. Extraer Perfiles 24h
    ghi_max_dia = ghi_limpio[ghi_limpio.index.normalize() == f_max.normalize()].values
    ghi_min_dia = ghi_limpio[ghi_limpio.index.normalize() == f_min.normalize()].values
    
    horas = np.arange(24)

    # --- 5. RESULTADOS EN CONSOLA ---
    df_comparativo = pd.DataFrame({
        'Hora': horas,
        'Promedio': ghi_promedio.values,
        'Máximo': ghi_max_dia,
        'Mínimo': ghi_min_dia
    }).set_index('Hora')

    print("\n" + "="*50)
    print("VALORES HORARIOS GHI [W/m²]")
    print("="*50)
    print(df_comparativo.round(2).to_string())
    
    print("\n" + "="*50)
    print("SUMAS DE ENERGÍA DIARIA (HSP - kWh/m²/día)")
    print(f"Promedio Anual : {ghi_promedio.sum()/1000:.3f}")
    print(f"Día Máximo ({f_max.strftime('%d-%b')}) : {ghi_max_dia.sum()/1000:.3f}")
    print(f"Día Mínimo ({f_min.strftime('%d-%b')}) : {ghi_min_dia.sum()/1000:.3f}")
    print("="*50)

    # --- 6. GENERACIÓN DE GRÁFICAS ---
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))

    # FIGURA 1: Las 3 Campanas (La que necesitabas corregir)
    axs[0, 0].plot(horas, ghi_promedio.values, 'k--', lw=2.5, label='Promedio Anual')
    axs[0, 0].plot(horas, ghi_max_dia, 'r-', lw=2, label=f'Día Máximo ({f_max.strftime("%d-%b")})')
    axs[0, 0].plot(horas, ghi_min_dia, 'g-', lw=2, label=f'Día Mínimo ({f_min.strftime("%d-%b")})')
    
    axs[0, 0].set_title('Campanas GHI 24h: Máx, Mín y Promedio')
    axs[0, 0].set_xlabel('Hora Local (Colombia)')
    axs[0, 0].set_ylabel('Irradiancia [W/m²]')
    axs[0, 0].set_xticks(range(0, 25, 2))
    axs[0, 0].legend()
    axs[0, 0].grid(True, alpha=0.3)

    # FIGURA 2: Irradiancia Media Diaria (365 días)
    axs[0, 1].plot(ghi_limpio.resample('D').mean().values, color='orange', lw=1)
    axs[0, 1].set_title('Irradiancia Media Diaria (TMY)')
    axs[0, 1].set_xlabel('Día del Año')
    axs[0, 1].set_ylabel('GHI Medio [W/m²]')
    axs[0, 1].grid(True, alpha=0.3)

    # FIGURA 3: Promedio Mensual
    prom_mensual = ghi_limpio.groupby(ghi_limpio.index.month).mean()
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    axs[1, 0].bar(meses, prom_mensual.values, color='skyblue', edgecolor='navy')
    axs[1, 0].set_title('Distribución Mensual de GHI')
    axs[1, 0].set_ylabel('GHI Medio [W/m²]')

    # FIGURA 4: Serie completa 8760h
    axs[1, 1].plot(ghi_series.values, color='gray', lw=0.2)
    axs[1, 1].set_title('Serie Temporal 8760h (Contexto)')
    axs[1, 1].set_xlabel('Horas del Año')
    axs[1, 1].grid(True, alpha=0.2)

    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"Error detectado: {e}")