from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


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