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
from backend.database import get_all_requests

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
    """Render map legend"""
    st.markdown("""
    <div class="legend">
        <h4 style="margin-bottom: 15px; color: #333;">🗺️ Map Legend</h4>
        <div class="legend-item">
            <div class="legend-color" style="background-color: red; border: 2px solid #333;"></div>
            <span style="font-size: 14px;">High Urgency - Pending</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: orange; border: 2px solid #333;"></div>
            <span style="font-size: 14px;">Medium Urgency - Pending/Processing</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: yellow; border: 2px solid #333;"></div>
            <span style="font-size: 14px;">Low Urgency - Pending</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: blue; border: 2px solid #333;"></div>
            <span style="font-size: 14px;">Medium Urgency - Processing</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: lightblue; border: 2px solid #333;"></div>
            <span style="font-size: 14px;">Low Urgency - Processing</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: green; border: 2px solid #333;"></div>
            <span style="font-size: 14px;">Resolved Cases</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_statistics(requests_data):
    """Render statistics for emergency requests"""
    if not requests_data:
        return
    
    total_requests = len(requests_data)
    pending_requests = sum(1 for r in requests_data if r.get("status") == "pending")
    processing_requests = sum(1 for r in requests_data if r.get("status") == "processing")
    resolved_requests = sum(1 for r in requests_data if r.get("status") == "resolved")
    high_urgency = sum(1 for r in requests_data if r.get("urgency") == "High")
    
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
            <div class="stat-number" style="color: #ff9800;">{}</div>
            <div class="stat-label">Processing</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #4caf50;">{}</div>
            <div class="stat-label">Resolved</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #e91e63;">{}</div>
            <div class="stat-label">High Urgency</div>
        </div>
    </div>
    """.format(total_requests, pending_requests, processing_requests, resolved_requests, high_urgency), 
    unsafe_allow_html=True)

def render_map_filters():
    """Render map filters"""
    st.markdown('<div class="map-controls">', unsafe_allow_html=True)
    st.markdown("#### 🔍 Filter Cases")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Status",
            options=["pending", "processing", "resolved"],
            default=["pending", "processing", "resolved"]
        )
    
    with col2:
        urgency_filter = st.multiselect(
            "Urgency",
            options=["High", "Medium", "Low"],
            default=["High", "Medium", "Low"]
        )
    
    with col3:
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
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return status_filter, urgency_filter, type_filter, time_filter

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

def create_emergency_map(requests_data):
    """Create and return the emergency map with caching"""
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
    valid_requests = 0
    marker_coords = []  # Store coordinates for auto-fitting
    
    for request in requests_data:
        location = request.get("location", "")
        if not location:
            continue
        
        # Use cached geocoding
        lat, lon = cached_geocode_address(location)
        
        if lat is None or lon is None:
            continue
        
        valid_requests += 1
        marker_coords.append([lat, lon])
        
        # Get marker properties
        color = get_marker_color(request.get("status", "pending"), request.get("urgency", "Medium"))
        icon = get_marker_icon(request.get("type", "Other"))
        
        # Create popup content
        popup_content = format_popup_content(request)
        
        # Add marker
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{request.get('type', 'Unknown')} - {request.get('urgency', 'Unknown')} - {request.get('status', 'Unknown').title()}",
            icon=folium.Icon(
                color=color,
                icon=icon,
                prefix='glyphicon'
            )
        ).add_to(m)
    
    # Only adjust bounds if we have markers and they're outside Sri Lanka's default view
    if valid_requests > 0 and marker_coords:
        # Check if any markers are outside Sri Lanka bounds
        markers_outside_sl = any(
            coord[0] < sri_lanka_bounds[0][0] or coord[0] > sri_lanka_bounds[1][0] or
            coord[1] < sri_lanka_bounds[0][1] or coord[1] > sri_lanka_bounds[1][1]
            for coord in marker_coords
        )
        
        # Only fit to markers if they're outside Sri Lanka or if we want to zoom in on a specific area
        if markers_outside_sl or valid_requests <= 5:
            m.fit_bounds(marker_coords)
    
    return m

def main():
    # Check authentication
    check_authentication()
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    st.markdown('<h1 class="main-title">🗺️ Emergency Cases Map</h1>', unsafe_allow_html=True)
    

    # Initialize session state for map data caching
    if 'map_data_cache' not in st.session_state:
        st.session_state.map_data_cache = None
    if 'last_filter_state' not in st.session_state:
        st.session_state.last_filter_state = None

    # Get all requests (cache to avoid repeated API calls)
    if st.session_state.map_data_cache is None:
        with st.spinner("Loading emergency data..."):
            response = get_all_requests()
        
        if "data" not in response:
            st.error(f"Error loading data: {response.get('error', 'Unknown error')}")
            return
    
        requests_data = response["data"]
        st.session_state.map_data_cache = requests_data
    else:
        requests_data = st.session_state.map_data_cache
    
    if not requests_data:
        st.info("No emergency requests found.")
        # Add refresh button
        if st.button("🔄 Refresh Data"):
            st.session_state.map_data_cache = None
            st.rerun()
        return
    
    # Render statistics
    render_statistics(requests_data)
    
    # Render filters
    status_filter, urgency_filter, type_filter, time_filter = render_map_filters()
    
    
    # Create filter state for caching
    current_filter_state = {
        'status': status_filter,
        'urgency': urgency_filter,
        'type': type_filter,
        'time': time_filter
    }
    
    # Filter requests
    filtered_requests = filter_requests(requests_data, status_filter, urgency_filter, type_filter, time_filter)
    
    if not filtered_requests:
        st.warning("No requests match the selected filters.")
        # Add refresh button
        if st.button("🔄 Refresh Data"):
            st.session_state.map_data_cache = None
            st.rerun()
        return
    
    st.info(f"Showing {len(filtered_requests)} out of {len(requests_data)} total cases")
    
    # Add refresh button for manual data refresh
    col_refresh, col_info = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh Data"):
            st.session_state.map_data_cache = None
            st.rerun()
    
    # Create columns for map and legend
    col1, col2 = st.columns([4, 1])
    
    with col2:
        render_map_legend()
    
    with col1:
        # Create and display map
        with st.spinner("Generating map..."):
            emergency_map = create_emergency_map(filtered_requests)
        
        # Display map with key to prevent unnecessary reruns
        # Use a unique key based on filter state to prevent rerun on every interaction
        map_key = f"emergency_map_{hash(str(current_filter_state))}"
        
        # Display map with minimal returned objects to reduce rerun triggers
        map_data = st_folium(
            emergency_map, 
            width=700, 
            height=500,
            returned_objects=["last_clicked"],  # Reduced from "last_object_clicked"
            key=map_key
        )
        
        # Handle map interactions without triggering rerun
        if map_data.get("last_clicked") and map_data["last_clicked"].get("lat"):
            clicked_lat = map_data["last_clicked"]["lat"]
            clicked_lng = map_data["last_clicked"]["lng"]
            st.info(f"📍 Map clicked at: {clicked_lat:.4f}, {clicked_lng:.4f}")
    
    # Additional information
    st.markdown("---")
    
    # Create expandable sections to reduce initial load
    with st.expander("📋 Recent Activity", expanded=False):
        # Show recent requests in a table
        recent_requests = sorted(filtered_requests, key=lambda x: x.get("timestamp", 0), reverse=True)[:10]
        
        if recent_requests:
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

if __name__ == "__main__":
    main()