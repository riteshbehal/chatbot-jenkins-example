"""Streamlit frontend for the Bedrock chatbot."""

import os

import streamlit as st

import chatbot_backend as demo


st.set_page_config(
    page_title="Chatbot BOB",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 Hi! This is Chatbot BOB")
st.caption("A Streamlit chatbot powered by AWS Bedrock, LangChain, and conversation memory.")

with st.sidebar:
    st.header("Chatbot Settings")
    st.write(f"**Model:** `{os.getenv('BEDROCK_MODEL_ID', demo.DEFAULT_MODEL_ID)}`")
    st.write(f"**AWS Region:** `{os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION', demo.DEFAULT_AWS_REGION)}`")

    if st.button("Clear chat", use_container_width=True):
        st.session_state.pop("memory", None)
        st.session_state.pop("chat_history", None)
        st.rerun()


if "memory" not in st.session_state:
    st.session_state.memory = demo.get_memory()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])


user_input = st.chat_input("Ask me anything...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.chat_history.append({
        "role": "user",
        "text": user_input,
    })

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = demo.generate_response(
                    input_text=user_input,
                    memory=st.session_state.memory,
                )
            st.markdown(response)

        st.session_state.chat_history.append({
            "role": "assistant",
            "text": response,
        })
    except Exception as exc:
        st.error(
            "The chatbot could not generate a response. Check AWS credentials, "
            "Bedrock model access, region, and Jenkins/Docker environment variables."
        )
        st.exception(exc)
