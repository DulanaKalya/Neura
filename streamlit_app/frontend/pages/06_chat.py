import sys
import os
import streamlit as st
from PIL import Image
import datetime
from streamlit_extras.switch_page_button import switch_page

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.vector_db import EmergencyKnowledgeVectorDB
from backend.auth import init_session_state, get_current_user


# Add this import if you want image analysis
try:
    from backend.models import chat_with_llama, image_to_text_mistral
    IMAGE_ANALYSIS_AVAILABLE = True
except ImportError:
    from backend.models import chat_with_llama
    IMAGE_ANALYSIS_AVAILABLE = False
    st.warning("Image analysis not available - Mistral model not configured")

init_session_state()



# Initialize vector database
@st.cache_resource
def initialize_vector_db():
    """Initialize and load vector database"""
    try:
        # Initialize with local storage paths
        db = EmergencyKnowledgeVectorDB(
            local_storage_path="./data/vector_db",
            pdf_path="./data/pdfs"
        )
        
        # Try to load from local storage first
        success = db.initialize_with_fallback()
        
        if success:
            st.success("✅ Knowledge base initialized successfully!")
        else:
            st.error("❌ Failed to initialize knowledge base")
            
        return db
        
    except Exception as e:
        st.error(f"Error initializing vector database: {str(e)}")
        # Return a basic instance that can still work
        return EmergencyKnowledgeVectorDB(
            local_storage_path="./data/vector_db",
            pdf_path="./data/pdfs"
        )

# Load vector database
vector_db = initialize_vector_db()

def get_rag_context(query: str, k: int = 3) -> str:
    """
    Get relevant context from vector database
    """
    results = vector_db.search(query, k=k)
    
    if not results:
        return ""
    
    context_parts = []
    for doc, score in results:
        context_parts.append(f"**{doc['title']}** (Category: {doc['category']}):\n{doc['content']}")
    
    return "\n\n".join(context_parts)

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


def create_rag_prompt(user_query: str, context: str) -> str:
    """
    Create enhanced prompt with RAG context
    """
    return f"""You are an emergency assistance AI with access to specialized emergency response knowledge.

CONTEXT FROM EMERGENCY KNOWLEDGE BASE:
{context}

Based on the above context and your training, please provide accurate, actionable emergency guidance.

IMPORTANT GUIDELINES:
1. Prioritize immediate safety advice
2. Provide clear, step-by-step instructions
3. Always recommend contacting emergency services (911) for life-threatening situations
4. Use the context provided but supplement with your knowledge when needed
5. Be calm, reassuring, but emphasize the seriousness of following safety protocols

USER QUESTION: {user_query}

Please provide a comprehensive response:"""



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

IMAGE_ANALYSIS_PROMPT = """You are analyzing an emergency situation image. Please provide:
1. What type of emergency or disaster is visible
2. Assessment of severity level (Low/Medium/High)
3. Immediate safety concerns
4. Recommended actions based on what you see
5. What emergency services might be needed

Be specific and focus on actionable emergency response information."""



render_sidebar()


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
    bg_color = "#BAD99E" if is_user else "#A3AEF6"
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

    # Image upload section
    st.markdown("#### 📷 Image Analysis (Optional)")
    uploaded_image = st.file_uploader(
        "Upload an emergency image for analysis", 
        type=['png', 'jpg', 'jpeg'],
        key="emergency_image"
    )
    
    if uploaded_image:
        st.image(uploaded_image, caption="Emergency Image for Analysis", width=300)


    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            render_message(message["content"], message["role"] == "user")

    # Check if we need to clear the input
    if "clear_input" in st.session_state and st.session_state["clear_input"]:
        st.session_state["user_input"] = ""
        st.session_state["clear_input"] = False

    user_input = st.text_area("Type your message:", height=100, key="user_input")
    col_send, col_clear, col_rebuild = st.columns([2, 1, 1])

    with col_send:
        send_button = st.button("Send", use_container_width=True)
    
    with col_clear:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "I'm your Emergency Assistant with access to comprehensive disaster response knowledge. How can I help you with your current situation?"}
            ]
            st.session_state.chat_history = []
            st.rerun()

    with col_rebuild:
        if st.button("Rebuild KB", use_container_width=True):
            with st.spinner("Rebuilding knowledge base..."):
                try:
                    success = vector_db.build_vector_database(force_rebuild=True)
                    if success:
                        vector_db.save_locally()
                        st.success("Knowledge base rebuilt!")
                        # Clear cache to reload
                        st.cache_resource.clear()
                    else:
                        st.error("Failed to rebuild knowledge base")
                except Exception as e:
                    st.error(f"Error rebuilding: {str(e)}")
            st.rerun()


    if send_button and user_input.strip():
        current_input = user_input
        
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": current_input})
        
        # Handle image analysis if uploaded
        image_context = ""
        if uploaded_image:
            try:
                with st.spinner("Analyzing emergency image..."):
                    image = Image.open(uploaded_image)
                    image_analysis = image_to_text_mistral(image, IMAGE_ANALYSIS_PROMPT)
                    image_context = f"\n\nIMAGE ANALYSIS:\n{image_analysis}"
            except Exception as e:
                image_context = f"\n\nIMAGE ANALYSIS ERROR: {str(e)}"
        
        # Get RAG context
        with st.spinner("Searching knowledge base..."):
            rag_context = get_rag_context(current_input + image_context)
        
        # Create enhanced prompt
        enhanced_prompt = create_rag_prompt(current_input + image_context, rag_context)
        
        # Format history for the model
        formatted_history = [
            (st.session_state.chat_history[i], st.session_state.chat_history[i + 1])
            for i in range(0, len(st.session_state.chat_history) - 1, 2)
            if i + 1 < len(st.session_state.chat_history)
        ]
        
        # Get response from model
        with st.spinner("Generating response..."):
            try:
                response = chat_with_llama(enhanced_prompt, history=formatted_history)
                
                # Add context information
                if rag_context:
                    response += "\n\n---\n*This response was enhanced with information from our emergency response knowledge base.*"
                
            except Exception as e:
                response = f"⚠️ An error occurred while contacting the AI model: {str(e)}"
        
        # Update chat history
        st.session_state.chat_history.append(current_input + image_context)
        st.session_state.chat_history.append(response)
        
        # Add assistant response
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        st.rerun()


with col2:

    st.markdown("### 📄 PDF Sources")
    if vector_db:
        pdf_status = vector_db.get_pdf_status()
        if pdf_status['pdf_count'] > 0:
            st.success(f"✅ {pdf_status['pdf_count']} PDF files processed")
            with st.expander("PDF Sources"):
                for pdf in pdf_status['pdf_files']:
                    st.write(f"📄 {pdf}")
        else:
            st.warning("⚠️ No PDF files found")
            st.info("Add PDF files to `./data/pdfs/` folder and rebuild")
        # Knowledge Base Status
    st.markdown("### 📚 Knowledge Base Status")
    if vector_db and vector_db.index:
        st.success(f"✅ Loaded {vector_db.index.ntotal} emergency protocols")
        
        # Show database info
        db_info = vector_db.get_database_info()
        if db_info:
            with st.expander("Database Details"):
                st.write(f"**Created:** {db_info.get('created_at', 'Unknown')}")
                st.write(f"**Documents:** {db_info.get('num_documents', 'Unknown')}")
                st.write(f"**Model:** {db_info.get('model_name', 'Unknown')}")
                
                # Show source breakdown
                if 'source_breakdown' in db_info:
                    st.write("**Sources:**")
                    for source, count in db_info['source_breakdown'].items():
                        st.write(f"  - {source}: {count} chunks")
    else:
        st.error("❌ Knowledge base not loaded")
        if st.button("🔄 Initialize Knowledge Base"):
            st.cache_resource.clear()
            st.rerun()
    
    # Emergency Contacts
    st.markdown("### 📞 Emergency Contacts")
    st.markdown("""
    - **Emergency Services:** 911
    - **FEMA Helpline:** 1-800-621-FEMA
    - **Disaster Distress Helpline:** 1-800-985-5990
    - **Red Cross:** 1-800-RED-CROSS
    - **Poison Control:** 1-800-222-1222
    """)
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("Submit Assistance Request", use_container_width=True):
        switch_page("request")
    if st.button("Return to Dashboard", use_container_width=True):
        switch_page("dashboard")

        