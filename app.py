import streamlit as st
import requests
from datetime import datetime

# Base URL of your FastAPI backend
API_BASE_URL = "http://localhost:8000"

# App config
st.set_page_config(
    page_title="PromoSensei - Puma Deals Assistant",
    layout="centered",
    page_icon="🧠"
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar options
with st.sidebar:
    st.header("⚙️ Options")
    summary_mode = st.checkbox("Summary Mode", value=False)
    
    if st.button("🔄 Refresh Product Data"):
        with st.spinner("Refreshing data (this may take a few minutes)..."):
            try:
                response = requests.post(f"{API_BASE_URL}/refresh")
                if response.status_code == 200:
                    st.success("✅ Product data refreshed successfully!")
                    st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    st.error(f"❌ Failed to refresh data: {response.json().get('message', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
    
    if "last_refresh" in st.session_state:
        st.caption(f"Last refreshed: {st.session_state.last_refresh}")
st.title("🧠 PromoSensei")
st.markdown("Your intelligent Puma deals assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about Puma deals..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Searching for the best deals..."):
            try:
                payload = {
                    "query": prompt,
                    "command_type": "summary" if summary_mode else "search"
                }
                response = requests.post(f"{API_BASE_URL}/query", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "success":
                        result = data["data"]["Response"]
                        
                        # Check if the response contains a Markdown table
                        if "|" in result and "-" in result:
                            # For better table rendering
                            st.markdown(result, unsafe_allow_html=True)
                        else:
                            st.markdown(result)
                            
                        st.session_state.messages.append({"role": "assistant", "content": result})
                    else:
                        error_msg = "Failed to get response from AI"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                else:
                    error_msg = f"API request failed: {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Connection error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})