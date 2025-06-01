"""
Database operations for SafeBridge application.
This module handles all Firestore database interactions.
"""

from datetime import datetime
import uuid
from firebase_admin import firestore
from .firebase_init import db

# User Management
def create_user(user_data):
    """
    Create a new user in Firestore
    
    Args:
        user_data (dict): User information containing email, password, fullName, role, location
    
    Returns:
        dict: Created user data with ID
    """
    try:
        # Check if user already exists
        existing_users = db.collection('users').where('email', '==', user_data['email']).get()
        if len(existing_users) > 0:
            return {"error": "User already exists", "status": 409}
        
        # Create timestamp
        now = datetime.now().timestamp() * 1000
        
        # Prepare user data (adding unique ID and timestamp)
        new_user = {
            "id": str(uuid.uuid4()),
            "email": user_data.get("email"),
            "password": user_data.get("password"),  # In production, use Firebase Auth instead
            "fullName": user_data.get("fullName", ""),
            "role": user_data.get("role", "affected_individual"),
            "location": user_data.get("location", ""),
            "created_at": now,
            "user_status":user_data.get("user_status", "active"),
        }
        
        # Add to Firestore
        db.collection('users').document(new_user["id"]).set(new_user)
        
        # Return user data without password
        user_response = {k: v for k, v in new_user.items() if k != 'password'}
        user_response["token"] = "mock-jwt-token-" + str(uuid.uuid4())
        
        return {"data": user_response, "status": 201}
    except Exception as e:
        print(f"Error creating user: {e}")
        return {"error": str(e), "status": 500}
        
def login_user(email, password):
    """
    Authenticate user with email and password
    
    Args:
        email (str): User email
        password (str): User password
        
    Returns:
        dict: User data if authenticated
    """
    try:
        # Get user by email
        users = db.collection('users').where('email', '==', email).where('password', '==', password).get()
        
        if len(users) == 0:
            return {"error": "Invalid email or password", "status": 401}
            
        user = users[0].to_dict()
        
        # Return user data with token
        return {
            "data": {
                "token": "mock-jwt-token-" + str(uuid.uuid4()),
                "role": user.get("role", ""),
                "fullName": user.get("fullName", ""),
                "location": user.get("location", ""),
                "email": user.get("email", ""),
            }, 
            "status": 200
        }
    except Exception as e:
        print(f"Error logging in: {e}")
        return {"error": str(e), "status": 500}
        
# Volunteer Management
def register_volunteer(volunteer_data):
    """
    Register a volunteer profile
    
    Args:
        volunteer_data (dict): Volunteer information
        
    Returns:
        dict: Created volunteer data
    """
    try:
        # Create timestamp
        now = datetime.now().timestamp() * 1000
        
        # Prepare volunteer data
        new_volunteer = {
            "id": str(uuid.uuid4()),
            "email": volunteer_data.get("email"),
            "name": volunteer_data.get("name"),
            "role": volunteer_data.get("role", "volunteer"),
            "location": volunteer_data.get("location", ""),
            "specialties": volunteer_data.get("specialties", []),
            "availability": volunteer_data.get("availability", ""),
            "experience": volunteer_data.get("experience", ""),
            "user_status":volunteer_data.get("user_status", "active"),
            "created_at": now,
        }
        
        # Add to Firestore
        db.collection('volunteers').document(new_volunteer["id"]).set(new_volunteer)
        
        return {"data": new_volunteer, "status": 201}
    except Exception as e:
        print(f"Error registering volunteer: {e}")
        return {"error": str(e), "status": 500}
        
# Request Management
def submit_request(request_data):
    """
    Submit a new emergency request
    
    Args:
        request_data (dict): Request information
        
    Returns:
        dict: Created request data
    """
    try:
        # Create timestamp
        now = datetime.now().timestamp() * 1000
        
        # Prepare request data
        new_request = {
            "id": str(uuid.uuid4()),
            "text": request_data.get("text"),
            "urgency": request_data.get("urgency", "Unknown"),
            "type": request_data.get("type", "Unknown"),
            "location": request_data.get("location", "User reported location"),
            "timestamp": now,
            "status": "pending",
            "lastUpdated": None,
        }
        
        # Add to Firestore
        db.collection('requests').document(new_request["id"]).set(new_request)
        
        return {"data": new_request, "status": 201}
    except Exception as e:
        print(f"Error submitting request: {e}")
        return {"error": str(e), "status": 500}
        
def get_all_requests():
    """
    Get all emergency requests
    
    Returns:
        list: List of all requests
    """
    try:
        # Get all requests
        requests = db.collection('requests').get()
        
        # Convert to list of dictionaries
        request_list = [doc.to_dict() for doc in requests]
        
        return {"data": request_list, "status": 200}
    except Exception as e:
        print(f"Error getting requests: {e}")
        return {"error": str(e), "status": 500}
        
def get_request_by_id(request_id):
    """
    Get a specific request by ID
    
    Args:
        request_id (str): Request ID
        
    Returns:
        dict: Request data
    """
    try:
        # Get request by ID
        request = db.collection('requests').document(request_id).get()
        
        if not request.exists:
            return {"error": "Request not found", "status": 404}
            
        return {"data": request.to_dict(), "status": 200}
    except Exception as e:
        print(f"Error getting request: {e}")
        return {"error": str(e), "status": 500}
        
def update_request_status(request_id, status):
    """
    Update a request status
    
    Args:
        request_id (str): Request ID
        status (str): New status
        
    Returns:
        dict: Updated request data
    """
    try:
        # Update request status
        now = datetime.now().timestamp() * 1000
        db.collection('requests').document(request_id).update({
            "status": status,
            "lastUpdated": now
        })
        
        # Get updated request
        updated_request = db.collection('requests').document(request_id).get()
        
        if not updated_request.exists:
            return {"error": "Request not found", "status": 404}
            
        return {"data": updated_request.to_dict(), "status": 200}
    except Exception as e:
        print(f"Error updating request: {e}")
        return {"error": str(e), "status": 500}

def update_user_status(user_id, status):
    """
    Update user's online status in Firestore
    
    Args:
        user_id (str): User ID
        status (str): User status ('active' or 'offline')
        
    Returns:
        dict: Response with success/error message
    """
    try:
        # Update the user document with the new status
        users_ref = db.collection('users').document(user_id)
        
        # Also update the last_active timestamp
        users_ref.update({
            'user_status': status,
            'last_active': firestore.SERVER_TIMESTAMP
        })
        
        return {"success": f"User status updated to {status}"}
    except Exception as e:
        print(f"Error updating user status: {e}")
        return {"error": str(e)}
    
def get_all_responders():
    """
    Get all volunteers and first responders
    
    Returns:
        dict: List of all responders (volunteers and first responders)
    """
    try:
        # Get volunteers and first responders
        volunteers = db.collection('users').where('role', '==', 'volunteer').get()
        first_responders = db.collection('users').where('role', '==', 'first_responder').get()
        
        # Convert to list of dictionaries
        volunteer_list = [doc.to_dict() for doc in volunteers]
        first_responder_list = [doc.to_dict() for doc in first_responders]
        
        # Combine lists
        all_responders = volunteer_list + first_responder_list
        
        return {"data": all_responders, "status": 200}
    except Exception as e:
        print(f"Error getting responders: {e}")
        return {"error": str(e), "status": 500}