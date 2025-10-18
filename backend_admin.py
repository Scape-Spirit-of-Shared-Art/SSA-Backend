from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
import json
from database_service import db_service

app = FastAPI(title="SSA Backend Admin API", version="1.0.0")

# IMAGE_DIR = "/uploads/images/"
# Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)

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
    password: str = Field(description="Password for authentication")
    monday_friday: str = Field(description="Schedule from Monday to Friday")
    saturday: str = Field(description="Schedule for Saturday")
    sunday: str = Field(description="Schedule for Sunday")
    events: List[Event] = Field(description="List of events at the place")
    image_path: str = Field(description="Path to the image file for the place")


class UpdatePlace(BaseModel):
    name: Optional[str] = Field(description="Name of the place")
    bio: Optional[str] = Field(description="Short description of the place")
    website: Optional[str] = Field(description="URL of the website")
    email: Optional[str] = Field(description="Email for contact")
    phone_number: Optional[str] = Field(description="Phone number for contact")
    address: Optional[str] = Field(description="Address of the place")
    floormaps: Optional[dict] = Field(description="JSON object containing floor map data")
    password: Optional[str] = Field(description="Password for authentication")
    monday_friday: Optional[str] = Field(description="Schedule from Monday to Friday")
    saturday: Optional[str] = Field(description="Schedule for Saturday")
    sunday: Optional[str] = Field(description="Schedule for Sunday")
    events: Optional[List[Event]] = Field(description="List of events at the place")
    image_path: Optional[str] = Field(description="Path to the image file for the place")
    

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
        

