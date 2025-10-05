from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime 
from weather_data_local_download import get_weather_data


app = FastAPI(title="Weather Analysis Microservice")



@app.get("/")
async def root():
    return {
        "service": "Weather Analysis Microservice",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Endpoint para verificar que el servicio está funcionando"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/weather_check")
def weather_check(
    lat: float,
    lon: float,
    radius: int,
    year: int,
    month: int,
    start_day: int,
    end_day: int
):
    """Endpoint para recibir parámetros de consulta meteorológica"""


    return {
        "location": {
            "lat": lat,
            "lon": lon,
            "radius": radius
        },
        "date_range": {
            "year": year,
            "month": month,
            "start_day": start_day,
            "end_day": end_day
        }
    }


