import earthaccess
import dotenv
import xarray as xr
import json
import numpy as np


dotenv.load_dotenv()


auth = earthaccess.login(strategy="environment")
s3_credentials = auth.get_s3_credentials(daac="NSIDC")
nasa_status = earthaccess.status()
print(nasa_status)



lat_target = 43.36029
lon_target = -5.84476
radius = 30000

# Rango de fechas: 10-14 septiembre, años 2010-2025
start_year = 2010
end_year = 2025
start_day = 12
end_day = 12
month = 8

# Inicializar estructura de datos
output_data = {
    "meanTemp": [],
    "maxTemp": [],
    "minTemp": [],
    "rain": {
        "quantity": [],
        "hours": []
    },
    "location": {
        "lat": lat_target,
        "lon": lon_target
    },
    "dateRange": f"September {start_day}-{end_day}",
    "years": list(range(start_year, end_year + 1))
}

# Hacer búsqueda para todos los años
all_results = []
for year in range(start_year, end_year + 1):
    print(f"Searching year {year}...")
    results = earthaccess.search_data(
        short_name=('M2SDNXSLV'),
        temporal=(f"{year}-{month:02d}-{start_day:02d} 00:00:00", f"{year}-{month}-{end_day:02d} 23:59:59"),
        cloud_hosted=True,
        circle=(lat_target, lon_target, radius),
    )
    all_results.extend(results)

print(f"Found {len(all_results)} total granules")

# Crear directorio para datos locales
import os
import glob
data_dir = './nasa_data'
os.makedirs(data_dir, exist_ok=True)

# Verificar si ya existen archivos descargados correspondientes a las fechas específicas
existing_files = []
for year in range(start_year, end_year + 1):
    for days in range(start_day, end_day + 1):
        existing_files.extend(glob.glob(os.path.join(data_dir, f'*.{year}{month}{days:02d}.nc4')))

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
ds_point = ds.sel(lat=lat_target, lon=lon_target,method='nearest',tolerance=radius)

# Organizar datos por año
print("Processing data by year...")
import pandas as pd

for year in range(start_year, end_year + 1):
    print(f"Processing year {year}...")
    
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
    mean_temps = (year_data['T2MMEAN'].values - 273.15).tolist()
    max_temps = (year_data['T2MMAX'].values - 273.15).tolist()
    min_temps = (year_data['T2MMIN'].values - 273.15).tolist()
    rain_quantity = year_data['TPRECMAX'].values.tolist()
    rain_hours = (24 - year_data['HOURNORAIN'].values/3600).tolist() #data is in seconds + is NO rain hours so it has been converted to hours of rain
    
    # Añadir datos de este año
    output_data["meanTemp"].append(mean_temps)
    output_data["maxTemp"].append(max_temps)
    output_data["minTemp"].append(min_temps)
    output_data["rain"]["quantity"].append(rain_quantity)
    output_data["rain"]["hours"].append(rain_hours)
    
    print(f"Year {year} completed: {len(mean_temps)} days of data")

# Cerrar dataset
ds.close()

# Guardar a JSON
with open('weather_data_historical.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print("\n" + "="*50)
print("Data extraction completed!")
print(f"Total years processed: {len(output_data['meanTemp'])}")
print(f"Output saved to: weather_data_historical.json")
print("\nJSON formatted output:")
print(json.dumps(output_data, indent=2))

print("="*50)




