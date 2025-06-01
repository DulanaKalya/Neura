"""
Authentication utilities for SafeBridge Streamlit application.
This module handles session management and authentication.
"""

import streamlit as st
import time
import uuid
from .database import login_user, create_user, update_user_status

def init_session_state():
    """Initialize session state variables for auth."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "auth_message" not in st.session_state:
        st.session_state.auth_message = None
    if "auth_status" not in st.session_state:
        st.session_state.auth_status = None

def login(email, password):
    """
    Authenticate user with email and password
    
    Args:
        email (str): User email
        password (str): User password
    
    Returns:
        bool: True if login successful, False otherwise
    """
    response = login_user(email, password)
    
    if "data" in response:
        # Store user in session
        st.session_state.user = response["data"]
        st.session_state.authenticated = True
        st.session_state.auth_message = "Login successful!"
        st.session_state.auth_status = "success"
        
        # Update user status to active in Firestore
        user_id = response["data"].get("id")
        if user_id:
            update_user_status(user_id, "active")
            
        return True
    else:
        st.session_state.auth_message = response.get("error", "Login failed")
        st.session_state.auth_status = "error"
        return False

def register(user_data):
    """
    Register a new user
    
    Args:
        user_data (dict): User information
    
    Returns:
        bool: True if registration successful, False otherwise
    """
    # Add user_status field to user data
    user_data["user_status"] = "active"
    
    response = create_user(user_data)
    
    if "data" in response:
        # Store user in session
        st.session_state.user = response["data"]
        st.session_state.authenticated = True
        st.session_state.auth_message = "Registration successful!"
        st.session_state.auth_status = "success"
        return True
    else:
        st.session_state.auth_message = response.get("error", "Registration failed")
        st.session_state.auth_status = "error"
        return False

def logout():
    """Log out the current user."""
    # Update user status to offline in Firestore before clearing session
    if st.session_state.user and st.session_state.authenticated:
        user_id = st.session_state.user.get("id")
        if user_id:
            update_user_status(user_id, "offline")
    
    # Clear session state
    st.session_state.user = None
    st.session_state.authenticated = False
    st.session_state.auth_message = "You have been logged out."
    st.session_state.auth_status = "info"
    
def check_authentication():
    """Check if user is authenticated, redirect if not."""
    init_session_state()
    if not st.session_state.authenticated:
        st.warning("Please log in to access this page.")
        st.stop()
    return st.session_state.user
    
def get_current_user():
    """Get the currently logged in user."""
    init_session_state()
    return st.session_state.user