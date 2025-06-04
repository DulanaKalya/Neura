"""
SafeBridge - Submit Request Page
This page allows users to submit emergency requests.
"""

import streamlit as st
import sys
import os
from PIL import Image
from streamlit_extras.switch_page_button import switch_page

# Add parent directory to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.auth import init_session_state, get_current_user, check_authentication
from backend.database import submit_request
from backend.models import image_to_text_mistral
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

         # Store AI analysis results in session state if not already present
        if "ai_analysis" not in st.session_state:
            st.session_state["ai_analysis"] = ""
        
        # Upload Image or Record Voice with icons and buttons
        st.markdown("#### Attach Visuals (Optional)")

        col_img, col_upload = st.columns(2)

        with col_img:
            image_data = st.camera_input("Capture Image (optional)", key="camera_input")
            
            # If image is captured and hasn't been analyzed yet
            if image_data and not st.session_state.get("image_analyzed"):
                # Display the captured image
                st.image(image_data, caption="Captured Image", use_column_width=True)
                
                # Process image with Mistral
                with st.spinner('Analyzing disaster image...'):
                    try:
                        # Convert to PIL Image
                        image = Image.open(image_data)
                        
                        # Create prompt for disaster analysis
                        analysis_prompt = """
                        Analyze this disaster image and provide a concise assessment of:
                        1. Type of disaster visible
                        2. Visible damage or hazards
                        3. Any immediate safety concerns
                        
                        Keep it brief and factual for emergency responders.
                        """
                        
                        # Get analysis from Mistral
                        analysis = image_to_text_mistral(image, analysis_prompt)
                        
                        # Store in session state
                        st.session_state["ai_analysis"] = analysis
                        st.session_state["image_analyzed"] = True
                        
                        # Show the analysis
                        st.success("AI analysis complete!")
                        st.info(f"AI assessment: {analysis}")
                        
                        # Offer to append to request
                        st.session_state["append_analysis"] = True
                        
                    except Exception as e:
                        st.error(f"Error analyzing image: {str(e)}")
            
            # If image was previously analyzed, show the analysis
            elif image_data and st.session_state.get("image_analyzed"):
                st.image(image_data, caption="Captured Image", use_column_width=True)
                st.info(f"AI assessment: {st.session_state['ai_analysis']}")
                
            st.session_state["captured_image"] = image_data
        with col_upload:
            # Changed from audio to image upload
            uploaded_image = st.file_uploader("Or upload an image file", type=["jpg", "jpeg", "png"], key="image_upload")
            
            # If image is uploaded and hasn't been analyzed yet
            if uploaded_image and not st.session_state.get("uploaded_image_analyzed"):
                # Display the uploaded image
                st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
                
                # Process image with Mistral
                with st.spinner('Analyzing uploaded disaster image...'):
                    try:
                        # Convert to PIL Image
                        image = Image.open(uploaded_image)
                        
                        # Create prompt for disaster analysis
                        analysis_prompt = """
                        Analyze this disaster image and provide a concise assessment of:
                        1. Type of disaster visible
                        2. Visible damage or hazards
                        3. Any immediate safety concerns
                        
                        Keep it brief and factual for emergency responders.
                        """
                        
                        # Get analysis from Mistral
                        analysis = image_to_text_mistral(image, analysis_prompt)
                        
                        # Store in session state
                        st.session_state["uploaded_ai_analysis"] = analysis
                        st.session_state["uploaded_image_analyzed"] = True
                        
                        # Show the analysis
                        st.success("AI analysis complete!")
                        st.info(f"AI assessment: {analysis}")
                        
                        # Set the analysis to be used in the form
                        st.session_state["ai_analysis"] = analysis
                        st.session_state["image_analyzed"] = True
                        
                    except Exception as e:
                        st.error(f"Error analyzing uploaded image: {str(e)}")
            
            # If uploaded image was previously analyzed, show the analysis
            elif uploaded_image and st.session_state.get("uploaded_image_analyzed"):
                st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
                st.info(f"AI assessment: {st.session_state['uploaded_ai_analysis']}")
                
            st.session_state["uploaded_image"] = uploaded_image
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
            
            # Append AI analysis to request text if available
            full_request_text = request_text
            if st.session_state.get("ai_analysis"):
                full_request_text += f"\n\n[AI Image Analysis]: {st.session_state['ai_analysis']}"
            
            # Submit request to database
            request_data = {
                "text": full_request_text,
                "urgency": urgency,
                "type": request_type,
                "location": location
            }
            
            response = submit_request(request_data)
            
            if "data" in response:
                st.success("Your request has been submitted successfully")
                st.balloons()  # Add balloons animation for successful submission
                
                # Clear the session state for next request
                st.session_state["ai_analysis"] = ""
                st.session_state["image_analyzed"] = False
            else:
                st.error(f"Error submitting request: {response.get('error', 'Unknown error')}")

    # Add option to go to dashboard
    st.markdown("### What would you like to do next?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Another Request", use_container_width=True):
            # Clear analysis data for new request
            if "ai_analysis" in st.session_state:
                del st.session_state["ai_analysis"]
            if "image_analyzed" in st.session_state:
                del st.session_state["image_analyzed"]
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
