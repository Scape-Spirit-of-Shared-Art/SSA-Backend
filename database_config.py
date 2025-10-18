"""
Database configuration for the SSA Backend
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL - you can set this as an environment variable or modify directly
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://username:password@localhost:5432/ssa_backend?schema=public"
)

# For development with SQLite (easier setup):
# DATABASE_URL = "file:./dev.db"

print(f"Using database URL: {DATABASE_URL}")
