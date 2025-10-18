from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reservation_service import reservation_service
from models import ReservationSession, AgentStatus
from pydantic import BaseModel, Field

class StartReservationRequest(BaseModel):
    user_prompt: str = Field(..., description="User's reservation request", min_length=1)

class StartReservationResponse(BaseModel):
    session_id: str
    status: str
    message: str = "Reservation process started"

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.post("/start", response_model=StartReservationResponse)
async def start_reservation(request: StartReservationRequest):
    """
    Starts a new reservation
    
    - **user_prompt**: User's request
    """
    try:
        session_id = await reservation_service.start_reservation(request.user_prompt)
        
        return StartReservationResponse(
            session_id=session_id,
            status=AgentStatus.WORKING.value,
            message="The reservation process started"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error at the reservation starting: {str(e)}")


@router.get("/{session_id}/status")
async def get_reservation_status(session_id: str):
    """
    Verifies the status of a reservation
    
    - **session_id**: Reservation session ID
    """
    session = reservation_service.get_session_status(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="The session wasn't found")
    
    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "user_prompt": session.user_prompt,
        "waiting_for_input": session.waiting_for_input,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "result": session.result,
        "error": session.error
    }

@router.delete("/{session_id}")
async def cleanup_session(session_id: str):
    """
    Deletes reservation's session
    
    - **session_id**: Reservation session ID
    """
    reservation_service.cleanup_session(session_id)
    
    return {"message": f"The session {session_id} was deleted successfully"}


@router.get("/")
async def get_all_sessions():
    """
    Obtains all active sessions
    """
    sessions = {}
    for session_id, session in reservation_service.sessions.items():
        sessions[session_id] = {
            "status": session.status.value,
            "user_prompt": session.user_prompt[:100] + "..." if len(session.user_prompt) > 100 else session.user_prompt,
            "waiting_for_input": session.waiting_for_input,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
    
    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }

