import asyncio
import time
import uuid
from browser_use import Agent, Browser, ChatAnthropic, Tools
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from models import OrderComplete, AgentStatus, ReservationSession

load_dotenv()

class ReservationService:
    def __init__(self):
        self.sessions: Dict[str, ReservationSession] = {}
        self.browser = None
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-0",
            temperature=0.0,
            timeout=200
        )
    async def initialize_browser(self):
        """Initialize browser"""
        if self.browser is None:
            self.browser = Browser(
                    headless=False,
                    executable_path='/usr/bin/google-chrome-stable',
                    window_size={'width': 1080, 'height': 2400}
            )
            await self.browser.start()
    
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

        agent = Agent(
            task=task,
            browser=self.browser,
            llm=self.llm,
            max_actions_per_step=10
        )
        
        asyncio.create_task(self.run_agent(session_id, agent))
        
        return session_id

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
            6. **IMPORTANT**: When you reach a form that requests personal data (email, first name, last name, phone number, password, etc.), 
               you must STOP the automation completely and leave the browser open for the user to complete manually.
               
               Instructions for personal data forms:
               - Navigate to the personal information form but DO NOT fill any fields automatically
               - DO NOT use any tools to collect or input personal information
               - DO NOT make up any personal information
               - STOP all automation at this point
               - Leave the browser window open and visible for the user
               - Inform the user that they need to complete the personal information form manually
               - Wait indefinitely until the user manually completes the form and continues the process
               
            7. After the user has manually filled the personal information and submitted the form, the control will be in the user's hands
            as he will continue in order to reach the payment page. Then, he will proceed to make the payment so leave the browser open.
            
            User's request: {user_prompt}
            
            **CRITICAL**: When you encounter a personal information form, STOP automation immediately and leave the browser open. 
            DO NOT use any tools to collect personal information. Let the user complete the form manually in the browser.
            The task is only complete after the user makes the payment so leave the browser open.
            
            Do not close the browser until the payment is completed. Wait for the user to introduce his payment details.
        """
        
    async def run_agent(self, session_id: str, agent: Agent):
        """Run agent in background"""
        
        try:
            session = self.sessions[session_id]
            result = await agent.run()
            
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
    
    def cleanup_session(self, session_id: str):
        """Clean up session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

reservation_service = ReservationService()
