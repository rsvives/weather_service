from datetime import datetime
import earthaccess
import dotenv
from fastapi import HTTPException
import xarray as xr
# import json
import numpy as np
import os
import glob
import pandas as pd


# Inicializar autenticación al importar el módulo
dotenv.load_dotenv()
_auth = None
_s3_credentials = None


def _ensure_auth():
    """Asegurar que la autenticación está inicializada"""
    global _auth, _s3_credentials
    if _auth is None:
        _auth = earthaccess.login(strategy="environment")
        _s3_credentials = _auth.get_s3_credentials(daac="NSIDC")
nasa_status = earthaccess.status()
print(nasa_status)


def get_weather_data(lat: float, lon: float, radius: int, start_date: str, end_date:str):
    """
    Obtiene datos meteorológicos históricos de NASA Earthdata para una ubicación y rango de fechas específicos.
    
    Args:
        lat: Latitud del punto objetivo
        lon: Longitud del punto objetivo
        radius: Radio de búsqueda en metros

        start_day: Día de inicio del rango
        end_day: Día de fin del rango
    

    Returns:
        dict: Datos meteorológicos estructurados con temperaturas y precipitación
    """
    # Asegurar autenticación
    _ensure_auth()

    start_year = 2015
    end_year = 2025

    start_date_dt = datetime.strptime(start_date, "%d/%m/%Y, %H:%M:%S")
    end_date_dt = datetime.strptime(end_date, "%d/%m/%Y, %H:%M:%S")
    start_month = start_date_dt.month
    end_month = end_date_dt.month
    start_day = start_date_dt.day
    end_day = end_date_dt.day


    # Inicializar estructura de datos
    output_data = {
        "temps": [],
        # "meanTemp": [],
        # "maxTemp": [],
        # "minTemp": [],
        "rain":[],
        # "rain": {
        #     "quantity": [],
        #     "hours": []
        # },
        "location": {
                "lat": lat,
                "lon": lon
        },
            # "dateRange": f"{year}-{month:02d}-{start_day:02d} to {year}-{month:02d}-{end_day:02d}",
    }

    # Hacer búsqueda para todos los años
    all_results = []
    try:
        for year in range(start_year, end_year + 1):
            print(f"Searching year {year}...")
            results = earthaccess.search_data(
                short_name=('M2SDNXSLV'),
                temporal=(f"{year}-{start_month:02d}-{start_day:02d} 00:00:00", f"{year}-{end_month:02d}-{end_day:02d} 23:59:59"),
                cloud_hosted=True,
                circle=(lat, lon, radius),
        )
            all_results.extend(results)

        print(f"Found {len(all_results)} total granules")
    except RuntimeError as e:
        print(f"Error searching data:")
        error_msg = str(e)
        print(error_msg)
        if("be within -90 and 90.0" in error_msg):
            raise Exception("Latitude must be between -90 and 90")
        else:
            raise Exception("Unknown error searching data")

    # Crear directorio para datos locales
    data_dir = './nasa_data'
    os.makedirs(data_dir, exist_ok=True)

    # Verificar si ya existen archivos descargados correspondientes a las fechas específicas
    existing_files = []
    for year in range(start_year, end_year + 1):
        for month in range(start_month, end_month + 1):
            for days in range(start_day, end_day + 1):
                existing_files.extend(glob.glob(os.path.join(data_dir, f'*.{year}{month:02d}{days:02d}.nc4')))

    print(existing_files)
    print(len(existing_files))

    if len(existing_files) == len(all_results):
        print(f"Found {len(existing_files)} existing files in {data_dir}")
        print("Using local files...")
        downloaded_files = sorted(existing_files)
    else:
        print(f"No local files found. Fetching data from {start_year} to {end_year} for September {start_day}-{end_day}...")
        
        # Descargar archivos localmente
        print("Downloading files to local storage...")
        downloaded_files = earthaccess.download(all_results, data_dir)
        print(f"Downloaded {len(downloaded_files)} files to {data_dir}")

    # Abrir archivos LOCALES (mucho más rápido)
    print("Opening local files...")
    ds = xr.open_mfdataset(downloaded_files, engine='h5netcdf')

    # Seleccionar el punto más cercano a nuestras coordenadas
    print("Selecting location...")
    ds_point = ds.sel(lat=lat, lon=lon, method='nearest', tolerance=radius)

    # Organizar datos por año
    print("Processing data by year...")
    import pandas as pd

    for year in range(start_year, end_year + 1):
        print(f"Processing year {year}...")
        for month in range(start_month, end_month + 1):
            # Filtrar datos de septiembre 10-14 de este año específico
            year_data = ds_point.sel(time=slice(f'{year}-{month}-{start_day:02d}', f'{year}-{month}-{end_day:02d}'))
        
        if len(year_data['time']) == 0:
            print(f"No data found for {year}")
            output_data["meanTemp"].append([])
            output_data["maxTemp"].append([])
            output_data["minTemp"].append([])
            output_data["rain"]["quantity"].append([])
            output_data["rain"]["hours"].append([])
            continue
        
        # Extraer datos (convertir temperaturas a Celsius)
        temps =dict(year=year,mean_temps=(year_data['T2MMEAN'].values - 273.15).tolist(),max_temps=(year_data['T2MMAX'].values - 273.15).tolist(),min_temps=(year_data['T2MMIN'].values - 273.15).tolist()) 
        # max_temps = dict(year=year,data=)
        # min_temps = dict(year=year,data=)
        rain_quantity = year_data['TPRECMAX'].values.tolist()
        rain_hours = ((year_data['HOURNORAIN'].values/(24*60*60))).tolist()  # data is in seconds + is NO rain hours so it has been converted to hours of rain
        rain = dict(year=year,quantity=rain_quantity,hours=rain_hours)
        print(rain_quantity)
        print(rain_hours)
        
        # Añadir datos de este año
        output_data["temps"].append(temps)
        output_data["rain"].append(rain)
        # output_data["meanTemp"].append(mean_temps)
        # output_data["maxTemp"].append(max_temps)
        # output_data["minTemp"].append(min_temps)
        # output_data["rain"]["quantity"].append(rain_quantity)
        # output_data["rain"]["hours"].append(rain_hours)
        
        print(f"Year {year} completed: {len(temps)} days of data")

    # Cerrar dataset
    ds.close()

    return output_data




