"""
SafeBridge - Submit Request Page
This page allows users to submit emergency requests.
"""

import streamlit as st
import sys
import os
from streamlit_extras.switch_page_button import switch_page

# Add parent directory to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.auth import init_session_state, get_current_user, check_authentication
from backend.database import submit_request
from streamlit_js_eval import streamlit_js_eval

# Configure the Streamlit page
st.set_page_config(
    page_title="Submit Request - SafeBridge",
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
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #555;
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
    .urgency-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .urgency-option {
        flex: 1;
        padding: 1rem;
        text-align: center;
        border-radius: 8px;
        margin: 0 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .urgency-high {
        background-color: #ffebee;
        color: #c62828;
        border: 2px solid #ef9a9a;
    }
    .urgency-high:hover, .urgency-high.selected {
        background-color: #ef9a9a;
        color: #b71c1c;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    .urgency-medium {
        background-color: #fff8e1;
        color: #f57f17;
        border: 2px solid #ffe082;
    }
    .urgency-medium:hover, .urgency-medium.selected {
        background-color: #ffe082;
        color: #f57f17;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    .urgency-low {
        background-color: #e8f5e9;
        color: #2e7d32;
        border: 2px solid #a5d6a7;
    }
    .urgency-low:hover, .urgency-low.selected {
        background-color: #a5d6a7;
        color: #2e7d32;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with navigation"""
    user = get_current_user()
    
    with st.sidebar:
        st.markdown("### 🌊 SafeBridge")
        st.markdown(f"Welcome, **{user['fullName']}**")
        st.markdown(f"Role: **{user['role']}**")
        st.markdown("---")
        
        # Navigation options        
        if st.button("📊 Dashboard", use_container_width=True):
            st.rerun()
        if st.button("📝 Submit Request", use_container_width=True):
            switch_page("request")
        
        if st.button("💬 AI Chat", use_container_width=True):
            switch_page("chat")
        
        if st.button("🗺️ Map ",use_container_width=True):
            switch_page("map")
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            switch_page("app")


def render_request_form():
    """Render the request submission form"""
    st.markdown('<h1 class="main-title">Submit Emergency Request</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Please provide details about your emergency situation</p>', unsafe_allow_html=True)
    
    # Form for request submission
    with st.form("request_form"):
        # Emergency type
        request_type = st.selectbox(
            "Type of Emergency",
            options=["Medical", "Food", "Shelter", "Evacuation", "Other"],
            index=0,
        )
        
        # Request text details
        request_text = st.text_area(
            "Describe your emergency situation",
            placeholder="Please provide details about your emergency...",
            height=150,
        )
        # Upload Image or Record Voice with icons and buttons
        
        st.markdown("#### Attach Visuals (Optional)")

        col_img, col_audio = st.columns(2)

        with col_img:
            image_data = st.camera_input("Capture Image (optional)", key="camera_input")
            if image_data:
                st.image(image_data, caption="Captured Image", use_column_width=True)
            st.session_state["captured_image"] = image_data

        with col_audio:

            # Optionally, you can allow file upload for audio as a workaround
            audio_file = st.file_uploader("Or upload an audio file", type=["wav", "mp3", "m4a"], key="audio_upload")
            if audio_file:
                st.audio(audio_file, format="audio/wav")


        # Urgency selection
        st.markdown("### Urgency Level")
        urgency_col1, urgency_col2, urgency_col3 = st.columns(3)
        
        with urgency_col1:
            high_urgency = st.checkbox("High Urgency", value=False, key="high_urgency")
            st.markdown("""
            <div style="text-align: center; color: #c62828; font-size: 0.9rem;">
                Life-threatening situation requiring immediate attention
            </div>
            """, unsafe_allow_html=True)
            
        with urgency_col2:
            medium_urgency = st.checkbox("Medium Urgency", value=True, key="medium_urgency")
            st.markdown("""
            <div style="text-align: center; color: #f57f17; font-size: 0.9rem;">
                Urgent but not immediately life-threatening
            </div>
            """, unsafe_allow_html=True)
            
        with urgency_col3:
            low_urgency = st.checkbox("Low Urgency", value=False, key="low_urgency")
            st.markdown("""
            <div style="text-align: center; color: #2e7d32; font-size: 0.9rem;">
                Requires assistance but not time-sensitive
            </div>
            """, unsafe_allow_html=True)
        
        # Location (auto-detect if possible)
        if "auto_location" not in st.session_state:
            st.session_state["auto_location"] = ""

        # Try to get location from browser using streamlit-js-eval

        js_code = """
        navigator.geolocation.getCurrentPosition(
            (pos) => {
            const coords = pos.coords.latitude + "," + pos.coords.longitude;
            window.parent.postMessage({type: "streamlit:setComponentValue", value: coords}, "*");
            },
            (err) => {
            window.parent.postMessage({type: "streamlit:setComponentValue", value: ""}, "*");
            }
        );
        """
        location_coords = streamlit_js_eval(js_expressions=js_code, key="get_location", want_output=True)
        if location_coords and isinstance(location_coords, str) and "," in location_coords:
            st.session_state["auto_location"] = location_coords

        # Show location input with auto-detected value as default
        location = st.text_input(
            "Your Location (auto-detected if possible)",
            value=st.session_state["auto_location"] or get_current_user().get("location", ""),
            placeholder="E.g., 123 Main St, Apartment 4B, Downtown or coordinates"
        )
        if st.session_state["auto_location"]:
            st.info(f"Detected coordinates: {st.session_state['auto_location']}")

        # Submit button
        submitted = st.form_submit_button("Submit Request", use_container_width=True)
        
        if submitted:
            # Validate form
            if not request_text:
                st.error("Please describe your emergency situation")
                return
            
            if not location:
                st.error("Please provide your location")
                return
            
            # Determine urgency level
            urgency = "Medium"  # Default
            if high_urgency:
                urgency = "High"
            elif low_urgency:
                urgency = "Low"
            
            # Submit request to database
            request_data = {
                "text": request_text,
                "urgency": urgency,
                "type": request_type,
                "location": location
            }
            
            response = submit_request(request_data)
            
            if "data" in response:
                st.success("Your request has been submitted successfully")
                st.balloons()
               
            else:
                st.error(f"Error submitting request: {response.get('error', 'Unknown error')}")

    # Add option to go to dashboard
    st.markdown("### What would you like to do next?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Another Request", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Go to Dashboard", use_container_width=True):
            switch_page("dashboard")

def main():
    # Check authentication
    check_authentication()
    
    # Render sidebar
    render_sidebar()
    
    # Create columns for centering content
    _, center_col, _ = st.columns([1, 3, 1])
    
    with center_col:
        render_request_form()

if __name__ == "__main__":
    main()
