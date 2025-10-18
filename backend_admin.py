from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path

app = FastAPI()

# IMAGE_DIR = "/uploads/images/"
# Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)

class Room(BaseModel):
    name: str = Field(description="Name of the room")
    length: float = Field(description="Length of the room in meters")
    width: float = Field(description="Width of the room in meters")
    
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
    number_of_rooms: int = Field(description="Number of rooms in the place")
    rooms: List[Room] = Field(description="List of rooms in the place")
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
    number_of_rooms: Optional[int] = Field(description="Number of rooms in the place")
    rooms: Optional[List[Room]] = Field(description="List of rooms in the place")
    password: Optional[str] = Field(description="Password for authentication")
    monday_friday: Optional[str] = Field(description="Schedule from Monday to Friday")
    saturday: Optional[str] = Field(description="Schedule for Saturday")
    sunday: Optional[str] = Field(description="Schedule for Sunday")
    events: Optional[List[Event]] = Field(description="List of events at the place")
    image_path: Optional[str] = Field(description="Path to the image file for the place")
    

list_places = []

# @app.get("/")
# def read_root():
#     return {"Hello": "World"}

@app.post("/new_palce")
def create_place(place: Place):
    new_id = len(list_places) + 1
    place_dict = place.model_dump()
    place_dict["id"] = new_id
    list_places.append(place_dict)
    return {"id": new_id, "place": place_dict}

# Endpoint pentru obținerea listei de locuri
@app.get("/places")
def get_list_of_places():
    return {"places": list_places}

# Endpoint pentru ștergerea unui loc după ID
@app.delete("/delete_place/{place_id}")
def delete_place(place_id: int):
    for idx, p in enumerate(list_places):
        if p["id"] == place_id:
            copy_p = p
            list_places.remove(p)
            return {"status": "success", "deleted_place": copy_p}

# Endpoint pentru actualizarea unui loc după ID
@app.put("/edit_place/{place_id}")
def update_place(place_id: int, updated_place: UpdatePlace):
    for idx, p in enumerate(list_places):
        if p["id"] == place_id:
            updated_data = updated_place.dict(exclude_unset=True)  # utilizăm dict() în loc de model_dump()
            list_places[idx].update(updated_data)
            return {"status": "success", "updated_place": list_places[idx]}
        

