# app.py

import streamlit as st
from utils import get_response

# Initialize session state for Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello and welcome! 🎉 You're in the right place to explore the Stock market. Just ask your question and let’s dive into the details!"}
    ]

# Chat input field at the top
user_input = st.chat_input("𝐀𝐬𝐤 𝐚𝐧𝐲𝐭𝐡𝐢𝐧𝐠 𝐚𝐛𝐨𝐮𝐭 𝐬𝐭𝐨𝐜𝐤 𝐦𝐚𝐫𝐤𝐞𝐭....!💹")

# Streamlit title
st.header("𝐀𝐈 𝐓𝐫𝐚𝐝𝐞𝐀𝐬𝐬𝐢𝐬𝐭🔎")

# Process user input
if user_input:
    # Add the user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get RAG + Groq response
    response = get_response(user_input)
    
    # Add the assistant response to the chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Display the full chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
