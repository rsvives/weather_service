import dotenv
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from weather_data_local_download import get_weather_data
from pydantic import BaseModel
import os
import jwt
# import bcrypt

app = FastAPI(title="Weather Analysis Microservice")
security = HTTPBearer()

config = dotenv.dotenv_values(".env")
# security = HTTPBearer()

# # Token hash almacenado (en producción, usar variable de entorno)
# AUTH_TOKEN_SECRET = config["AUTH_TOKEN_SECRET"]
# HASHED_TOKEN = bcrypt.hashpw(AUTH_TOKEN_SECRET.encode('utf-8'), bcrypt.gensalt())
# print(HASHED_TOKEN)


# # Función de dependencia para verificar el token
# async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     token = credentials.credentials
#     print(token.encode('utf-8'), HASHED_TOKEN)
#     if not bcrypt.checkpw(token.encode('utf-8'), HASHED_TOKEN):
#         raise HTTPException(status_code=403, detail="Token inválido")
    
#     return token



JWT_SECRET = config["JWT_SECRET"]
JWT_PASSWORD = config["JWT_PASSWORD"]
JWT_ALGORITHM = "HS256"

# Función de dependencia para verificar JWT
async def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    try:
        # Verificar y decodificar el JWT
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        print(payload)
        if "secret" not in payload or payload.get("secret") != JWT_PASSWORD:
            raise HTTPException(status_code=403, detail="Token inválido")
        else:
            return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Token inválido")


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

@app.get('/auth_check')
def auth_check(token: str = Depends(verify_jwt)):
    return {"status": "authenticated", "timestamp": datetime.now().isoformat()}

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
    weather_check: WeatherCheck,
    token: str = Depends(verify_jwt)
) -> WeatherResponse:
    return get_weather_data(weather_check.lat, weather_check.lon, weather_check.radius, weather_check.year, weather_check.month, weather_check.start_day, weather_check.end_day)

