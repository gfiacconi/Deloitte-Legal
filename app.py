 # Importing required packages
import streamlit as st
import openai
import uuid
import time
import pandas as pd
import io
from openai import OpenAI
import base64
from email.message import EmailMessage
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt


assistant_id = st.secrets["assistant_id"]  
api_key = st.secrets["api_key"]


def set_background(svg_file):
    def get_base64(file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()

    bin_str = get_base64(svg_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/svg+xml;base64,%s");
        background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)


client = OpenAI(api_key=api_key)

# Your chosen model
MODEL = "gpt-4-1106-preview"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state:
    st.session_state.run = {"status": None}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0

# Set up the page
st.set_page_config(page_title="Real Estate Deloitte - Luiss", page_icon=":house:", layout="wide")
set_background('./assett/sfondo3.svg')

# Logo e layout a tre colonne
col1, col2 = st.columns([1, 1])

with col1:
    
    st.markdown(
        """
        <style>
        .stChatInput {
            position: fixed;
            bottom: 20px; /* Staccata dal fondo */
            left: 50%; /* Centrare orizzontalmente */
            transform: translateX(-50%); /* Centrare con precisione */
            width: 60%; /* Ridurre la larghezza */
            z-index: 1000;
            background-color: white;
            padding: 8px 12px; /* Ridurre padding */
            border-radius: 8px; /* Angoli arrotondati */
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); /* Aggiungere un'ombra leggera */
            border: 1px solid #ccc; /* Bordo sottile e chiaro */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # File uploader for CSV, XLS, XLSX
    st.image('./assett/logo4.svg', width=330)

    # Initialize OpenAI assistant
    if "assistant" not in st.session_state:
        openai.api_key = api_key
        st.session_state.assistant = openai.beta.assistants.retrieve(assistant_id)
        st.session_state.thread = client.beta.threads.create(
            metadata={'session_id': st.session_state.session_id}
        )

    # Display chat messages
    elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":
        st.session_state.messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread.id
        )
        for message in reversed(st.session_state.messages.data):
            if message.role in ["user", "assistant"]:
                with st.chat_message(message.role):
                    for content_part in message.content:
                        message_text = content_part.text.value
                        st.markdown(message_text)

    # Chat input and message creation with file ID
    if prompt := st.chat_input("How can I help you?"):
        with st.chat_message('user'):
            st.write(prompt)

        message_data = {
            "thread_id": st.session_state.thread.id,
            "role": "user",
            "content": prompt
        }

        # Include file ID in the request if available
        if "file_id" in st.session_state:
            message_data["file_ids"] = [st.session_state.file_id]

        st.session_state.messages = client.beta.threads.messages.create(**message_data)

        st.session_state.run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread.id,
            assistant_id=st.session_state.assistant.id,
        )
        if st.session_state.retry_error < 3:
            time.sleep(1)
            st.rerun()

    # Handle run status
    if hasattr(st.session_state.run, 'status'):
        if st.session_state.run.status == "running":
            with st.chat_message('assistant'):
                st.write("Thinking ......")
            if st.session_state.retry_error < 3:
                time.sleep(1)
                st.rerun()

        elif st.session_state.run.status == "failed":
            st.session_state.retry_error += 1
            with st.chat_message('assistant'):
                if st.session_state.retry_error < 3:
                    st.write("Run failed, retrying ......")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("FAILED: The OpenAI API is currently processing too many requests. Please try again later ......")

        elif st.session_state.run.status != "completed":
            st.session_state.run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread.id,
                run_id=st.session_state.run.id,
            )
            if st.session_state.retry_error < 3:
                time.sleep(3)
                st.rerun()

with col2:
        st.header("Score Counter")
        # Imposta lo stato iniziale
        if 'data' not in st.session_state:
            st.session_state.data = {'Acquirente': 0, 'Venditore': 0}

        # Funzioni per aggiornare i valori
        def increase(role):
            st.session_state.data[role] += 1

        def decrease(role):
            st.session_state.data[role] -= 1

        # Prepara i dati per il grafico
        df = pd.DataFrame({
            "Ruolo": list(st.session_state.data.keys()),
            "Valore": list(st.session_state.data.values()),
            "Colore": ["#003169", "#83bf20"]  # Blu per Acquirente, Verde per Venditore
        })

        # Crea il grafico con Altair
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Ruolo", title="Ruolo"),
            y=alt.Y("Valore", title="Valore"),
            color=alt.Color("Ruolo", scale=alt.Scale(domain=["Acquirente", "Venditore"], range=["#003169", "#83bf20"])),
        ).properties(
            width=600,
            height=250
        )

        st.altair_chart(chart, use_container_width=True)

        # Logo e layout a tre colonne
        col1, col2, col3 = st.columns([1, 1, 1])
        # Pulsanti per interagire con i valori
        with col1:
            st.write("Acquirente")
            st.write("Venditore")
        
        with col2:
            st.button("➕​", key="inc_acquirente", on_click=increase, args=("Acquirente",))
            st.button("➕​", key="inc_venditore", on_click=increase, args=("Venditore",))
        
        with col3:
            st.button("​➖​", key="dec_acquirente", on_click=decrease, args=("Acquirente",))
            st.button("​➖​", key="dec_venditore", on_click=decrease, args=("Venditore",))
                    