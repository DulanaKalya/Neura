"""
SafeBridge - Emergency Cases Map
This page displays all emergency requests on an interactive map.
"""

import streamlit as st
import sys
import os
import folium
from streamlit_folium import st_folium
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
from streamlit_extras.switch_page_button import switch_page

# Add parent directory to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.auth import init_session_state, get_current_user, check_authentication
from backend.database import get_all_requests, get_all_responders

# Configure the Streamlit page
st.set_page_config(
    page_title="Emergency Map - SafeBridge",
    page_icon="🗺️",
    layout="wide",
)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_geocode_address(address):
    """Cached version of geocode_address_with_fallback"""
    return geocode_address_with_fallback(address)


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
    .map-controls {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .legend {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 0.8rem;
        padding: 0.2rem 0;
    }
    .legend-color {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 12px;
        border: 2px solid #333;
        flex-shrink: 0;
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    .stat-box {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        min-width: 120px;
        margin-bottom: 0.5rem;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

def geocode_address(address):
    """
    Convert address to coordinates using a geocoding service
    For demo purposes, using Nominatim (OpenStreetMap)
    """
    try:
        # Check if it's already coordinates (latitude,longitude format)
        if "," in address and len(address.split(",")) == 2:
            coords = address.split(",")
            # Try to convert to float - if successful, it's coordinates
            try:
                lat = float(coords[0].strip())
                lon = float(coords[1].strip())
                # Validate coordinate ranges
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
                else:
                    # Invalid coordinate range, treat as address
                    pass
            except ValueError:
                # Not numeric coordinates, treat as address
                pass
        
        # Use Nominatim for geocoding addresses
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        
        # Add User-Agent header to comply with Nominatim usage policy
        headers = {
            "User-Agent": "SafeBridge-Emergency-App/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                lat = float(result["lat"])
                lon = float(result["lon"])
                return lat, lon
            else:
                st.warning(f"No results found for address: {address}")
        else:
            st.warning(f"Geocoding service returned status code: {response.status_code}")
            
    except requests.exceptions.Timeout:
        st.warning(f"Timeout while geocoding address: {address}")
    except requests.exceptions.RequestException as e:
        st.warning(f"Network error while geocoding address: {address}. Error: {str(e)}")
    except Exception as e:
        #st.warning(f"Could not geocode address: {address}. Error: {str(e)}")
        pass
    
    return None, None

def geocode_address_with_fallback(address):
    """
    Enhanced geocoding with fallback options for Sri Lankan locations
    """
    if not address or address.strip() == "":
        return None, None
    
    # Try the main geocoding function first
    lat, lon = geocode_address(address)
    if lat is not None and lon is not None:
        return lat, lon
    
    # Fallback: Try with "Sri Lanka" appended
    if "sri lanka" not in address.lower():
        enhanced_address = f"{address}, Sri Lanka"
        lat, lon = geocode_address(enhanced_address)
        if lat is not None and lon is not None:
            return lat, lon
    
    # Fallback: Try common Sri Lankan location mappings
    sri_lankan_locations = {
        "chilaw": (7.5759, 79.7953),
        "bingiriya": (7.5667, 80.1000),
        "colombo": (6.9271, 79.8612),
        "kandy": (7.2906, 80.6337),
        "galle": (6.0535, 80.2210),
        "jaffna": (9.6615, 80.0255),
        "anuradhapura": (8.3114, 80.4037),
        "trincomalee": (8.5874, 81.2152),
        "batticaloa": (7.7102, 81.6924),
        "ratnapura": (6.6828, 80.3992),
        "negombo": (7.2083, 79.8358),
        "matara": (5.9549, 80.5550),
        "kurunegala": (7.4863, 80.3647),
        "badulla": (6.9934, 81.0550),
        "polonnaruwa": (7.9403, 81.0188)
    }
    
    # Check if the address contains any known Sri Lankan location
    address_lower = address.lower()
    for location, coords in sri_lankan_locations.items():
        if location in address_lower:
            st.info(f"Using fallback coordinates for {location}")
            return coords
    
    # Last fallback: Default to Colombo, Sri Lanka
    # st.warning(f"Could not geocode '{address}'. Using default location (Colombo, Sri Lanka)")
    return 6.9271, 79.8612  # Colombo coordinates

def load_responders_and_volunteers():
    """Load first responders and volunteers from database"""
    try:
        response = get_all_responders()
        if "data" not in response:
            st.error(f"Error loading responders: {response.get('error', 'Unknown error')}")
            return []
        return response["data"]
    except Exception as e:
        st.error(f"Error loading responders and volunteers: {e}")
        return []

def create_responder_icon(person_type, is_available):
    """Create custom icons for volunteers and first responders"""
    if person_type.lower() == 'volunteer':
        # Volunteer icons - Heart symbol
        color = 'green' if is_available else 'red'
        icon = 'heart'
    else:  # first_responder
        # First responder icons - Plus symbol
        color = 'blue' if is_available else 'gray'
        icon = 'plus'
    
    return folium.Icon(
        color=color,
        icon=icon,
        prefix='glyphicon'
    )

def format_specialities(specialities):
    """Format specialities list for display"""
    if isinstance(specialities, list):
        return ', '.join(specialities) if specialities else 'Not specified'
    elif isinstance(specialities, str):
        return specialities if specialities.strip() else 'Not specified'
    else:
        return 'Not specified'

def create_responder_popup_content(person_data):
    """Create HTML content for responder popup"""
    name = person_data.get('fullName', person_data.get('name', 'Unknown'))
    location = person_data.get('location', 'Location not available')
    specialities = format_specialities(person_data.get('specialities', []))
    in_action = person_data.get('inAction', False)
    person_type = person_data.get('role', 'unknown')
    
    # Status and type formatting
    status = "🔴 Busy" if in_action else "🟢 Available"
    type_emoji = "🚑" if person_type.lower() == 'first_responder' else "❤️"
    type_label = f"{type_emoji} {person_type.replace('_', ' ').title()}"
    
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; min-width: 250px;">
        <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #ddd; padding-bottom: 8px;">
            {name}
        </h4>
        <div style="margin: 8px 0;">
            <strong>{type_label}</strong>
        </div>
        <div style="margin: 8px 0;">
            <strong>📍 Location:</strong> {location}
        </div>
        <div style="margin: 8px 0;">
            <strong>🛠️ Specialities:</strong> {specialities}
        </div>
        <div style="margin: 8px 0;">
            <strong>Status:</strong> {status}
        </div>
        <div style="margin-top: 10px; font-size: 0.85em; color: #666;">
            Click to view more details
        </div>
    </div>
    """
    return popup_html


def get_marker_color(status, urgency):
    """Get marker color based on status and urgency"""
    if status == "resolved":
        return "green"
    elif status == "processing":
        if urgency == "High":
            return "orange"
        elif urgency == "Medium":
            return "blue"
        else:
            return "lightblue"
    else:  # pending
        if urgency == "High":
            return "red"
        elif urgency == "Medium":
            return "orange"
        else:
            return "yellow"

def get_marker_icon(request_type):
    """Get marker icon based on request type"""
    icon_map = {
        "Medical": "plus",
        "Food": "cutlery",
        "Shelter": "home",
        "Evacuation": "arrow-right",
        "Other": "info-sign"
    }
    return icon_map.get(request_type, "info-sign")

def format_popup_content(request):
    """Format popup content for map markers"""
    timestamp = request.get("timestamp", 0)
    if timestamp:
        dt = datetime.fromtimestamp(timestamp / 1000)
        time_str = dt.strftime("%b %d, %Y %I:%M %p")
    else:
        time_str = "Unknown"
    
    popup_html = f"""
    <div style="min-width: 250px;">
        <h4 style="margin-bottom: 10px; color: #333;">
            {request.get('type', 'Unknown')} Emergency
        </h4>
        <p><strong>Status:</strong> 
            <span style="color: {'green' if request.get('status') == 'resolved' else 'orange' if request.get('status') == 'processing' else 'red'};">
                {request.get('status', 'Unknown').title()}
            </span>
        </p>
        <p><strong>Urgency:</strong> 
            <span style="color: {'red' if request.get('urgency') == 'High' else 'orange' if request.get('urgency') == 'Medium' else 'green'};">
                {request.get('urgency', 'Unknown')}
            </span>
        </p>
        <p><strong>Location:</strong> {request.get('location', 'Not specified')}</p>
        <p><strong>Submitted:</strong> {time_str}</p>
        <p><strong>Description:</strong></p>
        <p style="font-style: italic; max-width: 200px; word-wrap: break-word;">
            {request.get('text', 'No description')[:100]}...
        </p>
        <p><strong>Request ID:</strong> {request.get('id', 'Unknown')}</p>
    </div>
    """
    return popup_html

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

def render_map_legend():
    """Map legend including responders and volunteers"""
    st.markdown("#### 🗺️ Map Legend")
    
    # Emergency Cases Legend
    st.markdown("**Emergency Cases:**")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: red; border-radius: 50%; margin: 5px;"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("High Urgency - Pending")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: orange; border-radius: 50%; margin: 5px;"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("Medium Urgency")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: yellow; border-radius: 50%; margin: 5px;"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("Low Urgency - Pending")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: green; border-radius: 50%; margin: 5px;"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("Resolved Cases")
    
    st.markdown("---")
    
    # Responders & Volunteers Legend
    st.markdown("**Responders & Volunteers:**")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: blue; border-radius: 50%; margin: 5px; color: white; text-align: center; line-height: 20px; font-size: 12px;">+</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("🚑 First Responder - Available")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: gray; border-radius: 50%; margin: 5px; color: white; text-align: center; line-height: 20px; font-size: 12px;">+</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("🚑 First Responder - Busy")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: green; border-radius: 50%; margin: 5px; color: white; text-align: center; line-height: 20px; font-size: 12px;">♥</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("❤️ Volunteer - Available")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: red; border-radius: 50%; margin: 5px; color: white; text-align: center; line-height: 20px; font-size: 12px;">♥</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("❤️ Volunteer - Busy")
    
    st.markdown("---")
    
    # Cluster Markers Legend
    st.markdown("**Cluster Markers:**")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div style="width: 20px; height: 20px; background-color: black; border-radius: 50%; margin: 5px; color: white; text-align: center; line-height: 20px; font-size: 10px;">i</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("Multiple Items at Location")

def render_statistics(requests_data,responders_data):
    """Render enhanced statistics including responders and volunteers"""

    # Emergency requests stats
    total_requests = len(requests_data) if requests_data else 0
    pending_requests = sum(1 for r in requests_data if r.get("status") == "pending") if requests_data else 0
    high_urgency = sum(1 for r in requests_data if r.get("urgency") == "High") if requests_data else 0
    
    # Responders and volunteers stats
    total_responders = len(responders_data) if responders_data else 0
    available_responders = sum(1 for r in responders_data if not r.get("inAction", False)) if responders_data else 0
    first_responders = sum(1 for r in responders_data if r.get("role", "").lower() == "first_responder") if responders_data else 0
    volunteers = sum(1 for r in responders_data if r.get("role", "").lower() == "volunteer") if responders_data else 0
    
    st.markdown("""
    <div class="stats-container">
        <div class="stat-box">
            <div class="stat-number" style="color: #1E88E5;">{}</div>
            <div class="stat-label">Total Cases</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #f44336;">{}</div>
            <div class="stat-label">Pending</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #e91e63;">{}</div>
            <div class="stat-label">High Urgency</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #4caf50;">{}</div>
            <div class="stat-label">Available Help</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #2196f3;">{}</div>
            <div class="stat-label">First Responders</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #ff5722;">{}</div>
            <div class="stat-label">Volunteers</div>
        </div>
    </div>
    """.format(total_requests, pending_requests, high_urgency, available_responders, first_responders, volunteers), 
    unsafe_allow_html=True)

def render_map_filters():
    """Render map filters"""
    st.markdown('<div class="map-controls">', unsafe_allow_html=True)
    st.markdown("#### 🔍 Filter Map Content")
    
    # Main content filters
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Show on Map:**")
        show_cases = st.checkbox("🚨 Emergency Cases", value=True)
        show_responders = st.checkbox("🚑 First Responders", value=True)
        show_volunteers = st.checkbox("❤️ Volunteers", value=True)
    
    with col2:
        st.markdown("**Availability Filter:**")
        availability_filter = st.selectbox(
            "Responder/Volunteer Availability",
            ["Show All", "Available Only", "Busy Only"],
            index=0
        )
    
    # Emergency case filters (only show if cases are enabled)
    if show_cases:
        st.markdown("**Emergency Case Filters:**")
        col3, col4, col5 = st.columns(3)
        
        with col3:
            status_filter = st.multiselect(
                "Status",
                options=["pending", "processing", "resolved"],
                default=["pending", "processing", "resolved"]
            )
        
        with col4:
            urgency_filter = st.multiselect(
                "Urgency",
                options=["High", "Medium", "Low"],
                default=["High", "Medium", "Low"]
            )
        
        with col5:
            type_filter = st.multiselect(
                "Emergency Type",
                options=["Medical", "Food", "Shelter", "Evacuation", "Other"],
                default=["Medical", "Food", "Shelter", "Evacuation", "Other"]
            )
        
        # Time filter
        time_filter = st.selectbox(
            "Time Range",
            options=["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
            index=0
        )
    else:
        # Default values when cases are not shown
        status_filter = ["pending", "processing", "resolved"]
        urgency_filter = ["High", "Medium", "Low"]
        type_filter = ["Medical", "Food", "Shelter", "Evacuation", "Other"]
        time_filter = "All Time"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return (show_cases, show_responders, show_volunteers, availability_filter, 
            status_filter, urgency_filter, type_filter, time_filter)

def filter_requests(requests_data, status_filter, urgency_filter, type_filter, time_filter):
    """Filter requests based on selected criteria"""
    if not requests_data:
        return []
    
    filtered_requests = []
    current_time = datetime.now().timestamp() * 1000
    
    for request in requests_data:
        # Status filter
        if request.get("status") not in status_filter:
            continue
        
        # Urgency filter
        if request.get("urgency") not in urgency_filter:
            continue
        
        # Type filter
        if request.get("type") not in type_filter:
            continue
        
        # Time filter
        if time_filter != "All Time":
            request_time = request.get("timestamp", 0)
            if request_time:
                time_diff = current_time - request_time
                hours_diff = time_diff / (1000 * 60 * 60)
                
                if time_filter == "Last 24 Hours" and hours_diff > 24:
                    continue
                elif time_filter == "Last 7 Days" and hours_diff > (24 * 7):
                    continue
                elif time_filter == "Last 30 Days" and hours_diff > (24 * 30):
                    continue
        
        filtered_requests.append(request)
    
    return filtered_requests

def create_emergency_map(requests_data,responders_data,filters):
    """Create and return the emergency map with caching"""
    (show_cases, show_responders, show_volunteers, availability_filter, 
     status_filter, urgency_filter, type_filter, time_filter) = filters
    # Sri Lanka bounds for better default view
    sri_lanka_bounds = [
        [5.9, 79.6],  # Southwest corner
        [9.9, 81.9]   # Northeast corner
    ]
    
    # Default center to Sri Lanka (Central location)
    center_lat, center_lon = 7.3731, 80.7718  # Center of Sri Lanka
    
    # Create map with Sri Lanka focus
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,  # Optimal zoom to show entire Sri Lanka
        tiles="OpenStreetMap"
    )
    
    # Set bounds to Sri Lanka
    m.fit_bounds(sri_lanka_bounds)
    
    # Add markers for each request
    location_groups = {}
    marker_coords = []  # Store coordinates for auto-fitting
    
    if show_cases and requests_data:
        filtered_requests = filter_requests(requests_data, status_filter, urgency_filter, type_filter, time_filter)
        
        for request in filtered_requests:
            location = request.get("location", "")
            if not location:
                continue
        
            # Use cached geocoding
            lat, lon = cached_geocode_address(location)
        
            if lat is None or lon is None:
                continue
        
            marker_coords.append([lat, lon])
            lat_rounded = round(lat, 3)
            lon_rounded = round(lon, 3)
            coord_key = f"{lat_rounded},{lon_rounded}"

            if coord_key not in location_groups:
                location_groups[coord_key] = {
                    'lat': lat,
                    'lon': lon,
                    'requests': [],
                    'responders': []
                }
        
            location_groups[coord_key]['requests'].append(request)

    
    # Add responders and volunteers markers
    if (show_responders or show_volunteers) and responders_data:
        for person in responders_data:
            person_type = person.get('role', '').lower()

            if person_type == 'first_responder' and not show_responders:
                continue
            if person_type == 'volunteer' and not show_volunteers:
                continue

            # Filter by availability
            in_action = person.get('inAction', False)
            if availability_filter == "Available Only" and in_action:
                continue
            elif availability_filter == "Busy Only" and not in_action:
                continue

            location = person.get("location", "")
            if not location:
                continue
            
            # Use cached geocoding
            lat, lon = cached_geocode_address(location)
            
            if lat is None or lon is None:
                continue
            
            marker_coords.append([lat, lon])
            
            # Round coordinates to group nearby markers
            lat_rounded = round(lat, 3)
            lon_rounded = round(lon, 3)
            coord_key = f"{lat_rounded},{lon_rounded}"
            
            if coord_key not in location_groups:
                location_groups[coord_key] = {
                    'lat': lat,
                    'lon': lon,
                    'requests': [],
                    'responders': []
                }
            
            location_groups[coord_key]['responders'].append(person)

    # Create markers for each location group
    for coord_key, group in location_groups.items():
        requests = group['requests']
        responders = group['responders']
        base_lat = group['lat']
        base_lon = group['lon']
        
        # If only one item at this location, create single marker
        if len(requests) + len(responders) == 1:
            if requests:
                request = requests[0]
                color = get_marker_color(request.get("status", "pending"), request.get("urgency", "Medium"))
                icon = get_marker_icon(request.get("type", "Other"))
                popup_content = format_popup_content(request)
                tooltip = f"{request.get('type', 'Unknown')} - {request.get('urgency', 'Unknown')} - {request.get('status', 'Unknown').title()}"
                
                folium.Marker(
                    location=[base_lat, base_lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=tooltip,
                    icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
                ).add_to(m)
            
            elif responders:
                person = responders[0]
                person_type = person.get('role', '').lower()
                is_available = not person.get('inAction', False)
                icon = create_responder_icon(person_type, is_available)
                popup_content = create_responder_popup_content(person)
                status_text = "Available" if is_available else "Busy"
                tooltip = f"{person_type.replace('_', ' ').title()}: {person.get('fullName', 'Unknown')} - {status_text}"
                
                folium.Marker(
                    location=[base_lat, base_lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=tooltip,
                    icon=icon
                ).add_to(m)
        
        else:
            # Multiple items at same location - create cluster or offset markers
            offset_distance = 0.001  # Small offset to separate markers
            total_items = len(requests) + len(responders)
            
            # Create a circular arrangement for overlapping markers
            import math
            for i, request in enumerate(requests):
                angle = (2 * math.pi * i) / total_items
                lat_offset = base_lat + (offset_distance * math.cos(angle))
                lon_offset = base_lon + (offset_distance * math.sin(angle))
                
                color = get_marker_color(request.get("status", "pending"), request.get("urgency", "Medium"))
                icon = get_marker_icon(request.get("type", "Other"))
                popup_content = format_popup_content(request)
                tooltip = f"📍 {request.get('type', 'Unknown')} - {request.get('urgency', 'Unknown')} - {request.get('status', 'Unknown').title()}"
                
                folium.Marker(
                    location=[lat_offset, lon_offset],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=tooltip,
                    icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
                ).add_to(m)
            
            # Add responders with offset
            for j, person in enumerate(responders):
                angle = (2 * math.pi * (len(requests) + j)) / total_items
                lat_offset = base_lat + (offset_distance * math.cos(angle))
                lon_offset = base_lon + (offset_distance * math.sin(angle))
                
                person_type = person.get('role', '').lower()
                is_available = not person.get('inAction', False)
                icon = create_responder_icon(person_type, is_available)
                popup_content = create_responder_popup_content(person)
                status_text = "Available" if is_available else "Busy"
                tooltip = f"👤 {person_type.replace('_', ' ').title()}: {person.get('fullName', 'Unknown')} - {status_text}"
                
                folium.Marker(
                    location=[lat_offset, lon_offset],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=tooltip,
                    icon=icon
                ).add_to(m)
            
            # Add a central info marker showing the count
            cluster_popup = f"""
            <div style="font-family: Arial, sans-serif; min-width: 200px; text-align: center;">
                <h4 style="margin-bottom: 15px; color: #333;">📍 Multiple Items at this Location</h4>
                <p><strong>Emergency Cases:</strong> {len(requests)}</p>
                <p><strong>Responders/Volunteers:</strong> {len(responders)}</p>
                <hr>
                <p style="font-size: 0.9em; color: #666;">
                    Individual markers are slightly offset around this location
                </p>
            </div>
            """
            
            folium.Marker(
                location=[base_lat, base_lon],
                popup=folium.Popup(cluster_popup, max_width=250),
                tooltip=f"📍 {total_items} items at this location",
                icon=folium.Icon(color='black', icon='info-sign', prefix='glyphicon')
            ).add_to(m)

    # Adjust map bounds if we have markers
    if marker_coords:
        # Check if any markers are outside Sri Lanka bounds
        markers_outside_sl = any(
            coord[0] < sri_lanka_bounds[0][0] or coord[0] > sri_lanka_bounds[1][0] or
            coord[1] < sri_lanka_bounds[0][1] or coord[1] > sri_lanka_bounds[1][1]
            for coord in marker_coords
        )
        
        # Only fit to markers if they're outside Sri Lanka or if we want to zoom in on a specific area
        if markers_outside_sl or len(marker_coords) <= 5:
            m.fit_bounds(marker_coords)
    
    return m

def main():
    # Check authentication
    check_authentication()
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    st.markdown('<h1 class="main-title">🗺️ Emergency Resources Map</h1>', unsafe_allow_html=True)
    

    # Initialize session state for map data caching
    if 'map_data_cache' not in st.session_state:
        st.session_state.map_data_cache = None
    if 'responders_data_cache' not in st.session_state:
        st.session_state.responders_data_cache = None
    if 'last_filter_state' not in st.session_state:
        st.session_state.last_filter_state = None

    # Get all requests (cache to avoid repeated API calls)
    if st.session_state.map_data_cache is None:
        with st.spinner("Loading emergency data..."):
            response = get_all_requests()
        if "data" not in response:
            st.error(f"Error loading data: {response.get('error', 'Unknown error')}")
            return
        st.session_state.map_data_cache = response["data"]

    if st.session_state.responders_data_cache is None:
        with st.spinner("Loading responders and volunteers..."):
            st.session_state.responders_data_cache = load_responders_and_volunteers()   #Everything handled inside this func

    requests_data = st.session_state.map_data_cache or []
    responders_data = st.session_state.responders_data_cache or []
    
    if not requests_data and not responders_data:
        st.info("No Data found.")
        # Add refresh button
        if st.button("🔄 Refresh Data"):
            st.session_state.map_data_cache = None
            st.session_state.responders_data_cache = None
            st.rerun()
        return
    
    # Render statistics
    render_statistics(requests_data,responders_data)
    
    # Render filters
    filters = render_map_filters()    
    
    (show_cases, show_responders, show_volunteers, availability_filter, 
     status_filter, urgency_filter, type_filter, time_filter) = filters
    
    # Add refresh button for manual data refresh
    col_refresh, col_info = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh Data"):
            st.session_state.map_data_cache = None
            st.session_state.responders_data_cache = None
            st.rerun()

    with col_info:
        info_parts = []
        if show_cases:
            info_parts.append(f"{len(requests_data)} emergency cases")
        if show_responders or show_volunteers:
            responder_count = sum(1 for r in responders_data if r.get("role", "").lower() == "first_responder")
            volunteer_count = sum(1 for r in responders_data if r.get("role", "").lower() == "volunteer")
            if show_responders:
                info_parts.append(f"{responder_count} first responders")
            if show_volunteers:
                info_parts.append(f"{volunteer_count} volunteers")
        
        if info_parts:
            st.info(f"Displaying: {', '.join(info_parts)}")

    # Create columns for map and legend - FIXED LAYOUT
    map_col, legend_col = st.columns([8, 3])
    
    with map_col:
        # Create and display map
        with st.spinner("Generating map..."):
            emergency_map = create_emergency_map(requests_data, responders_data, filters)
        
        # Display map with key to prevent unnecessary reruns
        map_key = f"emergency_map_{hash(str(filters))}"
        
        # Display map with minimal returned objects to reduce rerun triggers
        map_data = st_folium(
            emergency_map, 
            width=700, 
            height=500,
            returned_objects=["last_clicked"],
            key=map_key
        )
        
        # Handle map interactions without triggering rerun
        if map_data.get("last_clicked") and map_data["last_clicked"].get("lat"):
            clicked_lat = map_data["last_clicked"]["lat"]
            clicked_lng = map_data["last_clicked"]["lng"]
            st.info(f"📍 Map clicked at: {clicked_lat:.4f}, {clicked_lng:.4f}")
    
    with legend_col:
        # LEGEND NOW PROPERLY RENDERED IN RIGHT COLUMN
        with st.container():
            render_map_legend()


    # Additional information
    st.markdown("---")
    
    # Get filtered requests for expandable sections
    filtered_requests = filter_requests(requests_data, status_filter, urgency_filter, type_filter, time_filter) if show_cases else []
    
    # Filter responders based on availability filter
    filtered_responders = []
    if show_responders or show_volunteers:
        for person in responders_data:
            person_type = person.get('role', '').lower()
            
            # Type filter
            if person_type == 'first_responder' and not show_responders:
                continue
            if person_type == 'volunteer' and not show_volunteers:
                continue
            
            # Availability filter
            in_action = person.get('inAction', False)
            if availability_filter == "Available Only" and in_action:
                continue
            elif availability_filter == "Busy Only" and not in_action:
                continue
            
            filtered_responders.append(person)

    # Create expandable sections to reduce initial load
    with st.expander("📋 Recent Emergency Activity", expanded=False):
        if filtered_requests:
            # Show recent requests in a table
            recent_requests = sorted(filtered_requests, key=lambda x: x.get("timestamp", 0), reverse=True)[:10]
            
            df_data = []
            for req in recent_requests:
                timestamp = req.get("timestamp", 0)
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    time_str = dt.strftime("%b %d, %I:%M %p")
                else:
                    time_str = "Unknown"
                
                df_data.append({
                    "Time": time_str,
                    "Type": req.get("type", "Unknown"),
                    "Urgency": req.get("urgency", "Unknown"),
                    "Status": req.get("status", "pending").title(),
                    "Location": req.get("location", "Not specified")[:30] + "..." if len(req.get("location", "")) > 30 else req.get("location", "Not specified")
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No emergency cases match the current filters.")
    
    # Add responders and volunteers information
    with st.expander("👥 Available Responders & Volunteers", expanded=False):
        if filtered_responders:
            # Create tabs for different views
            tab1, tab2 = st.tabs(["📊 Summary", "📋 Detailed List"])
            
            with tab1:
                # Summary statistics
                available_count = sum(1 for r in filtered_responders if not r.get("inAction", False))
                busy_count = len(filtered_responders) - available_count
                first_responder_count = sum(1 for r in filtered_responders if r.get("role", "").lower() == "first_responder")
                volunteer_count = sum(1 for r in filtered_responders if r.get("role", "").lower() == "volunteer")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🟢 Available", available_count)
                with col2:
                    st.metric("🔴 Busy", busy_count)
                with col3:
                    st.metric("🚑 First Responders", first_responder_count)
                with col4:
                    st.metric("❤️ Volunteers", volunteer_count)
            
            with tab2:
                # Detailed list
                responder_data = []
                for person in filtered_responders:
                    status = "🟢 Available" if not person.get("inAction", False) else "🔴 Busy"
                    role_emoji = "🚑" if person.get("role", "").lower() == "first_responder" else "❤️"
                    
                    responder_data.append({
                        "Name": person.get("fullName", "Unknown"),
                        "Role": f"{role_emoji} {person.get('role', 'Unknown').replace('_', ' ').title()}",
                        "Status": status,
                        "Location": person.get("location", "Not specified")[:25] + "..." if len(person.get("location", "")) > 25 else person.get("location", "Not specified"),
                        "Specialities": format_specialities(person.get("specialities", []))[:30] + "..." if len(format_specialities(person.get("specialities", []))) > 30 else format_specialities(person.get("specialities", []))
                    })
                
                if responder_data:
                    df_responders = pd.DataFrame(responder_data)
                    st.dataframe(df_responders, use_container_width=True)
        else:
            st.info("No responders or volunteers match the current filters.")
    
    # Add detailed case view in expandable section
    with st.expander("🔍 Detailed Case Information", expanded=False):
        if filtered_requests:
            selected_case = st.selectbox(
                "Select a case to view details:",
                options=range(len(filtered_requests)),
                format_func=lambda x: f"{filtered_requests[x].get('type', 'Unknown')} - {filtered_requests[x].get('urgency', 'Unknown')} - {filtered_requests[x].get('location', 'Unknown')[:20]}..."
            )
            
            if selected_case is not None:
                case = filtered_requests[selected_case]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Type:** {case.get('type', 'Unknown')}")
                    st.write(f"**Status:** {case.get('status', 'Unknown').title()}")
                    st.write(f"**Urgency:** {case.get('urgency', 'Unknown')}")
                    st.write(f"**Location:** {case.get('location', 'Not specified')}")
                
                with col2:
                    timestamp = case.get("timestamp", 0)
                    if timestamp:
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        time_str = dt.strftime("%b %d, %Y %I:%M %p")
                    else:
                        time_str = "Unknown"
                    st.write(f"**Submitted:** {time_str}")
                    st.write(f"**Request ID:** {case.get('id', 'Unknown')}")
                
                st.write("**Description:**")
                st.write(case.get('text', 'No description available'))
        else:
            st.info("No emergency cases available to display details.")
    
    # Add responder details section
    with st.expander("👤 Responder/Volunteer Details", expanded=False):
        if filtered_responders:
            selected_responder = st.selectbox(
                "Select a responder/volunteer to view details:",
                options=range(len(filtered_responders)),
                format_func=lambda x: f"{filtered_responders[x].get('fullName', 'Unknown')} - {filtered_responders[x].get('role', 'Unknown').replace('_', ' ').title()}"
            )
            
            if selected_responder is not None:
                responder = filtered_responders[selected_responder]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {responder.get('fullName', 'Unknown')}")
                    st.write(f"**Role:** {responder.get('role', 'Unknown').replace('_', ' ').title()}")
                    status = "🟢 Available" if not responder.get("inAction", False) else "🔴 Busy"
                    st.write(f"**Status:** {status}")
                    st.write(f"**Location:** {responder.get('location', 'Not specified')}")
                
                with col2:
                    st.write(f"**Email:** {responder.get('email', 'Not provided')}")
                    st.write(f"**Phone:** {responder.get('phone', 'Not provided')}")
                    st.write(f"**Experience:** {responder.get('experience', 'Not specified')}")
                
                st.write("**Specialities:**")
                specialities = responder.get('specialities', [])
                if isinstance(specialities, list) and specialities:
                    for spec in specialities:
                        st.write(f"• {spec}")
                else:
                    st.write("No specialities specified")
        else:
            st.info("No responders or volunteers available to display details.")


if __name__ == "__main__":
    main()