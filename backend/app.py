from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.middleware.cors import add_cors_middleware
from backend.routes.reservations import router as reservations_router
from backend.routes.event_ticket import router as event_ticket_router

app = FastAPI(
    title="Reservation Agent API",
    description="API pentru agentul de rezervări culturale - teatru, muzee, filarmonica",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

add_cors_middleware(app)

app.include_router(reservations_router)
app.include_router(event_ticket_router)

@app.get("/")
async def root():
    """Pagina principală cu informații despre API"""
    return {
        "message": "🎭 Reservation Agent API",
        "description": "API pentru rezervări culturale - teatru, muzee, filarmonica",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "POST /reservations/start": "Începe o rezervare nouă",
            "GET /reservations/{session_id}/status": "Verifică statusul",
            "POST /reservations/{session_id}/personal-info": "Trimite date personale",
            "DELETE /reservations/{session_id}": "Șterge sesiunea",
            "POST /event/start": "Incepe o rezervare pentru eveniment",
            "GET /event/{session_id}/status": "Verifica statusul",
            "GET /event/": "Obtine toate evenimentele",
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "Reservation Agent API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
