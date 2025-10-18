"""
Database service using Prisma ORM
"""
import json
from typing import List, Optional, Dict, Any
from prisma import Prisma
from prisma.models import Place, Event
from pydantic import BaseModel, Field
from typing import Optional, List

# Initialize Prisma client
prisma = Prisma()

class DatabaseService:
    """Service class for database operations using Prisma ORM"""
    
    async def connect(self):
        """Connect to the database"""
        await prisma.connect()
    
    async def disconnect(self):
        """Disconnect from the database"""
        await prisma.disconnect()
    
    # Place operations
    async def create_place(self, place_data: Dict[str, Any]) -> Place:
        """Create a new place with events"""
        # Convert lists to JSON strings for SQLite compatibility
        if 'events' in place_data:
            events_data = place_data.pop('events')
        else:
            events_data = []
        
        # Map field names to match database schema
        mapped_data = {
            'name': place_data.get('name'),
            'bio': place_data.get('bio'),
            'website': place_data.get('website'),
            'email': place_data.get('email'),
            'phoneNumber': place_data.get('phone_number'),
            'address': place_data.get('address'),
            'floormaps': json.dumps(place_data.get('floormaps', {})),
            'categories': json.dumps(place_data.get('categories', [])),
            'password': place_data.get('password'),
            'mondayFriday': place_data.get('monday_friday'),
            'saturday': place_data.get('saturday'),
            'sunday': place_data.get('sunday'),
            'imagePath': place_data.get('image_path'),
        }
        
        # Create the place
        place = await prisma.place.create(
            data={
                **mapped_data,
                'events': {
                    'create': [
                        {
                            'name': event.get('name'),
                            'bio': event.get('bio'),
                            'maxParticipants': event.get('max_participants'),
                            'website': event.get('website'),
                            'email': event.get('email'),
                            'phoneNumber': event.get('phone_number'),
                            'address': event.get('address'),
                            'program': json.dumps(event.get('program', [])),
                            'imagesPaths': json.dumps(event.get('images_paths', []))
                        }
                        for event in events_data
                    ]
                }
            }
        )
        return place
    
    async def get_all_places(self) -> List[Place]:
        """Get all places with their events"""
        places = await prisma.place.find_many(
            include={
                'events': True
            }
        )
        return places
    
    async def get_place_by_id(self, place_id: int) -> Optional[Place]:
        """Get a place by ID with events"""
        place = await prisma.place.find_unique(
            where={'id': place_id},
            include={
                'events': True
            }
        )
        return place
    
    async def update_place(self, place_id: int, update_data: Dict[str, Any]) -> Optional[Place]:
        """Update a place by ID"""
        # Handle events separately if they exist
        events_data = update_data.pop('events', None)
        
        # Map field names to match database schema (same as create_place)
        mapped_data = {}
        for key, value in update_data.items():
            if value is not None:
                # Map field names to database schema
                if key == 'phone_number':
                    mapped_data['phoneNumber'] = value
                elif key == 'monday_friday':
                    mapped_data['mondayFriday'] = value
                elif key == 'image_path':
                    mapped_data['imagePath'] = value
                elif key == 'floormaps' and isinstance(value, dict):
                    mapped_data['floormaps'] = json.dumps(value)
                elif key == 'categories' and isinstance(value, list):
                    mapped_data['categories'] = json.dumps(value)
                else:
                    mapped_data[key] = value
        
        # Update the place
        place = await prisma.place.update(
            where={'id': place_id},
            data=mapped_data,
            include={
                'events': True
            }
        )
        
        # Update events if provided
        if events_data is not None:
            # Delete existing events
            await prisma.event.delete_many(where={'placeId': place_id})
            # Create new events
            if events_data:
                await prisma.event.create_many(
                    data=[
                        {
                            'name': event.get('name'),
                            'bio': event.get('bio'),
                            'maxParticipants': event.get('max_participants'),
                            'website': event.get('website'),
                            'email': event.get('email'),
                            'phoneNumber': event.get('phone_number'),
                            'address': event.get('address'),
                            'program': json.dumps(event.get('program', [])),
                            'imagesPaths': json.dumps(event.get('images_paths', [])),
                            'date': event.get('date'),
                            'placeId': place_id
                        }
                        for event in events_data
                    ]
                )
        
        # Return updated place
        return await self.get_place_by_id(place_id)
    
    async def delete_place(self, place_id: int) -> Optional[Place]:
        """Delete a place by ID (cascade delete will handle events)"""
        place = await self.get_place_by_id(place_id)
        if place:
            await prisma.place.delete(where={'id': place_id})
        return place

# Global database service instance
db_service = DatabaseService()
