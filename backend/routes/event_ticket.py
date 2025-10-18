from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from event_ticket_service import event_ticket_service
from models import EventTicketSession, AgentStatus, EventTicketRequest
from pydantic import BaseModel, Field

class StartBookingRequest(BaseModel):
    event_url: str = Field(..., description="URL of the event", min_length=1)
    ticket_count: int = Field(..., description="Number of tickets", gt=0, le=10)

class StartBookingResponse(BaseModel):
    session_id: str
    status: str
    message: str = "Booking process started"

router = APIRouter(prefix="/event", tags=["event"])

@router.post("/start", response_model=StartBookingResponse)
async def start_booking_ticket(request: StartBookingRequest):
    """
    Starts tickets' booking for an event

    - **event_url**: webiste URL of the event
    - **ticket_count**: Number of tickets
    """
    
    try:
        session_id = await event_ticket_service.start_booking_ticket(request)
        
        return StartBookingResponse(
            session_id=session_id,
            status=AgentStatus.WORKING.value,
            message="Booking process started successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error at the start of booking: {str(e)}")

@router.get("/{session_id}/status")
async def get_event_status(session_id: str):
    """
    Check the status of an event booking 

    Args:
        session_id: Event booking session ID
    """
    session = event_ticket_service.get_session_status(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session wasn't found")
    
    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "result": session.result,
        "error": session.error
    }

@router.get("/")
async def get_all_sessions():
    """
    Get all the active sessions (for debug)
    """
    
    sessions = {}
    for session_id, session in event_ticket_service.sessions.items():
        sessions[session_id] = {
            "status": session.status.value,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
    
    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }