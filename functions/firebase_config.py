import os
from firebase_admin import credentials
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_firebase_credentials():
    # For local development with .env file
    if os.getenv('FB_CLIENT_EMAIL'):
        # Create a credentials dict from environment variables
        cred_dict = {
            "type": "service_account",
            "project_id": os.getenv('FB_PROJECT_ID'),
            "private_key_id": os.getenv('FB_PRIVATE_KEY_ID'),
            "private_key": os.getenv('FB_PRIVATE_KEY'),
            "client_email": os.getenv('FB_CLIENT_EMAIL'),
            "client_id": os.getenv('FB_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FB_CLIENT_EMAIL').replace('@', '%40')}"
        }
        return credentials.Certificate(cred_dict)
    
    # For production deployment, use application default credentials
    return credentials.ApplicationDefault()

def get_firestore_client():
    from firebase_admin import firestore
    return firestore.client()

def get_database_url():
    return os.getenv('FB_DATABASE_URL', 'https://codeeditor-db5bc-default-rtdb.firebaseio.com')