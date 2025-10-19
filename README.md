# SSA Backend

A comprehensive backend system for the Smart Space Assistant (SSA) that provides multiple services including place management, AI-powered reservation agents, event ticket booking, camera detection, and database management. Built with FastAPI, Prisma ORM, and integrated AI services.

## 🚀 Tech Stack

### Core Framework
- **FastAPI 0.118.3** - Modern, fast web framework for building APIs
- **Uvicorn** - ASGI server for running FastAPI applications
- **Pydantic 2.11.10** - Data validation and settings management
- **Python 3.11+** - Core programming language

### Database & ORM
- **Prisma ORM 0.13.0** - Type-safe database toolkit
- **SQLite** - Development database (file-based)
- **PostgreSQL** - Production database support
- **AsyncPG 0.29.0** - PostgreSQL async driver

### AI & Automation Services
- **Browser-use 0.8.0** - AI-powered browser automation
- **Anthropic Claude Sonnet 4.0** - Large Language Model for AI agents
- **OpenCV 4.8.0+** - Computer vision for camera detection
- **Ultralytics YOLO 8.0+** - Object detection and segmentation

### Additional Dependencies
- **NumPy 1.24.0+** - Numerical computing
- **Pillow 9.0+** - Image processing
- **Python-dotenv 1.1.1** - Environment variable management
- **Requests 2.32.5+** - HTTP client library
- **HTTPx 0.28.1+** - Async HTTP client

## 🏗️ Architecture Overview

The SSA Backend consists of multiple interconnected services:

```
SSA-Backend/
├── Main Admin API (backend_admin.py)     # Port 8000
├── Reservation Agent API (backend/app.py) # Port 8001
├── Database Service (Prisma ORM)
├── AI Reservation Agent
├── AI Event Ticket Agent
├── Camera Detection System
└── File Upload System
```

## 📁 Project Structure

```
SSA-Backend/
├── backend/                    # Reservation Agent API
│   ├── app.py                 # Main FastAPI app for reservations
│   ├── middleware/
│   │   └── cors.py           # CORS configuration
│   └── routes/
│       ├── reservations.py   # Reservation endpoints
│       └── event_ticket.py   # Event ticket endpoints
├── prisma/                    # Database schema and migrations
│   ├── schema.prisma         # Database schema definition
│   ├── dev.db               # SQLite development database
│   └── migrations/          # Database migration files
├── uploads/                   # File upload storage
├── backend_admin.py          # Main admin API server
├── database_service.py       # Prisma database service
├── reservation_service.py    # AI reservation agent
├── event_ticket_service.py   # AI event ticket agent
├── models.py                 # Pydantic data models
├── requirements.txt          # Python dependencies
├── yolov8m-seg.pt           # YOLO model for camera detection
└── *.md                     # Documentation files
```

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.11 or higher
- Node.js (for Prisma CLI)
- Google Chrome (for AI agents)
- Git

### 2. Clone and Install Dependencies
```bash
git clone <repository-url>
cd SSA-Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Prisma CLI
npm install -g prisma@5.17.0

# Generate Prisma client
npx prisma generate
```

### 3. Environment Configuration
Create a `.env` file in the project root:
```bash
# Anthropic API Key for AI agents
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database URL (for production)
DATABASE_URL="postgresql://username:password@localhost:5432/ssa_backend"

# Optional: Custom Chrome path
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

### 4. Database Setup
```bash
# Initialize database (SQLite for development)
npx prisma db push

# Or run migrations
npx prisma migrate dev --name init

# View database in Prisma Studio
npx prisma studio
```

## 🚀 Running the Services

### Main Admin API (Port 8000)
```bash
# Start the main admin API
python backend_admin.py

# Or using uvicorn directly
uvicorn backend_admin:app --host 0.0.0.0 --port 8000 --reload
```

### Reservation Agent API (Port 8001)
```bash
# Start the reservation agent API
python backend/app.py

# Or using uvicorn directly
uvicorn backend.app:app --host 0.0.0.0 --port 8001 --reload
```

### Both Services Simultaneously
```bash
# Terminal 1 - Admin API
python backend_admin.py

# Terminal 2 - Reservation Agent API
python backend/app.py
```

## 🔧 Backend Services

### 1. Main Admin API (Port 8000)
**Purpose**: Manages places, events, and provides camera detection

**Key Features**:
- Place CRUD operations
- Event management
- Image upload handling
- Camera detection with YOLO
- Real-time people counting
- Static file serving

**Main Endpoints**:
- `POST /new_place` - Create new place
- `GET /places` - Get all places
- `GET /places/{id}` - Get specific place
- `PUT /edit_place/{id}` - Update place
- `DELETE /delete_place/{id}` - Delete place
- `POST /upload-image` - Upload images
- `GET /camera/{camera_id}/stream` - Camera stream
- `GET /camera/{camera_id}/people-count` - People count

### 2. Reservation Agent API (Port 8001)
**Purpose**: AI-powered reservation and ticket booking system

**Key Features**:
- AI reservation agent using Claude Sonnet 4.0
- Browser automation for booking
- Session management
- Real-time status updates

**Main Endpoints**:
- `POST /reservations/start` - Start reservation
- `GET /reservations/{session_id}/status` - Check status
- `POST /reservations/{session_id}/personal-info` - Submit personal info
- `DELETE /reservations/{session_id}` - Cancel reservation
- `POST /event/start` - Start event ticket booking
- `GET /event/{session_id}/status` - Check booking status

### 3. Database Service (Prisma ORM)
**Purpose**: Type-safe database operations

**Features**:
- SQLite for development
- PostgreSQL for production
- Automatic migrations
- Type-safe queries
- Relationship management

**Models**:
- **Place**: Cultural venues (museums, theaters, etc.)
- **Room**: Rooms within places
- **Event**: Events hosted at places

### 4. AI Reservation Agent
**Purpose**: Automated reservation booking using AI

**Technology Stack**:
- **Claude Sonnet 4.0** - Language model
- **Browser-use** - Browser automation
- **Chrome/Chromium** - Web browser

**Capabilities**:
- Natural language processing
- Website navigation
- Form filling
- Payment processing
- Error handling and retry logic

### 5. AI Event Ticket Agent
**Purpose**: Automated event ticket purchasing

**Features**:
- Event URL processing
- Ticket quantity selection
- Payment handling
- Order confirmation
- Session management

### 6. Camera Detection System
**Purpose**: Real-time people detection and counting

**Technology Stack**:
- **OpenCV** - Computer vision
- **YOLO v8** - Object detection
- **NumPy** - Numerical processing
- **Pillow** - Image processing

**Features**:
- Real-time video streaming
- People detection and counting
- Overlay visualization
- Multiple camera support
- Cross-platform compatibility

## 📊 API Documentation

### Interactive Documentation
- **Admin API**: `http://localhost:8000/docs` (Swagger UI)
- **Reservation API**: `http://localhost:8001/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc` and `http://localhost:8001/redoc`

### Example API Usage
```python
import requests

# Create a new place
place_data = {
    "name": "National Museum of Art",
    "bio": "A prestigious museum showcasing Romanian art",
    "website": "https://nationalmuseum.ro",
    "email": "info@nationalmuseum.ro",
    "phone_number": "+40123456789",
    "address": "Calea Victoriei 49-53, București",
    "password": "secure_password",
    "monday_friday": "10:00-18:00",
    "saturday": "10:00-16:00",
    "sunday": "Closed",
    "image_path": "/images/museum.jpg"
}

response = requests.post("http://localhost:8000/new_place", json=place_data)
print(response.json())

# Start a reservation
reservation_data = {
    "user_prompt": "I want to book 2 tickets for the opera tomorrow evening"
}

response = requests.post("http://localhost:8001/reservations/start", json=reservation_data)
session_id = response.json()["session_id"]
```

## 🧪 Testing

### Run Example API Tests
```bash
python example_api_usage.py
```

### Test Prisma Connection
```bash
python -c "from prisma import Prisma; print('Prisma client imported successfully!')"
```

### Manual Testing
1. Start both API servers
2. Visit `http://localhost:8000/docs` for admin API
3. Visit `http://localhost:8001/docs` for reservation API
4. Use the interactive documentation to test endpoints

## 🗄️ Database Management

### Prisma Commands
```bash
# View database in Prisma Studio
npx prisma studio

# Generate Prisma client after schema changes
npx prisma generate

# Push schema changes (development)
npx prisma db push

# Create and apply migrations
npx prisma migrate dev --name add_new_field

# Reset database (development only)
npx prisma migrate reset
```

### Database Schema
The database uses three main models with relationships:
- **Place** → **Room** (one-to-many)
- **Place** → **Event** (one-to-many)

## 🔒 Security & Environment

### Environment Variables
- `ANTHROPIC_API_KEY` - Required for AI agents
- `DATABASE_URL` - Database connection string
- `CHROME_PATH` - Custom Chrome executable path

### CORS Configuration
Both APIs include CORS middleware for cross-origin requests from frontend applications.

## 📱 Mobile & Production Deployment

### Docker Support
The backend can be containerized for production deployment:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN npx prisma generate

EXPOSE 8000 8001
CMD ["python", "backend_admin.py"]
```

### Production Database
For production, update `prisma/schema.prisma`:
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Chrome not found**: Install Google Chrome or set `CHROME_PATH`
2. **Prisma client not generated**: Run `npx prisma generate`
3. **Database locked**: Ensure no other processes are using the database
4. **AI agent errors**: Check `ANTHROPIC_API_KEY` is set correctly

### Logs and Debugging
- Check console output for detailed error messages
- Use FastAPI's built-in logging
- Monitor browser automation in headless mode

## 📄 Documentation Files

- `DATABASE_README.md` - Database setup and usage
- `PRISMA_GUIDE.md` - Comprehensive Prisma ORM guide
- `example_api_usage.py` - API usage examples

## 📄 License

This project is part of the SSA (Smart Space Assistant) system developed for the Craiova Hackathon.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For support and questions, please contact the development team or create an issue in the repository.
