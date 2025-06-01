import sys
import os
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.models import chat_with_llama

# Page configuration
st.set_page_config(page_title="Emergency Assistant", page_icon="🆘", layout="wide")

# Define system prompt
EMERGENCY_SYSTEM_PROMPT = """You are an emergency assistance AI specifically trained to help people during natural disasters.
Your primary goal is to provide accurate, concise, and potentially life-saving information.
Focus on these disaster types: earthquakes, floods, hurricanes, wildfires, tsunamis, tornadoes, landslides, and extreme weather events.

When responding:
1. Prioritize immediate safety advice for the user's specific situation
2. Provide clear, actionable instructions
3. Consider evacuation guidance, shelter information, first aid, and resource conservation
4. Be factual, calm, and reassuring, but emphasize the seriousness of following official guidance
5. If medical advice is requested, emphasize the importance of professional medical care when available

Remember that your advice could impact human safety in critical situations. Always recommend contacting emergency services (911) for immediate life-threatening emergencies."""

# Initialize session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "I'm your Emergency Assistant. How can I help you with your current situation?"}
    ]

if "chat_history" not in st.session_state or not isinstance(st.session_state.chat_history, list):
    st.session_state.chat_history = []

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

def render_message(message, is_user=False):
    avatar = "👤" if is_user else "🆘"
    alignment = "flex-end" if is_user else "flex-start"
    bg_color = "#4A179C" if is_user else "#1E3BFA"
    st.markdown(f"""
    <div style="display: flex; justify-content: {alignment}; margin-bottom: 10px;">
        <div style="background-color: {bg_color}; padding: 10px 15px; border-radius: 15px; max-width: 80%;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="margin-right: 10px; font-size: 1.5rem;">{avatar}</div>
                <div><strong>{'You' if is_user else 'Emergency Assistant'}</strong></div>
            </div>
            <div>{message}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 Talk to Emergency Assistant")
    st.markdown("_Ask anything about natural disasters, emergency response, or survival tips._")

    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            render_message(message["content"], message["role"] == "user")

    # Check if we need to clear the input
    if "clear_input" in st.session_state and st.session_state["clear_input"]:
        st.session_state["user_input"] = ""
        st.session_state["clear_input"] = False

    user_input = st.text_area("Type your message:", height=100, key="user_input")
    

    if st.button("Send", use_container_width=True):
        if user_input.strip():
            # Store the current input before clearing
            current_input = user_input
            
            # Add user message to display history
            st.session_state.chat_messages.append({"role": "user", "content": current_input})
            
            # Create prompt with system instructions
            enhanced_prompt = f"{EMERGENCY_SYSTEM_PROMPT}\n\nUser question: {current_input}"

            # Format history for the model
            formatted_history = [
                (st.session_state.chat_history[i], st.session_state.chat_history[i + 1])
                for i in range(0, len(st.session_state.chat_history) - 1, 2)
                if isinstance(st.session_state.chat_history[i], str) and isinstance(st.session_state.chat_history[i + 1], str)
            ]

            # Get response from model
            with st.spinner("Generating response..."):
                try:
                    response = chat_with_llama(enhanced_prompt, history=formatted_history)
                except Exception as e:
                    response = "⚠️ An error occurred while contacting the AI model."
                    st.error(str(e))

            # Update chat history
            st.session_state.chat_history.append(current_input)
            st.session_state.chat_history.append(response)
            
            # Add assistant response to display
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            
            # Clear the input using a different approach - set a flag to clear on next render
            st.session_state["clear_input"] = True
            
            # Rerun to update the UI
            st.rerun()

with col2:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("<h3>Emergency Contacts</h3>", unsafe_allow_html=True)
    st.markdown("""
    - **Emergency Services:** 911
    - **FEMA Helpline:** 1-800-621-FEMA
    - **Disaster Distress Helpline:** 1-800-985-5990
    - **Red Cross:** 1-800-RED-CROSS
    - **Poison Control:** 1-800-222-1222
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("<h3>Quick Actions</h3>", unsafe_allow_html=True)
    if st.button("Submit Assistance Request", use_container_width=True):
        switch_page("request")
    if st.button("Return to Dashboard", use_container_width=True):
        switch_page("dashboard")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("<h3>Suggested Questions</h3>", unsafe_allow_html=True)
    disaster_types = ["Earthquake", "Flood", "Hurricane", "Wildfire", "Tornado"]
    selected_disaster = st.selectbox("Select disaster type:", disaster_types)

    questions = {
        "Earthquake": [
            "What should I do during an earthquake?",
            "How do I check my home for damage after an earthquake?",
            "Is it safe to use gas/electricity after an earthquake?",
            "What supplies should I have in my earthquake kit?",
            "How do I find the nearest earthquake shelter?"
        ],
        "Flood": [
            "Is it safe to drive through flood water?",
            "How do I protect my home from flooding?",
            "What should I do if water enters my home?",
            "What diseases can flood water carry?",
            "How do I purify water during a flood?"
        ],
        "Hurricane": [
            "Should I evacuate or shelter in place?",
            "How do I prepare my home for a hurricane?",
            "What supplies should I have for a hurricane?",
            "When is it safe to return after evacuation?",
            "How do I protect important documents?"
        ],
        "Wildfire": [
            "What should I do if trapped by a wildfire?",
            "How do I create a defensible space around my home?",
            "What items should I prioritize when evacuating?",
            "How do I protect myself from smoke inhalation?",
            "When is it safe to return after a wildfire?"
        ],
        "Tornado": [
            "Where is the safest place during a tornado?",
            "What's the difference between a watch and a warning?",
            "What should I do after a tornado?",
            "How do I identify tornado damage to my home?",
            "How can I stay informed about tornado alerts?"
        ]
    }

    for q in questions[selected_disaster]:
        st.markdown(f"- {q}")

    st.markdown('</div>', unsafe_allow_html=True)