import streamlit as st
from groq import Groq
import pandas as pd
from datetime import datetime

# --- CONFIGURATION & SECRETS ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.set_page_config(page_title="Sand View Hotel | AI Smart Hub", layout="wide")

# --- CUSTOM CSS FOR SAND VIEW THEME ---
st.markdown("""
    <style>
    .main { background: #fdfcfb; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2C3E50, #000000); color: white; }
    .order-card { 
        padding: 15px; border-radius: 10px; border-left: 5px solid #D4B996;
        background: white; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .status-badge { background: #e8f5e9; color: #2e7d32; padding: 3px 8px; border-radius: 10px; font-size: 0.8em; }
    </style>
    """, unsafe_allow_view_to_html=True)

# --- DATABASE IN MEMORY ---
if 'order_db' not in st.session_state:
    st.session_state.order_db = []

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🏝️ Sand View")
    st.markdown("---")
    page = st.radio("Switch View:", ["Guest Experience", "Management Hub"])
    st.markdown("---")
    st.write("Logged in as: **Vista Kaviani**")

# --- PAGE 1: GUEST EXPERIENCE ---
if page == "Guest Experience":
    st.title("Concierge AI 🛎️")
    st.write("Welcome to Sand View Hotel. How can I assist you today?")

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("I'd like to order a Club Sandwich..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI Analysis using Groq
        with st.chat_message("assistant"):
            try:
                # Prompt Engineering: Asking AI to identify if it's an order
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": "You are the AI Concierge of Sand View Hotel. If a guest wants to order food or service, start your reply with '[ORDER]'. Be luxury and polite."},
                        {"role": "user", "content": prompt}
                    ]
                )
                full_response = response.choices[0].message.content
                st.markdown(full_response)
                
                # Logic: If AI identifies an order, save to Dashboard
                if "[ORDER]" in full_response:
                    new_order = {
                        "Room": "Room 304", # Hardcoded for Demo
                        "Request": prompt,
                        "Time": datetime.now().strftime("%H:%M"),
                        "Status": "Verified by AI"
                    }
                    st.session_state.order_db.append(new_order)
                    st.toast("Order sent to Kitchen Hub!", icon="✅")

                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error("Connection Error. Please check API Key in Secrets.")

# --- PAGE 2: MANAGEMENT HUB ---
elif page == "Management Hub":
    st.title("📊 Operational Dashboard")
    st.write("Incoming guest requests filtered by AI (WhatsApp bypassed).")

    if not st.session_state.order_db:
        st.info("No active orders at the moment.")
    else:
        col1, col2 = st.columns(2)
        for i, order in enumerate(st.session_state.order_db):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"""
                    <div class="order-card">
                        <div style="display:flex; justify-content:space-between">
                            <strong>{order['Room']}</strong>
                            <span class="status-badge">{order['Status']}</span>
                        </div>
                        <p style="margin:10px 0;">{order['Request']}</p>
                        <small style="color:gray;">Received at: {order['Time']}</small>
                    </div>
                """, unsafe_allow_view_to_html=True)
                if st.button("Complete Task", key=f"done_{i}"):
                    st.session_state.order_db.pop(i)
                    st.rerun()

    # Insight Section for Management
    st.markdown("---")
    st.subheader("Guest Intent Analysis")
    st.write("AI identifies these as your top guest needs today: **Room Service, Late Check-out.**")
