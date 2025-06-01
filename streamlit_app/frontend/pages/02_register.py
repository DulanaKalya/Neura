"""
SafeBridge - Registration Page
"""

import streamlit as st
import re
import sys
import os
from streamlit_extras.switch_page_button import switch_page

# Add parent directory to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.auth import init_session_state, register

# Configure the Streamlit page
st.set_page_config(
    page_title="Register - SafeBridge",
    page_icon="🌊",
    layout="wide",
)

# Initialize session state
init_session_state()

# Define CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #1E88E5, #9C27B0);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton button {
        background: linear-gradient(90deg, #1E88E5, #9C27B0);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    /* Step indicator styles */
    .step-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 2rem;
    }
    .step {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #f0f0f0;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 5px;
        font-weight: bold;
    }
    .step-active {
        background: linear-gradient(90deg, #1E88E5, #9C27B0);
        color: white;
    }
    .step-completed {
        background-color: #4CAF50;
        color: white;
    }
    .step-line {
        height: 2px;
        width: 80px;
        background-color: #f0f0f0;
    }
    .step-line-completed {
        background-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Navigation menu for header
def render_header():
    """Display the SafeBridge header."""
    col1, col2, col3 = st.columns([2,3,2])
    with col1:
        st.markdown("# 🌊")
        
    with col2:
        st.markdown('<h1 class="main-title">SafeBridge</h1>', unsafe_allow_html=True)
    
    with col3:
        col3_1, col3_2 = st.columns(2)
        with col3_1:
            if st.button("Home"):
                switch_page("app")
        with col3_2:
            if st.button("Login"):
                switch_page("login")
                
    st.markdown("---")

def render_step_indicator(current_step):
    """Render the step indicator for the registration process."""
    html = """
    <div class="step-container">
        <div class="step {0}">{1}</div>
        <div class="step-line {2}"></div>
        <div class="step {3}">{4}</div>
        <div class="step-line {5}"></div>
        <div class="step {6}">{7}</div>
    </div>
    """
    
    # Define the classes and content for each step
    step1_class = "step-active" if current_step == 1 else "step-completed" if current_step > 1 else ""
    step1_content = "✓" if current_step > 1 else "1"
    
    step2_class = "step-active" if current_step == 2 else "step-completed" if current_step > 2 else ""
    step2_content = "✓" if current_step > 2 else "2"
    
    step3_class = "step-active" if current_step == 3 else ""
    step3_content = "3"
    
    line1_class = "step-line-completed" if current_step > 1 else ""
    line2_class = "step-line-completed" if current_step > 2 else ""
    
    # Format and render the HTML
    html = html.format(step1_class, step1_content, line1_class, step2_class, step2_content, line2_class, step3_class, step3_content)
    st.markdown(html, unsafe_allow_html=True)

def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def validate_password(password, confirm_password):
    """Validate password strength and match"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if password != confirm_password:
        return False, "Passwords do not match"
    return True, ""

def step_one_account_info():
    """Render step one - account information form"""
    st.markdown("### Account Information")
    
    # Get stored form values from session state or initialize empty
    full_name = st.session_state.get('reg_full_name', '')
    email = st.session_state.get('reg_email', '')
    password = st.session_state.get('reg_password', '')
    confirm_password = st.session_state.get('reg_confirm_password', '')
    
    # Form fields
    full_name = st.text_input("Full Name", value=full_name, key="full_name_input")
    email = st.text_input("Email Address", value=email, key="email_input")
    password = st.text_input("Password", value=password, type="password", key="password_input")
    confirm_password = st.text_input("Confirm Password", value=confirm_password, type="password", key="confirm_password_input")
    
    # Store values in session state
    st.session_state['reg_full_name'] = full_name
    st.session_state['reg_email'] = email
    st.session_state['reg_password'] = password
    st.session_state['reg_confirm_password'] = confirm_password
    
    # Validation
    if st.button("Continue"):
        # Validate inputs
        if not full_name:
            st.error("Please enter your full name")
            return False
        
        if not email:
            st.error("Please enter your email address")
            return False
        
        if not validate_email(email):
            st.error("Please enter a valid email address")
            return False
        
        if not password or not confirm_password:
            st.error("Please enter and confirm your password")
            return False
        
        valid_password, error_msg = validate_password(password, confirm_password)
        if not valid_password:
            st.error(error_msg)
            return False
          # All validations passed
        st.session_state['reg_step'] = 2
        st.rerun()
    
    return False

def step_two_role_location():
    """Render step two - role and location form"""
    st.markdown("### Role & Location")
    
    # Get stored form values from session state or initialize with defaults
    role = st.session_state.get('reg_role', 'affected_individual')
    location = st.session_state.get('reg_location', '')
    terms_accepted = st.session_state.get('reg_terms_accepted', False)
    
    # Form fields
    st.markdown("#### I am registering as:")
    role_options = {
        "affected_individual": "Person in Need",
        "volunteer": "Volunteer",
        "first_responder": "First Responder"
    }
    
    role_cols = st.columns(3)
    with role_cols[0]:
        if st.button("Person in Need", type="primary" if role == "affected_individual" else "secondary"):
            role = "affected_individual"
    
    with role_cols[1]:
        if st.button("Volunteer", type="primary" if role == "volunteer" else "secondary"):
            role = "volunteer"
    
    with role_cols[2]:
        if st.button("First Responder", type="primary" if role == "first_responder" else "secondary"):
            role = "first_responder"
    
    # Store selected role
    st.session_state['reg_role'] = role
    st.markdown(f"Selected role: **{role_options[role]}**")
    
    # Location field
    location = st.text_input("Your Location", value=location)
    st.session_state['reg_location'] = location
    
    # Terms and conditions
    terms_accepted = st.checkbox("I agree to the Terms of Service and Privacy Policy", value=terms_accepted)
    st.session_state['reg_terms_accepted'] = terms_accepted
    
    # Navigation buttons
    col1, col2 = st.columns(2)    
    with col1:
        if st.button("Back"):
            st.session_state['reg_step'] = 1
            st.rerun()
    
    with col2:
        if st.button("Continue", key="step2_continue"):
            # Validate inputs
            if not location:
                st.error("Please enter your location")
                return False
            
            if not terms_accepted:
                st.error("You must agree to the Terms of Service and Privacy Policy")
                return False
            
            # If user role is affected_individual, skip step 3
            if role == "affected_individual":
                # Ready to register
                register_user()
            else:                # Go to step 3
                st.session_state['reg_step'] = 3
                st.rerun()
    
    return False

def step_three_experience():
    """Render step three - volunteer/responder experience form"""
    role_display = "Volunteer" if st.session_state.get('reg_role') == "volunteer" else "First Responder"
    st.markdown(f"### {role_display} Information")
    
    # Get stored form values from session state or initialize empty
    specialties = st.session_state.get('reg_specialties', [])
    availability = st.session_state.get('reg_availability', '')
    experience = st.session_state.get('reg_experience', '')
    
    # Specialties
    st.markdown("#### Select your specialties:")
    specialties_options = [
        'Medical', 
        'Search & Rescue', 
        'Firefighting',
        'Communication', 
        'Logistics', 
        'Transportation', 
        'Mental Health', 
        'Childcare', 
        'Elder Care',
        'Technical (Electricity/Water/Gas)', 
        'Foreign Languages', 
        'Food Distribution'
    ]
    
    # Create multi-select for specialties
    specialties = st.multiselect("Specialties", options=specialties_options, default=specialties)
    st.session_state['reg_specialties'] = specialties
    
    # Availability
    st.markdown("#### Availability:")
    availability_options = [
        "Available immediately (24/7)",
        "Available during emergencies only",
        "Available on weekdays",
        "Available on weekends",
        "Limited availability (specify in experience)"
    ]
    availability = st.selectbox("Select your availability", options=availability_options, index=0 if not availability else availability_options.index(availability))
    st.session_state['reg_availability'] = availability
    
    # Experience
    st.markdown("#### Relevant Experience:")
    experience = st.text_area("Please describe your relevant experience and skills", value=experience, height=150)
    st.session_state['reg_experience'] = experience
    
    # Navigation buttons
    col1, col2 = st.columns(2)    
    with col1:
        if st.button("Back"):
            st.session_state['reg_step'] = 2
            st.rerun()
    
    with col2:
        if st.button("Register", type="primary"):
            # Validate inputs
            if not specialties:
                st.error("Please select at least one specialty")
                return False
            
            if not experience or len(experience.strip()) < 10:
                st.error("Please provide a description of your relevant experience (minimum 10 characters)")
                return False
            
            # All validations passed, ready to register
            register_user()
    
    return False

def register_user():
    """Register the user with the collected data"""
    try:
        # Prepare user data for registration
        user_data = {
            "email": st.session_state.get('reg_email'),
            "password": st.session_state.get('reg_password'),
            "fullName": st.session_state.get('reg_full_name'),
            "role": st.session_state.get('reg_role'),
            "location": st.session_state.get('reg_location')
        }
        
        # Register the basic user
        success = register(user_data)
        
        if success:
            # If user is volunteer or first responder, register additional info
            if user_data["role"] in ["volunteer", "first_responder"]:
                from backend.database import register_volunteer
                
                volunteer_data = {
                    "email": user_data["email"],
                    "name": user_data["fullName"],
                    "role": user_data["role"],
                    "location": user_data["location"],
                    "specialties": st.session_state.get('reg_specialties', []),
                    "availability": st.session_state.get('reg_availability', ''),
                    "experience": st.session_state.get('reg_experience', '')
                }
                
                vol_response = register_volunteer(volunteer_data)
                if "error" in vol_response:
                    st.warning(f"Note: Your account was created but volunteer profile had an error: {vol_response['error']}")
            
            # Redirect to dashboard
            switch_page("dashboard")
        else:
            st.error(st.session_state.auth_message)
    except Exception as e:
        st.error(f"Registration failed: {str(e)}")

def main():
    render_header()
    
    # Center the registration form
    _, center_col, _ = st.columns([1, 3, 1])
    
    with center_col:
        st.markdown('<h1 class="main-title">Create Your SafeBridge Account</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Join our community to help connect during emergencies</p>', unsafe_allow_html=True)
        
        # Initialize registration step if not already set
        if 'reg_step' not in st.session_state:
            st.session_state['reg_step'] = 1
            
        # Render step indicator
        render_step_indicator(st.session_state['reg_step'])
        
        # Display error message if any
        if st.session_state.get('auth_message') and st.session_state.get('auth_status') == 'error':
            st.error(st.session_state.auth_message)
        
        # Render appropriate step form
        if st.session_state['reg_step'] == 1:
            step_one_account_info()
        elif st.session_state['reg_step'] == 2:
            step_two_role_location()
        elif st.session_state['reg_step'] == 3:
            step_three_experience()

if __name__ == "__main__":
    main()
