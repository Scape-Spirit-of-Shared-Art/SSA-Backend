import asyncio
import time
import uuid
from browser_use import Agent, Browser, ChatAnthropic, Tools
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from models import PersonalInfo, OrderComplete, AgentStatus, ReservationSession
import json

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
        
        tools = self.create_tools(session_id)
        
        task = self.create_task(user_prompt)

        agent = Agent(
            task=task,
            browser=self.browser,
            llm=self.llm,
            tools=tools,
            max_actions_per_step=10
        )
        
        asyncio.create_task(self.run_agent(session_id, agent))
        
        return session_id
    
    def create_tools(self, session_id: str):
        """Create tools for agent"""
        
        tools = Tools()
        
        @tools.action(description='Save collected personal info to file')
        def save_personal_info(info: PersonalInfo) -> str:
            session = self.sessions[session_id]
            session.personal_data = info.model_dump()
            session.updated_at = time.time()
            
            with open(f'personal_info_{session_id}.json', 'w') as f:
                json.dump(info.model_dump(), f, indent=2)
            return f'Personal information saved securely'

        @tools.action('Ask the human for required information that is missing.')
        def collect_personal_info(required_fields: list[str]) -> PersonalInfo:
            """Collect personal info through backend API"""
            session = self.sessions[session_id]
            
            session.status = AgentStatus.WAITING_FOR_INPUT
            session.required_fields = required_fields
            session.waiting_for_input = True
            session.updated_at = time.time()
            
            while session.waiting_for_input:
                time.sleep(0.1)

            return PersonalInfo(**session.personal_data)

        return tools

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
               that is NOT provided in the initial user prompt, you MUST use the 'collect_personal_info' tool to gather this information.
               DO NOT proceed without collecting the required information. DO NOT make up information.
               
               How to use collect_personal_info:
               - Identify which fields the form requires (e.g., first_name, last_name, email, phone, password, etc.)
               - Call collect_personal_info with a list of the required fields
               - Example: collect_personal_info(['first_name', 'last_name', 'email', 'phone', 'password'])
               - The tool will prompt the user for each field in the correct format and return a PersonalInfo object
               - Use the returned information to fill out the form fields
               
            7. After collecting all required information using collect_personal_info, complete the form and proceed with the order
            8. Continue until you reach the payment page, then let the user handle the payment
            
            User's request: {user_prompt}
            
            **CRITICAL**: Whenever you encounter a form field that requires information not in the user's original prompt, 
            you MUST call the collect_personal_info tool with the list of required fields. Do not stop or wait - actively use the tool to get the information you need.
            The task is only complete when you reach the payment page.
            
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
