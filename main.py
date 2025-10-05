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

class WeatherResponse(BaseModel):
    meanTemp: list
    maxTemp: list
    minTemp: list
    rain: dict
    location: dict
    dateRange: str
    year: int

@app.post("/weather_check")
async def weather_check(
    weather_check: WeatherCheck
) -> WeatherResponse:
    return get_weather_data(weather_check.lat, weather_check.lon, weather_check.radius, weather_check.year, weather_check.month, weather_check.start_day, weather_check.end_day)




