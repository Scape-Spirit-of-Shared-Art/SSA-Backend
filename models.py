from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, Any, Optional

class PersonalInfo(BaseModel):
    first_name: str = Field(description='First name of the user')
    last_name: str = Field(description='Last name of the user')
    email: str = Field(description='Email of the user')
    phone: str = Field(description='Phone number')
    password: str = Field(description='Password for user account')
    newsletter_subscription: bool = Field(description='Whether to subscribe to newsletter', default=False)
    terms_and_cond_acceptance: bool = Field(description='Whether t&c are accepted', default=False)

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

class ReservationSession(BaseModel):
    session_id: str
    status: AgentStatus
    user_prompt: str
    required_fields: Optional[list[str]] = None
    personal_data: Optional[Dict[str, Any]] = None
    waiting_for_input: bool = False
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
