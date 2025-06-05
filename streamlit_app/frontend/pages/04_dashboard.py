"""
SafeBridge - Dashboard Page
This is the main dashboard view that changes based on the user's role.
"""

import streamlit as st
import sys
import os
from streamlit_extras.switch_page_button import switch_page
import datetime

# Add parent directory to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.auth import init_session_state, get_current_user, check_authentication
from backend.database import get_all_requests,update_request_status
from backend.models import chat_with_llama,image_to_text_mistral
from backend.requests_matcher import match_responders_to_requests



# Configure the Streamlit page
st.set_page_config(
    page_title="Dashboard - SafeBridge",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .dashboard-card {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        height: 100%;
    }
    .dashboard-card h3 {
        color: #333;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: linear-gradient(90deg, #1E88E5, #9C27B0);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    .request-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #ccc;
    }
    .request-card.high {
        border-left: 4px solid #f44336;
    }
    .request-card.medium {
        border-left: 4px solid #ff9800;
    }
    .request-card.low {
        border-left: 4px solid #4caf50;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-pending {
        background-color: #ffe082;
        color: #ff8f00;
    }
    .status-processing {
        background-color: #90caf9;
        color: #1565c0;
    }
    .status-resolved {
        background-color: #a5d6a7;
        color: #2e7d32;
    }
    .sidebar-header {
        margin-left: 1rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def display_task_cards(user_id,matches_response):
    """
    Display task cards for the current responder with action buttons
    
    Args:
        user_id: ID of the current user/responder
    """
    # Get matches from our agent
    
    
    if "error" in matches_response:
        st.error(f"Failed to match responders: {matches_response['error']}")
        return
    
    if "message" in matches_response and "matches" not in matches_response:
        st.info(matches_response["message"])
        return
    
    # Find tasks assigned to this user
    matches = matches_response.get("matches", {})
    user_tasks = []
    print(user_id)
    print(matches)
    for request_id, match_data in matches.items():
        if "matches" in match_data:
            for match in match_data["matches"]:
                if match.get("responder_id") == user_id:
                    # This task is matched to the current user
                    user_tasks.append({
                        "request_id": request_id,
                        "match_reason": match.get("match_reason", "You're a good match for this request"),
                        "action_plan": match.get("action_plan", "No specific instructions provided")
                    })
    
    if not user_tasks:
        st.info("No tasks are currently matched to you.")
        return
    
    # Get request details from database
    all_requests_response = get_all_requests()
    if "data" not in all_requests_response:
        st.error("Failed to fetch request details")
        return
        
    all_requests = {req["id"]: req for req in all_requests_response["data"]}
    
    st.markdown("### Your Matched Tasks")
    st.markdown("These tasks have been matched to your skills and experience:")
    
    for i, task in enumerate(user_tasks):
        request_id = task['request_id']
        request_details = all_requests.get(request_id, {})
        
        with st.container():
            # Create a card-like container for each task
            urgency = request_details.get("urgency", "Unknown")
            urgency_class = "high" if urgency == "High" else "medium" if urgency == "Medium" else "low"
            
            st.markdown(f"""
            <div class="request-card {urgency_class}">
                <h4>{request_details.get("type", "Emergency")} Request in {request_details.get("location", "Unknown location")}</h4>
                <p>{request_details.get("text", "No details available")}</p>
                <div style="font-size: 0.9rem; color: #555; margin-top: 10px;">
                    <strong>Urgency:</strong> {urgency} • 
                    <strong>Submitted:</strong> {format_timestamp(request_details.get("timestamp"))}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Task details
            st.markdown(f"**Why you're matched:** {task['match_reason']}")
            
            # Action plan in an expander
            with st.expander("View Action Plan"):
                st.markdown(task['action_plan'])
            
            # Action buttons in columns
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Take Action", key=f"take_{task['request_id']}"):
                    # Update request status to "processing"
                    update_response = update_request_status(task['request_id'], "processing")
                    
                    if "error" in update_response:
                        st.error(f"Failed to update request: {update_response['error']}")
                    else:
                        st.success("Task marked as in progress!")
                        st.rerun()
            
            with col2:
                if st.button("Mark Complete", key=f"complete_{task['request_id']}"):
                    # Update request status to "finished"
                    update_response = update_request_status(task['request_id'], "resolved")
                    
                    if "error" in update_response:
                        st.error(f"Failed to update request: {update_response['error']}")
                    else:
                        st.success("Task marked as complete!")
                        st.rerun()

def get_recent_requests(user_requests, hours=1):
    """Get requests from the past specified hours (default: 1 hour)
    
    Args:
        user_requests: List of request dictionaries
        hours: Number of hours to look back (default: 1)
        
    Returns:
        List of recent request dictionaries
    """
    if not user_requests:
        return []
    
    current_time = datetime.datetime.now().timestamp() * 1000  # Convert to milliseconds
    time_threshold = current_time - (hours * 60 * 60 * 1000)  # hours to milliseconds
    
    # Filter requests by timestamp
    recent = [req for req in user_requests if req.get("timestamp", 0) >= time_threshold]
    
    # Sort by timestamp (newest first)
    sorted_requests = sorted(recent, key=lambda x: x.get("timestamp", 0), reverse=True)
    
    return sorted_requests

def format_timestamp(timestamp):
    """Convert timestamp to human readable format"""
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except:
        return "Invalid date"

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

def render_affected_individual_dashboard():
    """Render dashboard for affected individuals"""
    st.markdown('<h1 class="main-title">Your Dashboard</h1>', unsafe_allow_html=True)
    
    # User requests
    response = get_all_requests()
    if "data" in response:
        user_requests = response["data"]
        
        # Statistics row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Total Requests</div>
            </div>
            """.format(len(user_requests)), unsafe_allow_html=True)
        
        with col2:
            pending_count = sum(1 for r in user_requests if r.get("status") == "pending")
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Pending Requests</div>
            </div>
            """.format(pending_count), unsafe_allow_html=True)
            
        with col3:
            resolved_count = sum(1 for r in user_requests if r.get("status") == "resolved")
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Resolved Requests</div>
            </div>
            """.format(resolved_count), unsafe_allow_html=True)
        
            st.divider()
        st.markdown("### 🕒 Recent Requests")

        if not user_requests:
            st.info("You haven't submitted any requests yet.")
        else:
            recent_requests = get_recent_requests(user_requests)

        if not recent_requests:
                st.info("No requests in the past hour. Showing your most recent requests instead.")
                recent_requests = sorted(user_requests, key=lambda x: x.get("timestamp", 0), reverse=True)[:5]

        if recent_requests:
                # Display in a Streamlit "card"
                with st.container():
                    
                    
                    for req in recent_requests:
                        # Time formatting
                        timestamp = req.get("timestamp", 0)
                        if timestamp > 0:
                            time_diff = (datetime.datetime.now().timestamp() * 1000) - timestamp
                            minutes_ago = int(time_diff / (60 * 1000))
                            time_str = f"{minutes_ago} min ago" if minutes_ago < 60 else f"{int(minutes_ago / 60)} hr ago"
                        else:
                            time_str = "Unknown"

                        # Format line
                        urgency = req.get("urgency", "Unknown").capitalize()
                        location = req.get("location", "Not specified")
                        status = req.get("status", "pending").capitalize()

                        st.write(f"- {urgency} | {location} | {time_str} | {status}")
        else:
                st.info("No recent requests found.")
                st.divider()
    # Quick actions
    st.markdown("### Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Submit New Request", use_container_width=True):
            switch_page("request")
    
    with col2:
        if st.button("Contact Emergency Services", use_container_width=True):
            switch_page("chat")
            
    # Safety tips
    st.markdown("### Safety Tips")
    with st.expander("Emergency Preparedness", expanded=False):
        st.markdown("""
        - Keep an emergency kit with water, non-perishable food, medications, and first aid supplies
        - Create a family communication plan with meeting points and emergency contacts
        - Know evacuation routes from your home and community
        - Stay informed through emergency alerts and weather updates
        """)
    
    with st.expander("During a Disaster", expanded=False):
        st.markdown("""
        - Follow evacuation orders from local authorities
        - Stay away from damaged buildings, bridges, and utility wires
        - If trapped, signal for help using light, sound, or phone if available
        - Conserve your phone battery by limiting use to essential communications
        """)
#----------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------Volunteers------------------------------------------------------------------------------   
#----------------------------------------------------------------------------------------------------------------------------------

def render_volunteer_dashboard():
    """Render dashboard for volunteers"""
    st.markdown('<h1 class="main-title">Volunteer Dashboard</h1>', unsafe_allow_html=True)
    user = get_current_user()
    user_id = user.get("id")
    user_role = user.get("role")
    
    if user_role not in ["volunteer", "first_responder"]:
        st.error("This dashboard is only for volunteers and first responders")
        return
    
    # Display welcome message
    st.markdown(f"# Welcome, {user.get('fullName')}")
    st.markdown(f"Role: **{user_role.replace('_', ' ').title()}**")
    
    # Stats section
    st.markdown("## 📊 Overview")
    col1, col2, col3 = st.columns(3)
    
    # Use our request matcher to get stats
    matches_response = match_responders_to_requests()
    
    # Calculate stats
    total_pending = 0
    tasks_for_user = 0
    
    if "matches" in matches_response:
        matches = matches_response.get("matches", {})
        total_pending = len(matches)
        
        # Count matches for this user
        for request_id, match_data in matches.items():
            if "matches" in match_data:
                for match in match_data["matches"]:
                    if match.get("responder_id") == user_id:
                        tasks_for_user += 1
    
    with col1:
        st.metric("Total Pending Requests", total_pending)
    
    with col2:
        st.metric("Tasks Matched to You", tasks_for_user)
    
    with col3:
        # Get requests the user has taken action on
        all_requests = get_all_requests().get("data", [])
        in_progress = sum(1 for r in all_requests if r.get("status") == "processing" and r.get("assigned_to") == user_id)
        st.metric("Tasks In Progress", in_progress)
    
    # Display task cards
    st.markdown("## 📋 Your Tasks")
    display_task_cards(user_id,matches_response=matches_response)
    
    # Recent activity section
    st.markdown("## 🕒 Recent Activity")
    
    # Show recent requests in the system
    all_requests = get_all_requests().get("data", [])
    sorted_requests = sorted(all_requests, key=lambda r: r.get("timestamp", 0), reverse=True)[:5]
    
    for req in sorted_requests:
        status = req.get("status", "pending")
        status_emoji = "🟠" if status == "pending" else "🔵" if status == "processing" else "✅"
        
        st.markdown(f"{status_emoji} **{req.get('type')}** request - {req.get('urgency')} urgency - {format_timestamp(req.get('timestamp'))}")
    # Statistics row
    response = get_all_requests()
    if "data" in response:
        all_requests = response["data"]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Total Requests</div>
            </div>
            """.format(len(all_requests)), unsafe_allow_html=True)
        
        with col2:
            pending_count = sum(1 for r in all_requests if r.get("status") == "pending")
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Pending Requests</div>
            </div>
            """.format(pending_count), unsafe_allow_html=True)
            
        with col3:
            processing_count = sum(1 for r in all_requests if r.get("status") == "processing")
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">In Progress</div>
            </div>
            """.format(processing_count), unsafe_allow_html=True)
            
        with col4:
            resolved_count = sum(1 for r in all_requests if r.get("status") == "resolved")
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">{}</div>
                <div class="stat-label">Resolved</div>
            </div>
            """.format(resolved_count), unsafe_allow_html=True)
        
        # Pending requests
        st.markdown("### Requests Needing Assistance")
        # All active emergency requests
        st.markdown("### All Active Emergency Requests")
        active_requests = [r for r in all_requests if r.get("status") != "resolved"]
        
        if not active_requests:
            st.info("No active requests at this time")
        else:
            # Sort by urgency and timestamp
            urgency_order = {"High": 0, "Medium": 1, "Low": 2, "Unknown": 3}
            sorted_requests = sorted(active_requests, 
                                    key=lambda x: (urgency_order.get(x.get("urgency", "Unknown"), 4), 
                                                -(x.get("timestamp", 0) or 0)))
            
            # Create tabs for different urgency levels
            tabs = st.tabs(["All", "High", "Medium", "Low"])
            
            for tab_idx, tab in enumerate(tabs):
                with tab:
                    if tab_idx == 0:
                        filtered = sorted_requests
                    elif tab_idx == 1:
                        filtered = [r for r in sorted_requests if r.get("urgency") == "High"]
                    elif tab_idx == 2:
                        filtered = [r for r in sorted_requests if r.get("urgency") == "Medium"]
                    else:
                        filtered = [r for r in sorted_requests if r.get("urgency") == "Low"]
                    
                    if not filtered:
                        st.info(f"No {'active' if tab_idx == 0 else tab.label.lower() + ' urgency'} requests")
                        continue
                        
                    for i, request in enumerate(filtered):
                        urgency_class = "low"
                        if request.get("urgency") == "High":
                            urgency_class = "high"
                        elif request.get("urgency") == "Medium":
                            urgency_class = "medium"

                        text = request.get("text", "")
                        prompt = f"Request: {text}\nLocation: {request.get('location', 'Unknown')}\nUrgency: {request.get('urgency', 'Unknown')} make a summery and list of instructions to how to handle the situations"
                        summery = chat_with_llama(prompt,history="")
                        status_class = f"status-{request.get('status', 'pending')}"
                        
                        with st.expander(f"{request.get('type', 'General')} - {request.get('location', 'Unknown')}"):
                            st.markdown(f"""
                            <div style ='color:#455;' class="request-card {urgency_class}">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                    <div>
                                        <strong>{request.get("type", "General")} Request</strong> • 
                                        <span class="status-badge {status_class}">{request.get("status", "pending")}</span>
                                    </div>
                                    <div style="color: #777; font-size: 0.8rem;">{format_timestamp(request.get("timestamp"))}</div>
                                </div>
                                <p>{summery}</p>
                                <div style="font-size: 0.9rem; color: #555;">
                                    <strong>Location:</strong> {request.get("location", "Not specified")} • 
                                    <strong>Urgency:</strong> {request.get("urgency", "Unknown")}
                                </div>
                                <div style="font-size: 0.9rem; color: #555;">
                                    <strong>Last Updated:</strong> {format_timestamp(request.get("lastUpdated"))}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            
                            if request.get("status") == "pending":
                                if st.button("Take Action", key=f"take_{tab_idx}_{i}", use_container_width=True):
                                    from backend.database import update_request_status
                                    update_response = update_request_status(request.get("id"), "processing")
                                    if "data" in update_response:
                                        st.success("Request status updated!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error updating request: {update_response.get('error', 'Unknown error')}")
                            elif request.get("status") == "processing":
                                if st.button("Mark Resolved", key=f"resolve_{tab_idx}_{i}", use_container_width=True):
                                    from backend.database import update_request_status
                                    update_response = update_request_status(request.get("id"), "resolved")
                                    if "data" in update_response:
                                        st.success("Request marked as resolved!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error updating request: {update_response.get('error', 'Unknown error')}")
    if st.button("🗺️ View Emergency Map", key="Map"):
            switch_page("map")

#----------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------First Responders------------------------------------------------------------------------------   
#----------------------------------------------------------------------------------------------------------------------------------


def render_first_responder_dashboard():
    """Render dashboard for first responders - similar to volunteer but with more authority"""
    st.markdown('<h1 class="main-title">First Responder Dashboard</h1>', unsafe_allow_html=True)
    # Get user info
    user = get_current_user()
    user_id = user.get("id")
    user_role = user.get("role")
    
    if user_role not in ["volunteer", "first_responder"]:
        st.error("This dashboard is only for volunteers and first responders")
        return
    
    # Display welcome message
    st.markdown(f"# Welcome, {user.get('fullName')}")
    st.markdown(f"Role: **{user_role.replace('_', ' ').title()}**")
    
    # Stats section
    st.markdown("## 📊 Overview")

    col1, col2, col3 = st.columns(3)
    
    # Use our request matcher to get stats
    matches_response = match_responders_to_requests()
    
    # Calculate stats
    total_pending = 0
    tasks_for_user = 0
    
    if "matches" in matches_response:
        matches = matches_response.get("matches", {})
        total_pending = len(matches)
        
        # Count matches for this user
        for request_id, match_data in matches.items():
            if "matches" in match_data:
                for match in match_data["matches"]:
                    if match.get("responder_id") == user_id:
                        tasks_for_user += 1
    
    with col1:
        st.metric("Total Pending Requests", total_pending)
    
    with col2:
        st.metric("Tasks Matched to You", tasks_for_user)
    
    with col3:
        # Get requests the user has taken action on
        all_requests = get_all_requests().get("data", [])
        in_progress = sum(1 for r in all_requests if r.get("status") == "processing" and r.get("assigned_to") == user_id)
        st.metric("Tasks In Progress", in_progress)
    
    # Display task cards
    st.markdown("## 📋 Your Tasks")
    display_task_cards(user_id,matches_response=matches_response)
    
    # Recent activity section
    st.markdown("## 🕒 Recent Activity")
    
    # Show recent requests in the system
    all_requests = get_all_requests().get("data", [])
    sorted_requests = sorted(all_requests, key=lambda r: r.get("timestamp", 0), reverse=True)[:5]
    
    for req in sorted_requests:
        status = req.get("status", "pending")
        status_emoji = "🟠" if status == "pending" else "🔵" if status == "processing" else "✅"
        
        st.markdown(f"{status_emoji} **{req.get('type')}** request - {req.get('urgency')} urgency - {format_timestamp(req.get('timestamp'))}")
    # Statistics row
    response = get_all_requests()
    if "data" in response:
        all_requests = response["data"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            high_urgency = sum(1 for r in all_requests if r.get("urgency") == "High" and r.get("status") != "resolved")
            st.markdown("""
            <div class="stat-card" style="background: linear-gradient(90deg, #f44336, #ff9800);">
                <div class="stat-number">{}</div>
                <div class="stat-label">High Urgency</div>
            </div>
            """.format(high_urgency), unsafe_allow_html=True)
        
        with col2:
            medium_urgency = sum(1 for r in all_requests if r.get("urgency") == "Medium" and r.get("status") != "resolved")
            st.markdown("""
            <div class="stat-card" style="background: linear-gradient(90deg, #ff9800, #ffc107);">
                <div class="stat-number">{}</div>
                <div class="stat-label">Medium Urgency</div>
            </div>
            """.format(medium_urgency), unsafe_allow_html=True)
            
        with col3:
            low_urgency = sum(1 for r in all_requests if r.get("urgency") == "Low" and r.get("status") != "resolved")
            st.markdown("""
            <div class="stat-card" style="background: linear-gradient(90deg, #4caf50, #8bc34a);">
                <div class="stat-number">{}</div>
                <div class="stat-label">Low Urgency</div>
            </div>
            """.format(low_urgency), unsafe_allow_html=True)
        
        # Priority requests
        st.markdown("### Priority Emergency Requests")
        high_requests = [r for r in all_requests if r.get("urgency") == "High" and r.get("status") == "pending"]
        if not high_requests:
            st.success("No high-priority requests at this time!")
        else:
            for i, request in enumerate(sorted(high_requests, key=lambda x: -(x.get("timestamp", 0) or 0))):
                with st.container():
                    st.markdown(f"""
                    <div class="request-card high">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <div>
                                <strong>{request.get("type", "General")} Emergency</strong> • 
                                <span style="color: #f44336; font-weight: bold;">HIGH URGENCY</span>
                            </div>
                            <div style="color: #777; font-size: 0.8rem;">{format_timestamp(request.get("timestamp"))}</div>
                        </div>
                        <p>{request.get("text", "")}</p>
                        <div style="font-size: 0.9rem; color: #555;">
                            <strong>Location:</strong> {request.get("location", "Not specified")}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Deploy Response Team", key=f"deploy_{i}", use_container_width=True):
                            from backend.database import update_request_status
                            update_response = update_request_status(request.get("id"), "processing")                            
                            if "data" in update_response:
                                st.success("Response team deployed!")
                                st.rerun()
                        else:
                            st.error(f"Error deploying team: {update_response.get('error', 'Unknown error')}")
                        
        # All active emergency requests
        st.markdown("### All Active Emergency Requests")
        active_requests = [r for r in all_requests if r.get("status") != "resolved"]
        
        if not active_requests:
            st.info("No active requests at this time")
        else:
            # Sort by urgency and timestamp
            urgency_order = {"High": 0, "Medium": 1, "Low": 2, "Unknown": 3}
            sorted_requests = sorted(active_requests, 
                                    key=lambda x: (urgency_order.get(x.get("urgency", "Unknown"), 4), 
                                                -(x.get("timestamp", 0) or 0)))
            
            # Create tabs for different urgency levels
            tabs = st.tabs(["All", "High", "Medium", "Low"])
            
            for tab_idx, tab in enumerate(tabs):
                with tab:
                    if tab_idx == 0:
                        filtered = sorted_requests
                    elif tab_idx == 1:
                        filtered = [r for r in sorted_requests if r.get("urgency") == "High"]
                    elif tab_idx == 2:
                        filtered = [r for r in sorted_requests if r.get("urgency") == "Medium"]
                    else:
                        filtered = [r for r in sorted_requests if r.get("urgency") == "Low"]
                    
                    if not filtered:
                        st.info(f"No {'active' if tab_idx == 0 else tab.label.lower() + ' urgency'} requests")
                        continue
                        
                    for i, request in enumerate(filtered):
                        urgency_class = "low"
                        if request.get("urgency") == "High":
                            urgency_class = "high"
                        elif request.get("urgency") == "Medium":
                            urgency_class = "medium"

                        text = request.get("text", "")
                        prompt = f"Request: {text}\nLocation: {request.get('location', 'Unknown')}\nUrgency: {request.get('urgency', 'Unknown')} make a summery and list of instructions to how to handle the situations"
                        summery = chat_with_llama(prompt,history="")
                        status_class = f"status-{request.get('status', 'pending')}"
                        
                        with st.expander(f"{request.get('type', 'General')} - {request.get('location', 'Unknown')}"):
                            st.markdown(f"""
                            <div style ='color:#455;' class="request-card {urgency_class}">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                    <div>
                                        <strong>{request.get("type", "General")} Request</strong> • 
                                        <span class="status-badge {status_class}">{request.get("status", "pending")}</span>
                                    </div>
                                    <div style="color: #777; font-size: 0.8rem;">{format_timestamp(request.get("timestamp"))}</div>
                                </div>
                                <p>{summery}</p>
                                <div style="font-size: 0.9rem; color: #555;">
                                    <strong>Location:</strong> {request.get("location", "Not specified")} • 
                                    <strong>Urgency:</strong> {request.get("urgency", "Unknown")}
                                </div>
                                <div style="font-size: 0.9rem; color: #555;">
                                    <strong>Last Updated:</strong> {format_timestamp(request.get("lastUpdated"))}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            
                            if request.get("status") == "pending":
                                if st.button("Take Action", key=f"take_{tab_idx}_{i}", use_container_width=True):
                                    from backend.database import update_request_status
                                    update_response = update_request_status(request.get("id"), "processing")
                                    if "data" in update_response:
                                        st.success("Request status updated!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error updating request: {update_response.get('error', 'Unknown error')}")
                            elif request.get("status") == "processing":
                                if st.button("Mark Resolved", key=f"resolve_{tab_idx}_{i}", use_container_width=True):
                                    from backend.database import update_request_status
                                    update_response = update_request_status(request.get("id"), "resolved")
                                    if "data" in update_response:
                                        st.success("Request marked as resolved!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error updating request: {update_response.get('error', 'Unknown error')}")
        # Add a nicely styled button for the Map page
        
        if st.button("🗺️ View Emergency Map", key="Map"):
            switch_page("map")

    else:
        st.error(f"Error loading requests: {response.get('error', 'Unknown error')}")

def main():
    # Check authentication
    user = check_authentication()
    
    # Render sidebar
    render_sidebar()
    
    # Render dashboard based on user role
    if user["role"] == "affected_individual":
        render_affected_individual_dashboard()
    elif user["role"] == "volunteer":
        render_volunteer_dashboard()
    elif user["role"] == "first_responder":
        render_first_responder_dashboard()
    else:
        st.error("Unknown user role")

if __name__ == "__main__":
    main()
