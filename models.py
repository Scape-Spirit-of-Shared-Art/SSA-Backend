from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, Any, Optional

class OrderComplete(BaseModel):
    website: str = Field(description='The URL of the website from where the ticket waas bought')
    event_name: str = Field(description='The name of the event the user is attending')
    date: str = Field(description='The date of the event')
    ticket_number: int = Field(description='The number of tickets requested by the user')

class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    ERROR = "error"
    NAVIGATION_TO_EVENT = "navigating"
    SELECTING_TICKETS = "selecting"
    READY_FOR_PAYMENT = "payment_reached"

class EventTicketRequest(BaseModel):
    event_url: str = Field(description='URL of the event')
    ticket_count: int = Field(description='Number of tickets requested by the user')

class EventTicketSession(BaseModel):
    session_id: str
    status: AgentStatus
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    event_url: str
    ticket_count: int

class ReservationSession(BaseModel):
    session_id: str
    status: AgentStatus
    user_prompt: str
    waiting_for_input: bool = False
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TicketPurchaseResult(BaseModel):
    success: bool
    order_id: Optional[str]
    total_amount: Optional[int]
    error_message: Optional[str]