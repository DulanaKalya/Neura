"""
Firebase Admin SDK setup for SafeBridge application.
This module initializes the connection to Firebase services.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_firebase():
    """Initialize Firebase Admin SDK with credentials from environment variables."""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Use service account credentials from environment or file
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                # For development, you can use a JSON string from .env
                firebase_config = os.environ.get('FIREBASE_CONFIG')
                if firebase_config:
                    import json
                    cred = credentials.Certificate(json.loads(firebase_config))
                else:
                    raise ValueError("Firebase credentials not found")
            
            # Initialize the app
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return False

# Get Firestore database instance
def get_firestore_client():
    """Get a Firestore client instance."""
    if initialize_firebase():
        return firestore.client()
    return None

# Initialize Firebase when module is imported
db = get_firestore_client()
