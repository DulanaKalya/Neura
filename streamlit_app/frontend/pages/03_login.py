"""
SafeBridge - Login Page
"""

import streamlit as st
import sys
import os
from streamlit_extras.switch_page_button import switch_page

# Add parent directory to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.auth import init_session_state, login

# Configure the Streamlit page
st.set_page_config(
    page_title="Login - SafeBridge",
    page_icon="🌊",
    layout="wide",
)

# Initialize session state
init_session_state()

# Define CSS
st.markdown("""
<style>
            
    /* Hide the default Streamlit page navigation */
    .css-1d391kg {display: none;}
    .css-1rs6os {display: none;}
    .css-17eq0hr {display: none;}
    div[data-testid="stSidebarNav"] {display: none;}
    .css-k1vhr4 {display: none;}
    .css-1cypcdb {display: none;}
    section[data-testid="stSidebarNav"] {display: none;}
    
    /* Keep the sidebar itself visible but hide the navigation */
    section[data-testid="stSidebar"] {
        display: block !important;
    }
    
    /* Hide specific navigation elements */
    .css-1544g2n {display: none;}
    .css-163ttbj {display: none;}
    
    /* Additional selectors to ensure page navigation is hidden */
    ul[data-testid="stSidebarNav"] {display: none;}
    nav[data-testid="stSidebarNav"] {display: none;}

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
    .login-card {
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        padding: 2rem;
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
            if st.button("Register"):
                switch_page("register")
                
    st.markdown("---")

def main():
    render_header()
    
    # Check if user is already logged in
    if st.session_state.get('authenticated'):
        st.success("You are already logged in!")
        if st.button("Go to Dashboard"):
            switch_page("dashboard")
        
    
    # Center the login form
    _, center_col, _ = st.columns([2, 3, 2])
    
    with center_col:
        st.markdown('<h1 class="main-title">Sign in to SafeBridge</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Access the emergency response platform</p>', unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Sign in", use_container_width=True)
            
            if submit_button:
                if not email or not password:
                    st.error("Please enter your email and password")
                else:
                    success = login(email, password)
                    if success:
                        st.success("Login successful! Redirecting to dashboard...")
                        st.rerun()
                    else:
                        st.error(st.session_state.auth_message or "Invalid email or password")
        
        # Forgot password link and register link
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<a href="#" style="color: #1E88E5; text-decoration: none;">Forgot password?</a>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="text-align: right;"><a href="/streamlit_app/frontend/pages/02_register.py" style="color: #1E88E5; text-decoration: none;">Don\'t have an account? Register here</a></div>', unsafe_allow_html=True)
            if st.button("Register here"):
                switch_page("register")

if __name__ == "__main__":
    main()
