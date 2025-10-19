from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from pathlib import Path
import json
import uuid
import os
import sys
import cv2
import numpy as np
import time
import threading
import asyncio
import platform
from contextlib import asynccontextmanager
from database_service import db_service

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import backend routes
from backend.routes.reservations import router as reservations_router
from backend.routes.event_ticket import router as event_ticket_router

# Camera Detection System
class PeopleDetectionStream:
    def __init__(self, camera_source=0):
        try:
            from ultralytics import YOLO
            self.model = YOLO('yolov8m-seg.pt')
        except ImportError:
            print("Warning: ultralytics not available. Camera detection will be disabled.")
            self.model = None
        
        self.camera_source = camera_source
        self.cap = None
        self.people_count = 0
        self.last_frame = None
        self.last_processed_frame = None
        self.is_running = False
        self.lock = threading.Lock()
        
        # Overlay color and transparency
        self.color = (0, 255, 0)  # BGR: Green
        self.alpha = 0.6
    
    def get_camera_backend(self):
        """Get the appropriate camera backend for the current platform"""
        if platform.system() == 'Darwin':  # macOS
            return cv2.CAP_AVFOUNDATION
        else:  # Windows/Linux
            return cv2.CAP_DSHOW
        
    def list_available_cameras(self):
        """List all available cameras, prioritizing USB cameras"""
        available_cameras = []
        usb_cameras = []
        print("\n🔍 Căutare camere USB...")
        
        # Check indices 1-10 for USB cameras first
        backend = self.get_camera_backend()
        for i in range(1, 10):
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    available_cameras.append(i)
                    usb_cameras.append(i)
                    print(f"✅ Camera USB găsită la indexul {i}")
                cap.release()
        
        # Only check built-in camera (0) if no USB cameras found
        if not usb_cameras:
            print("⚠️  Nicio cameră USB găsită, verific camera integrată...")
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    available_cameras.append(0)
                    print(f"ℹ️  Camera integrată găsită la indexul 0")
                cap.release()
        
        if not available_cameras:
            print("❌ Nicio cameră găsită")
        else:
            if usb_cameras:
                print(f"\n📹 Camere USB disponibile: {usb_cameras}")
        
        return available_cameras
    
    def initialize_camera(self):
        """Initialize the camera"""
        if self.model is None:
            print("❌ YOLO model not available. Camera detection disabled.")
            return False
            
        # List available cameras first
        available_cameras = self.list_available_cameras()
        
        if not available_cameras:
            print("\n⚠️  Nu am găsit nicio cameră USB.")
            print("💡 Asigură-te că:")
            print("   - Camera USB este conectată")
            print("   - Driverele sunt instalate")
            print("   - Camera nu este folosită de altă aplicație")
            return False
        
        # Try to open the specified camera first
        print(f"\n🎥 Încerc să deschid camera USB {self.camera_source}...")
        backend = self.get_camera_backend()
        self.cap = cv2.VideoCapture(self.camera_source, backend)
        
        if not self.cap.isOpened():
            # Try the first available camera as fallback
            print(f"⚠️  Camera USB {self.camera_source} nu este disponibilă.")
            print(f"🔄 Încerc prima cameră disponibilă: {available_cameras[0]}")
            self.camera_source = available_cameras[0]
            self.cap = cv2.VideoCapture(self.camera_source, backend)
        
        if self.cap.isOpened():
            # Configure camera settings
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 60)
            self.is_running = True
            print(f"✅ Camera {self.camera_source} deschisă cu succes!")
            
            # Print actual camera properties
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            print(f"📹 Rezoluție: {int(actual_width)}x{int(actual_height)} @ {int(actual_fps)} FPS")
            return True
        
        print("❌ Nu am putut deschide nicio cameră")
        return False
    
    def color_exact_people(self, frame, results):
        """Color detected people using segmentation masks"""
        people_count = 0
        
        for result in results:
            if getattr(result, 'masks', None) is not None:
                masks = result.masks
                boxes = result.boxes

                for i, (box, mask) in enumerate(zip(boxes, masks)):
                    confidence = float(box.conf[0].cpu().numpy())

                    if confidence > 0.5:
                        people_count += 1

                        # Mask data (float [0..1]) -> resize to frame size
                        mask_data = mask.data[0].cpu().numpy()
                        mask_resized = cv2.resize(mask_data, (frame.shape[1], frame.shape[0]))

                        # Binary mask 0 or 255 (uint8) for OpenCV operations
                        mask_binary = (mask_resized > 0.5).astype(np.uint8) * 255

                        # Create 3-channel mask for broadcasting
                        mask_3c = cv2.merge([mask_binary, mask_binary, mask_binary])

                        # Red overlay image
                        red_overlay = np.zeros_like(frame, dtype=np.uint8)
                        red_overlay[:] = self.color

                        # Alpha blend the red overlay with the original frame
                        blended = cv2.addWeighted(frame, 1.0 - self.alpha, red_overlay, self.alpha, 0)

                        # Replace masked pixels with blended pixels
                        frame = np.where(mask_3c == 255, blended, frame).astype(np.uint8)
        
        return frame, people_count
    
    def process_frame(self, frame):
        """Process frame with YOLO and return processed frame"""
        if self.model is None:
            return frame, 0
            
        results = self.model(
            frame,
            classes=[0],      # Only detect people
            conf=0.4,         # Confidence threshold
            iou=0.5,          # IoU threshold
            imgsz=416,        # Image size
            half=False,       # Full precision
            max_det=20,       # Max detections
            vid_stride=1,     # Process all frames
            stream=False,
            device='cpu',     # Change to 'cuda' if GPU available
            verbose=False
        )
        
        # Apply segmentation coloring
        processed_frame, people_count = self.color_exact_people(frame.copy(), results)
        
        # Add overlay information
        current_time = time.strftime("%H:%M:%S")
        cv2.putText(processed_frame, f'PEOPLE: {people_count}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(processed_frame, f'TIME: {current_time}', 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Alert for high density
        if people_count > 15:
            cv2.putText(processed_frame, 'HIGH DENSITY!', 
                       (150, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        return processed_frame, people_count
    
    def get_frame(self):
        """Read a frame from the camera"""
        if self.cap is None or not self.cap.isOpened():
            return None, None
        
        ret, frame = self.cap.read()
        if not ret:
            return None, None
        
        return frame, frame.copy()
    
    def release(self):
        """Release camera resources"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()

# Global camera detector instance
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))
detector = PeopleDetectionStream(camera_source=CAMERA_INDEX)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database connection and camera on startup and cleanup on shutdown"""
    # Startup
    await db_service.connect()
    
    # Initialize camera
    print("\n" + "="*60)
    print("🚀 SSA Backend Admin API - Starting...")
    print("="*60)
    if detector.initialize_camera():
        print("✅ Camera system ready!")
    else:
        print("⚠️  Camera system not available (ultralytics not installed or no camera found)")
    print("="*60 + "\n")
    
    yield
    
    # Shutdown
    detector.release()
    await db_service.disconnect()

app = FastAPI(title="SSA Backend Admin API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost:4201", "http://127.0.0.1:4201"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Mount static files to serve uploaded images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include backend routers
app.include_router(reservations_router)
app.include_router(event_ticket_router)

# Valid categories for places
VALID_CATEGORIES = ["REFINED_SIDE", "FUN_SIDE", "SPORT_SPHERE", "CITY_TREASURES"]

class Event(BaseModel):
    name: str = Field(description="Name of the event")
    bio: str = Field(description="Short description of the event")
    max_participants: int = Field(description="Maximum number of participants")
    website: str = Field(description="URL of the event website")
    email: str = Field(description="Email for contact")
    phone_number: str = Field(description="Phone number for contact")
    address: str = Field(description="Address of the event location")
    program: List[str] = Field(description="List of scheduled activities for the event")
    images_paths: List[str] = Field(description="List of image paths for the event")

class Place(BaseModel):
    name: str = Field(description="Name of the place")
    bio: str = Field(description="Short description of the place")
    website: str = Field(description="URL of the website")
    email: str = Field(description="Email for contact")
    phone_number: str = Field(description="Phone number for contact")
    address: str = Field(description="Address of the place")
    floormaps: dict = Field(description="JSON object containing floor map data")
    categories: List[str] = Field(description="List of categories for the place")
    password: str = Field(description="Password for authentication")
    monday_friday: str = Field(description="Schedule from Monday to Friday")
    saturday: str = Field(description="Schedule for Saturday")
    sunday: str = Field(description="Schedule for Sunday")
    events: List[Event] = Field(description="List of events at the place")
    image_path: str = Field(description="Path to the image file for the place")
    
    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v):
        if not v:
            raise ValueError('Categories list cannot be empty')
        for category in v:
            if category not in VALID_CATEGORIES:
                raise ValueError(f'Invalid category: {category}. Valid categories are: {VALID_CATEGORIES}')
        return v


class UpdatePlace(BaseModel):
    name: Optional[str] = Field(description="Name of the place")
    bio: Optional[str] = Field(description="Short description of the place")
    website: Optional[str] = Field(description="URL of the website")
    email: Optional[str] = Field(description="Email for contact")
    phone_number: Optional[str] = Field(description="Phone number for contact")
    address: Optional[str] = Field(description="Address of the place")
    floormaps: Optional[dict] = Field(description="JSON object containing floor map data")
    categories: Optional[List[str]] = Field(description="List of categories for the place")
    password: Optional[str] = Field(description="Password for authentication")
    monday_friday: Optional[str] = Field(description="Schedule from Monday to Friday")
    saturday: Optional[str] = Field(description="Schedule for Saturday")
    sunday: Optional[str] = Field(description="Schedule for Sunday")
    events: Optional[List[Event]] = Field(description="List of events at the place")
    image_path: Optional[str] = Field(description="Path to the image file for the place")
    
    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v):
        if v is not None:
            if not v:
                raise ValueError('Categories list cannot be empty')
            for category in v:
                if category not in VALID_CATEGORIES:
                    raise ValueError(f'Invalid category: {category}. Valid categories are: {VALID_CATEGORIES}')
        return v
    

# Database connection is now handled by the lifespan context manager

@app.get("/")
def read_root():
    return {
        "message": "SSA Backend Admin API", 
        "docs": "/docs",
        "description": "API for SSA cultural reservation system - places, events, and reservations",
        "endpoints": {
            "admin": {
                "GET /places": "Get all places",
                "POST /new_place": "Create a new place",
                "GET /places/{place_id}": "Get place by ID",
                "PUT /edit_place/{place_id}": "Update place",
                "DELETE /delete_place/{place_id}": "Delete place",
                "POST /upload-image": "Upload image file",
                "GET /categories": "Get valid categories"
            },
            "events": {
                "POST /places/{place_id}/events": "Create event for place",
                "GET /places/{place_id}/events": "Get events for place",
                "GET /places/{place_id}/events/{event_id}": "Get specific event",
                "PUT /places/{place_id}/events/{event_id}": "Update event",
                "DELETE /places/{place_id}/events/{event_id}": "Delete event"
            },
            "reservations": {
                "POST /reservations/start": "Start new reservation",
                "GET /reservations/{session_id}/status": "Check reservation status",
                "DELETE /reservations/{session_id}": "Delete reservation session",
                "GET /reservations/": "Get all active sessions"
            },
            "event_tickets": {
                "POST /event/start": "Start event ticket booking",
                "GET /event/{session_id}/status": "Check booking status",
                "GET /event/": "Get all booking sessions"
            },
            "camera": {
                "GET /camera/raw": "Stream raw camera feed",
                "GET /camera/processed": "Stream processed camera feed with people detection",
                "GET /camera/people_count": "Get current people count"
            }
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "SSA Backend Admin API is running"}

@app.get("/categories")
def get_valid_categories():
    """Get list of valid categories for places"""
    return {"categories": VALID_CATEGORIES}

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file and return the path"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Return the path that can be used to access the image
        return {"image_path": f"/uploads/{unique_filename}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@app.post("/new_place")
async def create_place(place: Place):
    """Create a new place"""
    try:
        place_dict = place.model_dump()
        created_place = await db_service.create_place(place_dict)
        return {"id": created_place.id, "place": created_place}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating place: {str(e)}")

@app.get("/places")
async def get_list_of_places():
    """Get all places"""
    try:
        places = await db_service.get_all_places()
        print(f"DEBUG: Found {len(places)} places")
        
        # Convert places to match frontend expectations
        converted_places = []
        
        # Hardcode "Filarmonica Oltenia" to appear as 3rd place
        filarmonica_oltenia = None
        other_places = []
        
        for place in places:
            print(f"DEBUG: Place {place.id} has {len(place.events) if place.events else 0} events")
            
            # Convert events for this place
            converted_events = []
            if place.events:
                for event in place.events:
                    print(f"DEBUG: Event {event.id} imagesPaths raw: {event.imagesPaths}")
                    
                    # Parse images_paths
                    try:
                        if event.imagesPaths:
                            parsed_images = json.loads(event.imagesPaths)
                            print(f"DEBUG: Event {event.id} parsed images: {parsed_images}")
                        else:
                            parsed_images = []
                            print(f"DEBUG: Event {event.id} no imagesPaths, using empty array")
                    except Exception as e:
                        print(f"DEBUG: Event {event.id} JSON parse error: {e}")
                        parsed_images = []
                    
                    converted_event = {
                        'id': str(event.id),
                        'name': event.name,
                        'bio': event.bio,
                        'max_participants': event.maxParticipants,
                        'website': event.website,
                        'email': event.email,
                        'phone_number': event.phoneNumber,
                        'address': event.address,
                        'program': json.loads(event.program) if event.program else [],
                        'images_paths': parsed_images,
                        'date': event.date
                    }
                    converted_events.append(converted_event)
            
            # Create converted place
            converted_place = {
                'id': place.id,
                'name': place.name,
                'bio': place.bio,
                'website': place.website,
                'email': place.email,
                'phone_number': place.phoneNumber,
                'address': place.address,
                'floormaps': json.loads(place.floormaps) if place.floormaps else {},
                'categories': json.loads(place.categories) if place.categories else [],
                'password': place.password,
                'monday_friday': place.mondayFriday,
                'saturday': place.saturday,
                'sunday': place.sunday,
                'imagePath': place.imagePath,  # Changed from image_path to imagePath to match frontend interface
                'events': converted_events
            }
            
            # Separate "Filarmonica Oltenia" from other places
            if place.name.lower() == "teatrul național marin sorescu":
                filarmonica_oltenia = converted_place
            else:
                other_places.append(converted_place)
        
        # Reorder places: first 2 other places, then Filarmonica Oltenia, then the rest
        if filarmonica_oltenia:
            # Take first 2 other places
            first_two = other_places[:2]
            # Add Filarmonica Oltenia as 3rd
            converted_places.extend(first_two)
            converted_places.append(filarmonica_oltenia)
            # Add the rest
            converted_places.extend(other_places[2:])
        else:
            # If Filarmonica Oltenia not found, return all places as normal
            converted_places = other_places
        
        return {"places": converted_places}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching places: {str(e)}")

@app.get("/places/{place_id}")
async def get_place_by_id(place_id: int):
    """Get a specific place by ID"""
    try:
        place = await db_service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        # Convert events for this place (same logic as get_all_places)
        converted_events = []
        if place.events:
            for event in place.events:
                print(f"DEBUG: Event {event.id} imagesPaths raw: {event.imagesPaths}")
                
                # Parse images_paths
                try:
                    if event.imagesPaths:
                        parsed_images = json.loads(event.imagesPaths)
                        print(f"DEBUG: Event {event.id} parsed images: {parsed_images}")
                    else:
                        parsed_images = []
                        print(f"DEBUG: Event {event.id} no imagesPaths, using empty array")
                except Exception as e:
                    print(f"DEBUG: Event {event.id} JSON parse error: {e}")
                    parsed_images = []
                
                converted_event = {
                    'id': str(event.id),
                    'name': event.name,
                    'bio': event.bio,
                    'max_participants': event.maxParticipants,
                    'website': event.website,
                    'email': event.email,
                    'phone_number': event.phoneNumber,
                    'address': event.address,
                    'program': json.loads(event.program) if event.program else [],
                    'images_paths': parsed_images,
                    'date': event.date
                }
                converted_events.append(converted_event)
        
        # Create converted place with converted events
        converted_place = {
            'id': place.id,
            'name': place.name,
            'bio': place.bio,
            'website': place.website,
            'email': place.email,
            'phone_number': place.phoneNumber,
            'address': place.address,
            'floormaps': json.loads(place.floormaps) if place.floormaps else {},
            'categories': json.loads(place.categories) if place.categories else [],
            'password': place.password,
            'monday_friday': place.mondayFriday,
            'saturday': place.saturday,
            'sunday': place.sunday,
            'imagePath': place.imagePath,  # Use imagePath (camelCase) to match frontend interface
            'events': converted_events
        }
        
        return {"place": converted_place}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching place: {str(e)}")

@app.delete("/delete_place/{place_id}")
async def delete_place(place_id: int):
    """Delete a place by ID"""
    try:
        deleted_place = await db_service.delete_place(place_id)
        if not deleted_place:
            raise HTTPException(status_code=404, detail="Place not found")
        return {"status": "success", "deleted_place": deleted_place}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting place: {str(e)}")

@app.put("/edit_place/{place_id}")
async def update_place(place_id: int, updated_place: UpdatePlace):
    """Update a place by ID"""
    try:
        # Convert Pydantic model to dict, excluding unset fields
        updated_data = updated_place.model_dump(exclude_unset=True)
        updated_place_result = await db_service.update_place(place_id, updated_data)
        if not updated_place_result:
            raise HTTPException(status_code=404, detail="Place not found")
        return {"status": "success", "updated_place": updated_place_result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating place: {str(e)}")

# Event Management Endpoints

class CreateEvent(BaseModel):
    name: str = Field(description="Name of the event")
    bio: str = Field(description="Short description of the event")
    max_participants: int = Field(description="Maximum number of participants")
    website: str = Field(description="URL of the event website")
    email: str = Field(description="Email for contact")
    phone_number: str = Field(description="Phone number for contact")
    address: str = Field(description="Address of the event location")
    program: List[str] = Field(description="List of scheduled activities for the event")
    images_paths: List[str] = Field(description="List of image paths for the event")
    date: Optional[str] = Field(description="Date of the event (ISO format)")

class UpdateEvent(BaseModel):
    name: Optional[str] = Field(description="Name of the event")
    bio: Optional[str] = Field(description="Short description of the event")
    max_participants: Optional[int] = Field(description="Maximum number of participants")
    website: Optional[str] = Field(description="URL of the event website")
    email: Optional[str] = Field(description="Email for contact")
    phone_number: Optional[str] = Field(description="Phone number for contact")
    address: Optional[str] = Field(description="Address of the event location")
    program: Optional[List[str]] = Field(description="List of scheduled activities for the event")
    images_paths: Optional[List[str]] = Field(description="List of image paths for the event")
    date: Optional[str] = Field(description="Date of the event (ISO format)")

@app.post("/places/{place_id}/events")
async def create_event(place_id: int, event: CreateEvent):
    """Create a new event for a specific place"""
    try:
        # Get the place first
        place = await db_service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        # Create the event using the database service
        event_dict = event.model_dump()
        
        # Create the event in the database
        from prisma import Prisma
        prisma = Prisma()
        await prisma.connect()
        
        try:
            created_event = await prisma.event.create(
                data={
                    'name': event_dict['name'],
                    'bio': event_dict['bio'],
                    'maxParticipants': event_dict['max_participants'],
                    'website': event_dict['website'],
                    'email': event_dict['email'],
                    'phoneNumber': event_dict['phone_number'],
                    'address': event_dict['address'],
                    'program': json.dumps(event_dict['program']),
                    'imagesPaths': json.dumps(event_dict['images_paths']),
                    'date': event_dict.get('date'),
                    'placeId': place_id
                }
            )
            
            # Convert the created event to match frontend expectations
            converted_event = {
                'id': str(created_event.id),
                'name': created_event.name,
                'bio': created_event.bio,
                'max_participants': created_event.maxParticipants,
                'website': created_event.website,
                'email': created_event.email,
                'phone_number': created_event.phoneNumber,
                'address': created_event.address,
                'program': json.loads(created_event.program) if created_event.program else [],
                'images_paths': json.loads(created_event.imagesPaths) if created_event.imagesPaths else [],
                'date': created_event.date
            }
            
            # Get updated place with events
            updated_place = await db_service.get_place_by_id(place_id)
            
            return {"status": "success", "event": converted_event, "place": updated_place}
            
        finally:
            await prisma.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@app.get("/places/{place_id}/events")
async def get_place_events(place_id: int):
    """Get all events for a specific place"""
    try:
        place = await db_service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        # Convert events to match frontend expectations
        events = []
        if hasattr(place, 'events') and place.events:
            for event in place.events:
                print(f"DEBUG: Event {event.id} - imagesPaths raw: {event.imagesPaths}")
                print(f"DEBUG: Event {event.id} - imagesPaths type: {type(event.imagesPaths)}")
                
                # Try to parse images_paths
                try:
                    if event.imagesPaths:
                        parsed_images = json.loads(event.imagesPaths)
                        print(f"DEBUG: Event {event.id} - parsed images successfully: {parsed_images}")
                    else:
                        parsed_images = []
                        print(f"DEBUG: Event {event.id} - no imagesPaths, using empty array")
                except Exception as e:
                    print(f"DEBUG: Event {event.id} - JSON parse error: {e}")
                    parsed_images = []
                
                converted_event = {
                    'id': str(event.id),
                    'name': event.name,
                    'bio': event.bio,
                    'max_participants': event.maxParticipants,
                    'website': event.website,
                    'email': event.email,
                    'phone_number': event.phoneNumber,
                    'address': event.address,
                    'program': json.loads(event.program) if event.program else [],
                    'images_paths': parsed_images,
                    'date': event.date
                }
                print(f"DEBUG: Event {event.id} - final converted images_paths: {converted_event['images_paths']}")
                events.append(converted_event)
        
        return {"events": events}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")

@app.get("/places/{place_id}/events/{event_id}")
async def get_event(place_id: int, event_id: str):
    """Get a specific event by ID"""
    try:
        place = await db_service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        # Find the event in the place's events
        event = None
        if hasattr(place, 'events') and place.events:
            for e in place.events:
                if str(e.id) == event_id:
                    event = e
                    break
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Convert event to match frontend expectations
        converted_event = {
            'id': str(event.id),
            'name': event.name,
            'bio': event.bio,
            'max_participants': event.maxParticipants,
            'website': event.website,
            'email': event.email,
            'phone_number': event.phoneNumber,
            'address': event.address,
            'program': json.loads(event.program) if event.program else [],
            'images_paths': json.loads(event.imagesPaths) if event.imagesPaths else [],
            'date': event.date
        }
        
        return {"event": converted_event}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching event: {str(e)}")

@app.put("/places/{place_id}/events/{event_id}")
async def update_event(place_id: int, event_id: str, updated_event: UpdateEvent):
    """Update a specific event"""
    try:
        place = await db_service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        # Check if event exists
        event_exists = False
        if hasattr(place, 'events') and place.events:
            for e in place.events:
                if str(e.id) == event_id:
                    event_exists = True
                    break
        
        if not event_exists:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Update the event using Prisma
        from prisma import Prisma
        prisma = Prisma()
        await prisma.connect()
        
        try:
            # Convert field names to match database schema
            updated_data = updated_event.model_dump(exclude_unset=True)
            converted_data = {}
            
            for key, value in updated_data.items():
                if key == 'max_participants':
                    converted_data['maxParticipants'] = value
                elif key == 'phone_number':
                    converted_data['phoneNumber'] = value
                elif key == 'images_paths':
                    converted_data['imagesPaths'] = json.dumps(value) if value else None
                elif key == 'program':
                    converted_data['program'] = json.dumps(value) if value else None
                else:
                    converted_data[key] = value
            
            # Update the event in the database
            updated_event_db = await prisma.event.update(
                where={'id': int(event_id)},
                data=converted_data
            )
            
            # Convert the updated event to match frontend expectations
            converted_event = {
                'id': str(updated_event_db.id),
                'name': updated_event_db.name,
                'bio': updated_event_db.bio,
                'max_participants': updated_event_db.maxParticipants,
                'website': updated_event_db.website,
                'email': updated_event_db.email,
                'phone_number': updated_event_db.phoneNumber,
                'address': updated_event_db.address,
                'program': json.loads(updated_event_db.program) if updated_event_db.program else [],
                'images_paths': json.loads(updated_event_db.imagesPaths) if updated_event_db.imagesPaths else [],
                'date': updated_event_db.date
            }
            
            # Get updated place with events
            updated_place = await db_service.get_place_by_id(place_id)
            
            return {"status": "success", "event": converted_event, "place": updated_place}
            
        finally:
            await prisma.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")

@app.delete("/places/{place_id}/events/{event_id}")
async def delete_event(place_id: int, event_id: str):
    """Delete a specific event"""
    try:
        place = await db_service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        # Find the event to delete
        event_to_delete = None
        if hasattr(place, 'events') and place.events:
            for e in place.events:
                if str(e.id) == event_id:
                    event_to_delete = e
                    break
        
        if not event_to_delete:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Delete the event using Prisma
        from prisma import Prisma
        prisma = Prisma()
        await prisma.connect()
        
        try:
            # Delete the event from the database
            await prisma.event.delete(
                where={'id': int(event_id)}
            )
            
            # Convert the deleted event to match frontend expectations
            deleted_event = {
                'id': str(event_to_delete.id),
                'name': event_to_delete.name,
                'bio': event_to_delete.bio,
                'max_participants': event_to_delete.maxParticipants,
                'website': event_to_delete.website,
                'email': event_to_delete.email,
                'phone_number': event_to_delete.phoneNumber,
                'address': event_to_delete.address,
                'program': json.loads(event_to_delete.program) if event_to_delete.program else [],
                'images_paths': json.loads(event_to_delete.imagesPaths) if event_to_delete.imagesPaths else [],
                'date': event_to_delete.date
            }
            
            # Get updated place with events
            updated_place = await db_service.get_place_by_id(place_id)
            
            return {"status": "success", "deleted_event": deleted_event, "place": updated_place}
            
        finally:
            await prisma.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")

# Camera Streaming Functions
async def generate_raw_frames():
    """Generate raw camera frames"""
    while True:
        frame, _ = detector.get_frame()
        if frame is None:
            await asyncio.sleep(0.016)  # ~60 FPS
            continue
        
        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        await asyncio.sleep(0.016)  # ~60 FPS

async def generate_processed_frames():
    """Generate processed frames with people detection"""
    while True:
        frame, _ = detector.get_frame()
        if frame is None:
            await asyncio.sleep(0.016)  # ~60 FPS
            continue
        
        # Process frame with YOLO
        processed_frame, people_count = detector.process_frame(frame)
        
        # Update global count
        with detector.lock:
            detector.people_count = people_count
            detector.last_processed_frame = processed_frame
        
        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        await asyncio.sleep(0.016)  # ~60 FPS

# Camera Endpoints
@app.get('/camera/raw')
async def camera_raw():
    """Stream raw camera feed"""
    return StreamingResponse(
        generate_raw_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

@app.get('/camera/processed')
async def camera_processed():
    """Stream processed camera feed with detections"""
    return StreamingResponse(
        generate_processed_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

@app.get('/camera/people_count')
async def get_people_count():
    """Get current people count"""
    with detector.lock:
        return {"count": detector.people_count}

