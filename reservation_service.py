import asyncio
import time
import uuid
from browser_use.agent.service import AgentService
from browser_use.browser.service import BrowserService
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from models import PersonalInfo, OrderComplete, AgentStatus, ReservationSession
import json

load_dotenv()

class ReservationService:
    def __init__(self):
        self.sessions: Dict[str, ReservationSession] = {}
        self.browser_service = None
        self.agent_service = None
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.0,
            timeout=200
        )
    async def initialize_browser(self):
        """Initialize browser"""
        if self.browser_service is None:
            self.browser_service = BrowserService(
                headless=False,
                executable_path='/usr/bin/google-chrome-stable',
                window_size={'width': 1080, 'height': 2400}
            )
            await self.browser_service.start()
    
    async def start_reservation(self, user_prompt: str) -> str:
        """Start new reservation and return session_id"""
        
        session_id = str(uuid.uuid4())
        
        session = ReservationSession(
            session_id=session_id,
            status=AgentStatus.WORKING,
            user_prompt=user_prompt,
            created_at=time.time(),
            updated_at=time.time()
        )
        
        self.sessions[session_id] = session
        
        await self.initialize_browser()
        
        task = self.create_task(user_prompt)

        # Create agent service with the new API
        agent_service = AgentService(
            task=task,
            llm=self.llm,
            use_vision=True
        )
        
        asyncio.create_task(self.run_agent(session_id, agent_service))
        
        return session_id
    
    # Note: The new browser_use API doesn't use the same tools system
    # Personal info collection will need to be handled differently
    # For now, we'll implement a simpler approach

    def create_task(self, user_prompt: str) -> str:
        """Create the agent task"""
        return f"""You are an AI Agent destined to book reservations or buy tickets
            for museum exhibitions, theatre plays, philharmonic shows or any other cultural events.
            You will receive a prompt from the user requesting you to buy tickets or book reservations.

            Your job will be to:
            1. Find the official website of the event organizer (the event organizer will be specified by the user)
            2. Search for the event desired by the user. If the user specifies an hour or date, you should also look for this
            3. Find the tickets' section
            4. Buy the the number of tickets (it will be specified by the user)
            5. Choose the requested tickets
            6. **IMPORTANT**: When the website requests personal data (email, first name, last name, phone number, password, etc.) 
               that is NOT provided in the initial user prompt, you MUST pause and inform the user that additional information is needed.
               DO NOT proceed without the required information. DO NOT make up information.
               
            7. After collecting all required information, complete the form and proceed with the order
            8. Continue until you reach the payment page, then let the user handle the payment
            
            User's request: {user_prompt}
            
            **CRITICAL**: Whenever you encounter a form field that requires information not in the user's original prompt, 
            you MUST pause and inform the user about what information is needed. The task is only complete when you reach the payment page.
            
            Do not close the browser until the payment is completed. Wait for the user to introduce his payment details.
        """
        
    async def run_agent(self, session_id: str, agent_service: AgentService):
        """Run agent in background"""
        
        try:
            session = self.sessions[session_id]
            result = await agent_service.run()
            
            session.status = AgentStatus.COMPLETED
            session.result = {"message": "Reservation completed", "result": str(result)}
            session.updated_at = time.time()
        
        except Exception as e:
            session = self.sessions[session_id]
            session.status = AgentStatus.ERROR
            session.error = str(e)
            session.updated_at = time.time()
    
    def get_session_status(self, session_id: str) -> Optional[ReservationSession]:
        """Get session status"""
        return self.sessions.get(session_id)
    
    def provide_personal_info(self, session_id: str, personal_data: Dict[str, Any]) -> bool:
        """Provide personal information to continue agent"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.personal_data = personal_data
        session.waiting_for_input = False
        session.status = AgentStatus.WORKING
        session.updated_at = time.time()
        
        return True
    
    def cleanup_session(self, session_id: str):
        """Clean up session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

reservation_service = ReservationService()
