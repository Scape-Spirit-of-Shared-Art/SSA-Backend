import asyncio
import time
import uuid
from browser_use import Agent, Browser, ChatAnthropic, Tools
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from models import OrderComplete, AgentStatus, EventTicketSession, EventTicketRequest

load_dotenv()

class EventTicketService:
    def __init__(self):
        self.sessions: Dict[str, EventTicketSession] = {}
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
    
    async def start_booking_ticket(self, request: EventTicketRequest) -> str:
        """Start new reservation and return session_id"""
        
        session_id = str(uuid.uuid4())
        
        session = EventTicketSession(
            session_id=session_id,
            status=AgentStatus.WORKING,
            created_at=time.time(),
            updated_at=time.time(),
            event_url=request.event_url,
            ticket_count=request.ticket_count
        )
        
        self.sessions[session_id] = session
        
        await self.initialize_browser()
        
        task = self.create_task(request)

        agent = Agent(
            task=task,
            browser=self.browser,
            llm=self.llm,
            max_actions_per_step=10
        )
        
        asyncio.create_task(self.run_agent(session_id, agent))
        
        return session_id

    def create_task(self, request: EventTicketRequest) -> str:
        """Create optimized task for direct event URL booking"""
        return f"""You are an AI Agent specialized in booking tickets from direct event URLs.
            You have been provided with a direct link to an event page and need to book exactly {request.ticket_count} tickets.

            **DIRECT URL PROVIDED**: {request.event_url}
            **TICKETS REQUIRED**: {request.ticket_count}

            Your job will be to:
            1. **Navigate directly to the provided URL**: {request.event_url}
               - Do NOT search for events or organizations
               - Go straight to this exact URL
               
            2. **Locate the ticket booking section** on this specific event page
               - Look for "Buy Tickets", "Book Now", "Reserve", "Purchase" buttons
               - Find ticket selection or quantity options
               
            3. **Select exactly {request.ticket_count} tickets**
               - Choose the exact quantity requested: {request.ticket_count}
               - If there are different ticket types, choose the standard/general admission
               - Proceed to add tickets to cart or continue to checkout
               
            4. **Navigate through the booking process**
               - Follow the normal flow: select seats (if applicable) → add to cart → proceed to checkout
               - Continue until you reach a form asking for personal information
               
            5. **CRITICAL - When you encounter personal data forms (STOP IMMEDIATELY)**:
               - **RECOGNIZE personal info forms**: fields asking for name, email, phone, address, password, credit card, etc.
               - **STOP all automation** as soon as you see these fields
               - **DO NOT fill any personal information fields**
               - **DO NOT attempt to collect or input personal data**
               - **DO NOT use any tools for personal information**
               - **LEAVE THE BROWSER WINDOW OPEN and VISIBLE**
               - **INFORM the user**: "Personal information form detected. Please complete the form manually and proceed with payment."
               
            6. **After stopping at personal info form**:
               - **Your task is COMPLETE** when you reach the personal information form
               - **The user will take over** to complete personal details and payment
               - **DO NOT close the browser** - leave it open for the user
               - **DO NOT attempt to continue** - wait for user to handle the rest
               
            **SUCCESS CRITERIA**:
            ✓ Successfully navigated to: {request.event_url}
            ✓ Found and selected exactly {request.ticket_count} tickets
            ✓ Reached personal information/checkout form
            ✓ Stopped automation and left browser open for user
            
            **CRITICAL REMINDERS**:
            - NEVER fill personal information (name, email, phone, payment details)
            - ALWAYS stop when you see personal data forms
            - ALWAYS leave browser open and visible
            - User will complete personal info and payment manually
            - Your automation ends at the personal information form
            
            **WHAT TO AVOID**:
            - Do not search for events (you have direct URL)
            - Do not guess or make up personal information
            - Do not attempt to complete checkout
            - Do not close the browser window
            - Do not continue past personal information forms
        """
        
    async def run_agent(self, session_id: str, agent: Agent):
        """Run agent in background with proper status tracking"""
        
        try:
            session = self.sessions[session_id]

            session.status = AgentStatus.NAVIGATION_TO_EVENT
            session.updated_at = time.time()
            
            result = await agent.run()
            

            result_str = str(result).lower()
            
            if "personal" in result_str or "information" in result_str or "form" in result_str:
    
                session.status = AgentStatus.WAITING_FOR_INPUT
                session.result = {
                    "message": "Successfully reached personal information form. Browser left open for user to complete.",
                    "result": str(result),
                    "next_action": "User should complete personal information and payment manually"
                }
            elif "payment" in result_str or "checkout" in result_str:
                session.status = AgentStatus.READY_FOR_PAYMENT
                session.result = {
                    "message": "Successfully reached payment page. Browser left open for user.",
                    "result": str(result),
                    "next_action": "User should complete payment manually"
                }
            else:
                session.status = AgentStatus.COMPLETED
                session.result = {
                    "message": "Ticket booking process completed. Browser left open for user.",
                    "result": str(result)
                }
            
            session.updated_at = time.time()
        
        except Exception as e:
            session = self.sessions[session_id]
            session.status = AgentStatus.ERROR
            session.error = str(e)
            session.updated_at = time.time()
    
    def get_session_status(self, session_id: str) -> Optional[EventTicketSession]:
        """Get session status"""
        return self.sessions.get(session_id)
    
    def cleanup_session(self, session_id: str):
        """Clean up session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

event_ticket_service = EventTicketService()
