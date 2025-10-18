# Database Setup for Places API

This document explains how to set up and use the database for the Places API backend.

## Overview

The application now uses SQLAlchemy with SQLite for data persistence. The database stores information about places, rooms, and events.

## Database Schema

### Tables

1. **places** - Main table for places/locations
2. **rooms** - Rooms belonging to places
3. **events** - Events hosted at places

### Relationships

- One place can have many rooms (one-to-many)
- One place can have many events (one-to-many)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

Run the initialization script:

```bash
python init_database.py
```

This will:
- Create the database file (`places.db`)
- Create all necessary tables
- Optionally add sample data

### 3. Start the Server

```bash
python backend_admin.py
```

Or using uvicorn directly:

```bash
uvicorn backend_admin:app --reload
```

## API Endpoints

### Places Management

- `POST /new_place` - Create a new place
- `GET /places` - Get all places
- `GET /places/{place_id}` - Get a specific place
- `PUT /edit_place/{place_id}` - Update a place
- `DELETE /delete_place/{place_id}` - Delete a place

### Statistics

- `GET /stats` - Get database statistics

## Database File

The database is stored as `places.db` in the project root directory. This is a SQLite file that can be:

- Backed up by copying the file
- Inspected using SQLite tools
- Migrated to other database systems if needed

## Data Models

### Place
- Basic information (name, bio, contact details)
- Schedule information (Monday-Friday, Saturday, Sunday)
- Associated rooms and events

### Room
- Name, dimensions (length, width)
- Belongs to a place

### Event
- Event details (name, bio, max participants)
- Contact information
- Program schedule (JSON array)
- Image paths (JSON array)
- Belongs to a place

## Migration from In-Memory Storage

The application has been migrated from using an in-memory list (`list_places`) to a persistent SQLite database. All existing API endpoints maintain the same interface, so no changes are needed in client applications.

## Troubleshooting

### Database Locked Error
If you encounter database locked errors, make sure:
- No other processes are using the database
- The database file has proper write permissions

### Missing Dependencies
If you get import errors, ensure all dependencies are installed:
```bash
pip install sqlalchemy alembic
```

### Reset Database
To start fresh, simply delete the `places.db` file and run the initialization script again.

## Development Notes

- The database is automatically initialized when the FastAPI app starts
- All database operations use SQLAlchemy ORM
- JSON fields (program, images_paths) are stored as text and parsed when needed
- Foreign key relationships ensure data integrity
