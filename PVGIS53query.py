#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 19 14:48:45 2025

@author: pm.deoliveiradejes
"""
import pvlib
import pandas as pd
import numpy as np

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

    print(f"\n--- VALORES HORARIOS GHI [W/m²] (Riohacha) ---")
    print(df_comparativo.round(2).to_string())
    
    print(f"\n" + "="*45)
    print(f"SUMAS DE ENERGÍA DIARIA (kWh/m²/día):")
    print(f"---------------------------------------------")
    print(f"CASO PROMEDIO: {ghi_prom.sum()/1000:.3f}")
    print(f"CASO MÁXIMO  : {ghi_max.sum()/1000:.3f} (Fecha TMY: {f_max.strftime('%d-%b')})")
    print(f"CASO MÍNIMO  : {ghi_min.sum()/1000:.3f} (Fecha TMY: {f_min.strftime('%d-%b')})")
    print("="*45)

except Exception as e:
    print(f"Error: {e}")