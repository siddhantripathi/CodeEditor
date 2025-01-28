import os
from dotenv import load_dotenv
from datetime import timedelta

# Load .env file if it exists (local development)
if os.path.exists('.env'):
    load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Optional MongoDB config if needed
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/python_compiler')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False 