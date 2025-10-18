from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from pathlib import Path
import json
import uuid
import os
from database_service import db_service

app = FastAPI(title="SSA Backend Admin API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Mount static files to serve uploaded images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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
    
    @validator('categories')
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
    
    @validator('categories')
    def validate_categories(cls, v):
        if v is not None:
            if not v:
                raise ValueError('Categories list cannot be empty')
            for category in v:
                if category not in VALID_CATEGORIES:
                    raise ValueError(f'Invalid category: {category}. Valid categories are: {VALID_CATEGORIES}')
        return v
    

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await db_service.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await db_service.disconnect()

@app.get("/")
def read_root():
    return {"message": "SSA Backend Admin API", "docs": "/docs"}

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
        return {"places": places}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching places: {str(e)}")

@app.get("/places/{place_id}")
async def get_place_by_id(place_id: int):
    """Get a specific place by ID"""
    try:
        place = await db_service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        return {"place": place}
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
        
        # Add the new event to the place's events list
        event_dict = event.model_dump()
        event_dict["id"] = str(uuid.uuid4())  # Generate unique ID
        
        # Convert field names to match database schema (camelCase)
        converted_event = {}
        for key, value in event_dict.items():
            if key == 'max_participants':
                converted_event['maxParticipants'] = value
            elif key == 'phone_number':
                converted_event['phoneNumber'] = value
            elif key == 'images_paths':
                converted_event['imagesPaths'] = value
            else:
                converted_event[key] = value
        
        if not hasattr(place, 'events') or place.events is None:
            place.events = []
        
        place.events.append(converted_event)
        
        # Update the place with the new event
        updated_place = await db_service.update_place(place_id, {"events": place.events})
        
        return {"status": "success", "event": converted_event, "place": updated_place}
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
        
        events = getattr(place, 'events', []) or []
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
        
        events = getattr(place, 'events', []) or []
        event = next((e for e in events if e.get('id') == event_id), None)
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return {"event": event}
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
        
        events = getattr(place, 'events', []) or []
        event_index = next((i for i, e in enumerate(events) if e.get('id') == event_id), None)
        
        if event_index is None:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Update the event - convert snake_case to camelCase for database consistency
        updated_data = updated_event.model_dump(exclude_unset=True)
        
        # Convert field names to match database schema
        converted_data = {}
        for key, value in updated_data.items():
            if key == 'max_participants':
                converted_data['maxParticipants'] = value
            elif key == 'phone_number':
                converted_data['phoneNumber'] = value
            elif key == 'images_paths':
                converted_data['imagesPaths'] = value
            else:
                converted_data[key] = value
        
        events[event_index].update(converted_data)
        
        # Update the place with the modified events
        updated_place = await db_service.update_place(place_id, {"events": events})
        
        return {"status": "success", "event": events[event_index], "place": updated_place}
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
        
        events = getattr(place, 'events', []) or []
        event_index = next((i for i, e in enumerate(events) if e.get('id') == event_id), None)
        
        if event_index is None:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Remove the event
        deleted_event = events.pop(event_index)
        
        # Update the place with the modified events
        updated_place = await db_service.update_place(place_id, {"events": events})
        
        return {"status": "success", "deleted_event": deleted_event, "place": updated_place}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")
        

