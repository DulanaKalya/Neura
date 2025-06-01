"""
SafeBridge - AI-Powered Disaster Response
Main Streamlit application entry point.
"""

import streamlit as st
from PIL import Image
import os
import sys

# Add parent directory to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.auth import init_session_state, login, register, logout, get_current_user

# Configure the Streamlit page
st.set_page_config(
    page_title="SafeBridge - Disaster Response",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_session_state()

# Define CSS
st.markdown("""
<style>
    .main-title {
        font-size: 3rem !important;
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
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    .feature-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def display_header():
    """Display the SafeBridge header."""
    user = get_current_user()
      # Top navigation
    col1, col2, col3 = st.columns([2,3,2])
    with col1:
        st.markdown("# 🌊")
        
    with col2:
        st.markdown('<h1 class="main-title">SafeBridge</h1>', unsafe_allow_html=True)
    
    with col3:
        if user:
            st.markdown(f"Welcome, {user['fullName']}")
            if st.button("Logout"):
                logout()
                st.rerun()
        else:
            col3_1, col3_2 = st.columns(2)
            with col3_1:
                if st.button("Login"):
                    st.switch_page("pages/03_login.py")
            with col3_2:
                if st.button("Register"):
                    st.switch_page("pages/02_register.py")
    
    # Navigation menu
    menu_options = ["Home"]
    
    if user:
        menu_options.extend(["Dashboard", "Submit Request", "Chat"])
    
    st.markdown("---")

def display_home_content():
    """Display the home page content."""
    
    st.markdown('<p class="subtitle">AI-Powered Platform Connecting Communities During Emergencies</p>', unsafe_allow_html=True)
    
    # Hero section with image
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### Connecting People When It Matters Most
        
        SafeBridge is an AI-powered emergency response platform that connects individuals affected by 
        disasters with emergency services, volunteers, and resources in real-time.
        
        Our platform enables:
        - **Rapid Emergency Response** coordination
        - **AI-Powered Resource Allocation**
        - **Community-Driven Support Networks**
        """)
        
        if "authenticated" not in st.session_state or not st.session_state.authenticated:
            if st.button("Get Started", key="home_cta"):
                st.switch_page("pages/02_register.py")
    
    with col2:
        # Use a sample disaster response image
        st.image("D:\\MY_PROJECTS\\Intellihack\\Finals\\streamlit_app\\natural-disaster.jpg", 
                 caption="AI-powered emergency response platform")
    
    # Feature section
    st.markdown("## How SafeBridge Works", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card" style="background-image: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'); background-size: cover; background-position: center; color: #fff; min-height: 250px;">
            <div class="feature-icon">🆘</div>
            <div class="feature-title">Request Help</div>
            <p style="color: #fff; text-shadow: 1px 1px 4px #000;">Submit emergency requests that are prioritized by AI based on urgency and resource availability.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card" style="background-image: url('https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=400&q=80'); background-size: cover; background-position: center; color: #fff; min-height: 250px;">
            <div class="feature-icon">🤝</div>
            <div class="feature-title">Connect Resources</div>
            <p style="color: #fff; text-shadow: 1px 1px 4px #000;">Our platform matches those in need with first responders, volunteers, and nearby services.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card" style="background-image: url('https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=400&q=80'); background-size: cover; background-position: center; color: #fff; min-height: 250px;">
            <div class="feature-icon">📊</div>
            <div class="feature-title">AI Coordination</div>
            <p style="color: #fff; text-shadow: 1px 1px 4px #000;">Advanced AI algorithms optimize resource allocation and provide real-time situational awareness.</p>
        </div>
        """, unsafe_allow_html=True)

    # Testimonials
    st.markdown("## Making a Difference", unsafe_allow_html=True)
    
    testimonials = [
        {
            "quote": "SafeBridge helped us coordinate rescue efforts during the recent floods, saving countless lives.",
            "author": "Sarah J., First Responder"
        },
        {
            "quote": "When we were stranded after the hurricane, SafeBridge connected us with volunteers who brought supplies.",
            "author": "Michael T., Hurricane Survivor"
        },
        {
            "quote": "The AI-powered chat assistant guided me through administering first aid until medical help arrived.",
            "author": "Priya K., Community Volunteer"
        }
    ]
    
    cols = st.columns(3)
    for i, testimonial in enumerate(testimonials):
        with cols[i]:
            st.markdown(f"""
            <div class="card">
                <p>"{testimonial['quote']}"</p>
                <p><em>- {testimonial['author']}</em></p>
            </div>
            """, unsafe_allow_html=True)

def main():
    display_header()
    display_home_content()

if __name__ == "__main__":
    main()
