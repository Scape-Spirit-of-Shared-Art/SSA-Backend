# Prisma ORM Setup Guide for SSA Backend

## Overview

This guide explains how to use Prisma ORM with your SSA Backend project. Prisma is a modern database toolkit that provides type-safe database access, automatic migrations, and a powerful query API.

## What We've Set Up

### 1. Database Schema (`prisma/schema.prisma`)

We've created a Prisma schema with three main models:

- **Place**: Main entity representing cultural venues (museums, theaters, etc.)
- **Room**: Rooms within a place
- **Event**: Events hosted at a place

### 2. Database Service (`database_service.py`)

A service class that wraps Prisma operations with proper error handling and field mapping.

### 3. Updated API (`backend_admin.py`)

Your FastAPI endpoints now use Prisma instead of in-memory lists.

## Key Features

### Type Safety
- All database operations are type-safe
- Automatic validation of data types
- IDE autocompletion for database queries

### Relationships
- One-to-many relationships between Place → Rooms and Place → Events
- Cascade deletes (deleting a place removes its rooms and events)

### JSON Support
- Arrays are stored as JSON strings (SQLite compatibility)
- Automatic serialization/deserialization

## How to Use Prisma

### 1. Basic CRUD Operations

```python
from database_service import db_service

# Create a place
place_data = {
    "name": "Museum of Art",
    "bio": "A beautiful art museum",
    "website": "https://museum.com",
    "email": "info@museum.com",
    "phone_number": "+1234567890",
    "address": "123 Art Street",
    "number_of_rooms": 2,
    "password": "secure_password",
    "monday_friday": "9:00-17:00",
    "saturday": "10:00-16:00",
    "sunday": "Closed",
    "image_path": "/images/museum.jpg",
    "rooms": [
        {"name": "Main Hall", "length": 20.0, "width": 15.0}
    ],
    "events": [
        {
            "name": "Art Exhibition",
            "bio": "Modern art showcase",
            "max_participants": 50,
            "website": "https://museum.com/art",
            "email": "events@museum.com",
            "phone_number": "+1234567890",
            "address": "123 Art Street",
            "program": ["Opening", "Tour", "Q&A"],
            "images_paths": ["/images/art1.jpg"]
        }
    ]
}

# Create
place = await db_service.create_place(place_data)

# Read
all_places = await db_service.get_all_places()
specific_place = await db_service.get_place_by_id(place.id)

# Update
update_data = {"name": "Updated Museum Name"}
updated_place = await db_service.update_place(place.id, update_data)

# Delete
deleted_place = await db_service.delete_place(place.id)
```

### 2. Advanced Queries with Prisma

```python
from prisma import Prisma

prisma = Prisma()
await prisma.connect()

# Complex queries
places_with_events = await prisma.place.find_many(
    where={
        "events": {
            "some": {
                "maxParticipants": {
                    "gte": 50
                }
            }
        }
    },
    include={
        "rooms": True,
        "events": True
    }
)

# Filtering and sorting
recent_places = await prisma.place.find_many(
    order_by={"createdAt": "desc"},
    take=10
)

# Search
search_results = await prisma.place.find_many(
    where={
        "OR": [
            {"name": {"contains": "museum"}},
            {"bio": {"contains": "art"}}
        ]
    }
)

await prisma.disconnect()
```

### 3. Database Migrations

When you change the schema, create a migration:

```bash
# Generate migration
prisma migrate dev --name add_new_field

# Apply migrations
prisma migrate deploy

# Reset database (development only)
prisma migrate reset
```

### 4. Database Management

```bash
# View database in Prisma Studio
prisma studio

# Generate Prisma client after schema changes
prisma generate

# Push schema changes without migration (development)
prisma db push
```

## API Endpoints

Your FastAPI server now provides these endpoints:

- `POST /new_place` - Create a new place
- `GET /places` - Get all places
- `GET /places/{place_id}` - Get specific place
- `PUT /edit_place/{place_id}` - Update a place
- `DELETE /delete_place/{place_id}` - Delete a place

## Environment Setup

### For Development (SQLite)
```bash
# Already configured in schema.prisma
datasource db {
  provider = "sqlite"
  url      = "file:./dev.db"
}
```

### For Production (PostgreSQL)
1. Update `prisma/schema.prisma`:
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

2. Set environment variable:
```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/ssa_backend"
```

## Best Practices

### 1. Connection Management
- Always use the database service for connection management
- The FastAPI app handles startup/shutdown automatically

### 2. Error Handling
- All database operations are wrapped in try-catch blocks
- Proper HTTP status codes are returned

### 3. Data Validation
- Pydantic models validate input data
- Prisma validates database constraints

### 4. Performance
- Use `include` to fetch related data in one query
- Use `select` to fetch only needed fields
- Consider pagination for large datasets

## Testing

Run the test script to verify everything works:

```bash
python test_prisma.py
```

## Troubleshooting

### Common Issues

1. **Field mapping errors**: Check that field names match between Pydantic models and Prisma schema
2. **Connection errors**: Ensure database is running and accessible
3. **Migration errors**: Run `prisma generate` after schema changes

### Useful Commands

```bash
# Check Prisma version
prisma --version

# View current schema
cat prisma/schema.prisma

# Check database status
prisma db pull

# Reset everything (development)
prisma migrate reset
```

## Next Steps

1. **Add more models**: Extend the schema with additional entities
2. **Implement authentication**: Add user management
3. **Add validation**: Enhance data validation rules
4. **Performance optimization**: Add indexes and optimize queries
5. **Monitoring**: Add logging and performance monitoring

## Resources

- [Prisma Documentation](https://www.prisma.io/docs/)
- [Prisma Python Client](https://prisma-client-py.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
