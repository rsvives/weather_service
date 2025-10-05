from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime 
from weather_data_local_download import get_weather_data
from pydantic import BaseModel

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



class WeatherCheck(BaseModel):
    lat: float
    lon: float
    radius: int
    year: int
    month: int
    start_day: int
    end_day: int

@app.post("/weather_check")
async def weather_check(
    weather_check: WeatherCheck
):
    """Endpoint para recibir parámetros de consulta meteorológica"""
    lat = weather_check.lat
    lon = weather_check.lon
    radius = weather_check.radius
    year = weather_check.year
    month = weather_check.month
    start_day = weather_check.start_day
    end_day = weather_check.end_day

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


