import streamlit as st
from groq import Groq
import pandas as pd
from datetime import datetime

# --- CONFIGURATION & SECRETS ---
# استفاده از try-except برای جلوگیری از کرش در صورت نبود کلید
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("❌ API Key not found in Secrets. Please check Streamlit settings.")

st.set_page_config(page_title="Sand View Hotel | AI Smart Hub", layout="wide")

# --- CSS پایدار ---
st.markdown("""
    <style>
    .stApp { background: #fdfcfb; }
    .order-card { 
        padding: 15px; border-radius: 10px; border-left: 5px solid #D4B996;
        background: white; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        color: #2C3E50;
    }
    .status-badge { background: #e8f5e9; color: #2e7d32; padding: 3px 8px; border-radius: 10px; font-size: 0.8em; }
    </style>
    """, unsafe_allow_html=True)

if 'order_db' not in st.session_state:
    st.session_state.order_db = []

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏝️ Sand View")
    page = st.radio("Switch View:", ["Guest Experience", "Management Hub"])

# --- PAGE 1: GUEST EXPERIENCE ---
if page == "Guest Experience":
    st.title("Concierge AI 🛎️")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("How can I help you?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # استفاده از مدل پایدار 3.1
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are the AI Concierge of Sand View Hotel. If the guest wants to order food or a service, strictly start your reply with '[ORDER]'. Be luxury and polite."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                full_response = response.choices[0].message.content
                st.markdown(full_response)
                
                if "[ORDER]" in full_response:
                    st.session_state.order_db.append({
                        "Room": "Room 304", 
                        "Request": prompt,
                        "Time": datetime.now().strftime("%H:%M"),
                        "Status": "Verified by AI"
                    })
                    st.toast("Order sent to Kitchen Hub!", icon="✅")

                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"AI Error: {str(e)}")
                st.info("Check if your Groq API Key has reached its limit or is incorrect.")

# --- PAGE 2: MANAGEMENT HUB ---
elif page == "Management Hub":
    st.title("📊 Operational Dashboard")
    if not st.session_state.order_db:
        st.info("No active orders.")
    else:
        for i, order in enumerate(st.session_state.order_db):
            st.markdown(f"""
                <div class="order-card">
                    <strong>{order['Room']}</strong> | <span class="status-badge">{order['Status']}</span><br>
                    {order['Request']}<br>
                    <small>{order['Time']}</small>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Mark Complete", key=f"done_{i}"):
                st.session_state.order_db.pop(i)
                st.rerun()
