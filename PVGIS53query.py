#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 19 14:48:45 2025
@author: pm.deoliveiradejes - Gemini 3

!pip install pvlib 
import pvlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. Configuración
lat, lon = 11.546, -72.896 #Rio Hacha, La Guajira. Colombia
# lat, lon =36.157, -115.170 #Las Vegas, USA
try:
    # 2. Obtención de TMY (especificando periodo para mayor precisión)
    # start y end definen el rango de años que PVGIS usa para elegir los meses típicos
    output = pvlib.iotools.get_pvgis_tmy(
        lat, lon, 
        map_variables=True, 
        startyear=2005, 
        endyear=2023, 
        url='https://re.jrc.ec.europa.eu/api/v5_3/'
    )
    
    data = output[0]
    # Ajuste de zona horaria para Colombia (evitando el error de "Already tz-aware")
    if data.index.tz is None:
        data = data.tz_localize('UTC')
    ghi_series = data.tz_convert('America/Bogota')['ghi']

    # --- 3. PROCESAMIENTO ---
    # Filtrar solo días con 24 horas (para evitar errores en los bordes del año)
    conteo = ghi_series.resample('D').count()
    dias_ok = conteo[conteo == 24].index
    ghi_limpio = ghi_series[ghi_series.index.normalize().isin(dias_ok)]

    # A. VECTOR PROMEDIO (Media horaria anual)
    ghi_prom = ghi_limpio.groupby(ghi_limpio.index.hour).mean()

    # B. BUSCAR EXTREMOS (Días completos)
    energia_diaria = ghi_limpio.resample('D').sum()
    f_max = energia_diaria.idxmax()
    f_min = energia_diaria.idxmin()

    # C. VECTORES 24H
    ghi_max = ghi_limpio[ghi_limpio.index.normalize() == f_max.normalize()].values
    ghi_min = ghi_limpio[ghi_limpio.index.normalize() == f_min.normalize()].values

    # --- 4. RESULTADOS ---
    # Formatear tabla para impresión
    df_comparativo = pd.DataFrame({
        'Hora': range(24),
        'GHI_Promedio': ghi_prom.values,
        'GHI_Max_Dia': ghi_max,
        'GHI_Min_Dia': ghi_min
    }).set_index('Hora')

    print(f"\n--- VALORES HORARIOS GHI [W/m²]  ---")
    print(df_comparativo.round(2).to_string())
    
    print(f"\n" + "="*45)
    print(f"SUMAS DE ENERGÍA DIARIA (kWh/m²/día):")
    print(f"---------------------------------------------")
    print(f"CASO PROMEDIO: {ghi_prom.sum()/1000:.3f}")
    print(f"CASO MÁXIMO  : {ghi_max.sum()/1000:.3f} (Fecha TMY: {f_max.strftime('%d-%b')})")
    print(f"CASO MÍNIMO  : {ghi_min.sum()/1000:.3f} (Fecha TMY: {f_min.strftime('%d-%b')})")
    print("="*45)

# 2. Descarga de datos TMY
    output = pvlib.iotools.get_pvgis_tmy(lat, lon, map_variables=True, url='https://re.jrc.ec.europa.eu/api/v5_3/')
    data = output[0]
    
    # 3. Ajuste de Zona Horaria (UTC a Colombia)
    if data.index.tz is None:
        data = data.tz_localize('UTC')
    data_local = data.tz_convert('America/Bogota')
    ghi = data_local['ghi']

    # --- 4. CÁLCULO DE VECTORES (24 PUNTOS CADA UNO) ---
    
    # A. Vector Promedio: Media por hora (0-23)
    ghi_promedio = ghi.groupby(ghi.index.hour).mean().values
    
    # B. Identificar Días Extremos
    # Calculamos la energía diaria (Suma de cada día calendario)
    energia_diaria = ghi.resample('D').sum()
    fecha_max = energia_diaria.idxmax()
    fecha_min = energia_diaria.idxmin()
    
    # C. Extraer Perfiles (Asegurando 24 horas usando el atributo .hour)
    # Filtramos los datos por la fecha y agrupamos por hora para asegurar 24 posiciones
    ghi_max_dia = ghi[ghi.index.normalize() == fecha_max.normalize()].groupby(lambda x: x.hour).first().values
    ghi_min_dia = ghi[ghi.index.normalize() == fecha_min.normalize()].groupby(lambda x: x.hour).first().values

    # Verificación de seguridad: si por algún motivo no tienen 24h, rellenamos con 0
    def asegurar_24(vec):
        return np.pad(vec, (0, max(0, 24 - len(vec))), 'constant')[:24]

    ghi_max_dia = asegurar_24(ghi_max_dia)
    ghi_min_dia = asegurar_24(ghi_min_dia)
    horas = np.arange(24)

    # --- 5. GENERACIÓN DE GRÁFICAS ---
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))

    # FIGURA 1: Las 3 Campanas (Máxima, Mínima, Promedio)
    axs[0, 0].plot(horas, ghi_promedio, 'k--', lw=2.5, label='Promedio Anual')
    axs[0, 0].plot(horas, ghi_max_dia, 'r-', lw=2, label=f'Día Máximo ({fecha_max.strftime("%d-%b")})')
    axs[0, 0].plot(horas, ghi_min_dia, 'b-', lw=2, label=f'Día Mínimo ({fecha_min.strftime("%d-%b")})')
    
    axs[0, 0].set_title('Campanas GHI 24h: Máx, Mín y Promedio')
    axs[0, 0].set_xlabel('Hora Local (Colombia)')
    axs[0, 0].set_ylabel('Irradiancia [W/m²]')
    axs[0, 0].set_xticks(range(0, 25, 2))
    axs[0, 0].legend()
    axs[0, 0].grid(True, alpha=0.3)

    # FIGURA 2: Promedio Diario Anual
    axs[0, 1].plot(ghi.resample('D').mean().values, color='orange', lw=1)
    axs[0, 1].set_title('Irradiancia Media Diaria (365 días)')
    axs[0, 1].set_ylabel('GHI Medio [W/m²]')
    axs[0, 1].grid(True, alpha=0.3)

    # FIGURA 3: Promedio Mensual
    prom_mensual = ghi.groupby(ghi.index.month).mean()
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    axs[1, 0].bar(meses, prom_mensual.values, color='skyblue', edgecolor='navy')
    axs[1, 0].set_title('Distribución Mensual de GHI')
    axs[1, 0].set_ylabel('GHI Medio [W/m²]')

    # FIGURA 4: Serie completa
    axs[1, 1].plot(ghi.values, color='gray', lw=0.2)
    axs[1, 1].set_title('Serie Temporal 8760h (TMY)')
    axs[1, 1].grid(True, alpha=0.2)

    plt.tight_layout()
    plt.show()


except Exception as e:
    print(f"Error: {e}")
