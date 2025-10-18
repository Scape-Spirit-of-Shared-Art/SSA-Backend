"""
Example script showing how to use the SSA Backend API with Prisma
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8001"

def test_api_endpoints():
    """Test all API endpoints"""
    
    print("🚀 Testing SSA Backend API with Prisma...")
    
    # Sample place data
    place_data = {
        "name": "National Museum of Art",
        "bio": "A prestigious museum showcasing Romanian and international art",
        "website": "https://nationalmuseum.ro",
        "email": "info@nationalmuseum.ro",
        "phone_number": "+40123456789",
        "address": "Calea Victoriei 49-53, București",
        "number_of_rooms": 3,
        "password": "secure_admin_password",
        "monday_friday": "10:00-18:00",
        "saturday": "10:00-16:00",
        "sunday": "Closed",
        "image_path": "/images/national_museum.jpg",
        "rooms": [
            {
                "name": "Main Exhibition Hall",
                "length": 25.0,
                "width": 18.0
            },
            {
                "name": "Contemporary Art Gallery",
                "length": 15.0,
                "width": 12.0
            },
            {
                "name": "Sculpture Garden",
                "length": 30.0,
                "width": 20.0
            }
        ],
        "events": [
            {
                "name": "Romanian Art Through the Ages",
                "bio": "A comprehensive exhibition of Romanian art from medieval times to present",
                "max_participants": 100,
                "website": "https://nationalmuseum.ro/romanian-art",
                "email": "events@nationalmuseum.ro",
                "phone_number": "+40123456789",
                "address": "Calea Victoriei 49-53, București",
                "program": [
                    "Welcome and introduction",
                    "Guided tour of medieval art",
                    "Modern art presentation",
                    "Q&A session with curators"
                ],
                "images_paths": [
                    "/images/romanian_art_1.jpg",
                    "/images/romanian_art_2.jpg",
                    "/images/romanian_art_3.jpg"
                ]
            },
            {
                "name": "International Contemporary Art",
                "bio": "Showcasing contemporary artists from around the world",
                "max_participants": 75,
                "website": "https://nationalmuseum.ro/contemporary",
                "email": "events@nationalmuseum.ro",
                "phone_number": "+40123456789",
                "address": "Calea Victoriei 49-53, București",
                "program": [
                    "Artist meet and greet",
                    "Interactive art workshop",
                    "Panel discussion",
                    "Networking reception"
                ],
                "images_paths": [
                    "/images/contemporary_1.jpg",
                    "/images/contemporary_2.jpg"
                ]
            }
        ]
    }
    
    try:
        # 1. Create a new place
        print("\n📝 Creating a new place...")
        response = requests.post(f"{BASE_URL}/new_place", json=place_data)
        if response.status_code == 200:
            result = response.json()
            place_id = result["id"]
            print(f"✅ Created place with ID: {place_id}")
            print(f"   Name: {result['place']['name']}")
        else:
            print(f"❌ Error creating place: {response.status_code} - {response.text}")
            return
        
        # 2. Get all places
        print("\n📋 Getting all places...")
        response = requests.get(f"{BASE_URL}/places")
        if response.status_code == 200:
            result = response.json()
            places = result["places"]
            print(f"✅ Found {len(places)} places")
            for place in places:
                print(f"   - {place['name']} (ID: {place['id']})")
        else:
            print(f"❌ Error getting places: {response.status_code} - {response.text}")
        
        # 3. Get specific place
        print(f"\n🔍 Getting place with ID {place_id}...")
        response = requests.get(f"{BASE_URL}/places/{place_id}")
        if response.status_code == 200:
            result = response.json()
            place = result["place"]
            print(f"✅ Found place: {place['name']}")
            print(f"   - Rooms: {len(place['rooms'])}")
            print(f"   - Events: {len(place['events'])}")
            print(f"   - Address: {place['address']}")
        else:
            print(f"❌ Error getting place: {response.status_code} - {response.text}")
        
        # 4. Update place
        print(f"\n✏️ Updating place {place_id}...")
        update_data = {
            "name": "National Museum of Art - Updated",
            "bio": "An updated description of this prestigious museum"
        }
        response = requests.put(f"{BASE_URL}/edit_place/{place_id}", json=update_data)
        if response.status_code == 200:
            result = response.json()
            updated_place = result["updated_place"]
            print(f"✅ Updated place: {updated_place['name']}")
        else:
            print(f"❌ Error updating place: {response.status_code} - {response.text}")
        
        # 5. Delete place
        print(f"\n🗑️ Deleting place {place_id}...")
        response = requests.delete(f"{BASE_URL}/delete_place/{place_id}")
        if response.status_code == 200:
            result = response.json()
            deleted_place = result["deleted_place"]
            print(f"✅ Deleted place: {deleted_place['name']}")
        else:
            print(f"❌ Error deleting place: {response.status_code} - {response.text}")
        
        print("\n🎉 All API tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server.")
        print("   Make sure the server is running on http://localhost:8001")
        print("   Start it with: python -m uvicorn backend_admin:app --reload --port 8001")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_api_endpoints()
