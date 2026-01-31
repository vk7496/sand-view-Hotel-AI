import streamlit as st
from groq import Groq
from datetime import datetime
import pandas as pd
import os
import csv
import random
import string

# --- CONFIGURATION ---
st.set_page_config(page_title="Sand View Hotel | AI Infrastructure", layout="wide")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("AI Configuration Error. Please verify the API Key.")

# --- PERSISTENT DATABASE LOGIC ---
LIVE_DB = "orders_live.csv"
ARCHIVE_DB = "orders_archive.csv"

# Ensure DB files exist with headers
for db in [LIVE_DB, ARCHIVE_DB]:
    if not os.path.exists(db):
        pd.DataFrame(columns=["ID", "Date", "Time", "Room", "Guest", "Request"]).to_csv(db, index=False)

def generate_order_id():
    """Generates a unique tracking ID like SV-X123"""
    chars = string.ascii_uppercase + string.digits
    return "SV-" + ''.join(random.choice(chars) for _ in range(4))

def save_order_robust(order_dict, target_file):
    with open(target_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=order_dict.keys())
        writer.writerow(order_dict)

def load_data_safe(file):
    try:
        return pd.read_csv(file).to_dict('records')
    except:
        return []

# --- ADVANCED UI (Beach & Luxury Theme) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80");
        background-size: cover; background-attachment: fixed;
    }}
    section[data-testid="stSidebar"] {{
        background-color: rgba(28, 45, 102, 0.9) !important;
        backdrop-filter: blur(15px);
    }}
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(8px);
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }}
    .order-card-live {{
        background: rgba(255, 255, 255, 0.95);
        padding: 18px; border-radius: 12px;
        border-left: 8px solid #d4b996;
        color: #1c2d66; margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .id-badge {{
        background-color: #d4b996; color: white;
        padding: 2px 8px; border-radius: 5px; font-weight: bold;
    }}
    .footer-credit {{
        position: fixed; bottom: 10px; right: 20px;
        color: rgba(255,255,255,0.6); font-size: 0.8rem;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("logo.png") # Ensure logo.png is in your GitHub repo
    st.markdown("<h2 style='text-align:center; color:white;'>Sand View AI</h2>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Guest Experience", "Staff Dashboard", "Management Reports"])

# --- PAGE 1: GUEST EXPERIENCE ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.markdown("<h1 style='color:white; text-shadow:2px 2px 12px black; font-size:4rem;'>Sand View Hotel</h1>", unsafe_allow_html=True)
        col_log, _ = st.columns([1.5, 1])
        with col_log:
            u_name = st.text_input("Guest Name")
            u_room = st.text_input("Room #")
            if st.button("Start My Experience"):
                if u_name and u_room:
                    st.session_state.user_data = {"name": u_name, "room": u_room}
                    st.rerun()
    else:
        st.markdown(f"<h3 style='color:white;'>Welcome, {st.session_state.user_data['name']} (Room {st.session_state.user_data['room']})</h3>", unsafe_allow_html=True)
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("Tell me what you need..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            keywords = ['want', 'need', 'order', 'bring', 'taxi', 'water', 'towel', 'clean', 'food', 'breakfast', 'laundry']
            is_req = any(w in prompt.lower() for w in keywords)

            try:
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "You are Sand View AI. If it's a request, confirm it's being handled."},
                              {"role": "user", "content": prompt}]
                )
                ai_msg = res.choices[0].message.content
                
                if is_req:
                    order_id = generate_order_id()
                    ai_msg += f"\n\n**✅ Request Recorded. Tracking ID: {order_id}**"
                    
                    order_record = {
                        "ID": order_id,
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Time": datetime.now().strftime("%H:%M"),
                        "Room": st.session_state.user_data['room'],
                        "Guest": st.session_state.user_data['name'],
                        "Request": prompt
                    }
                    save_order_robust(order_record, LIVE_DB)
                    save_order_robust(order_record, ARCHIVE_DB)
                    st.toast(f"Order {order_id} Sent!", icon="🛎️")

                st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
                st.rerun()
            except: st.error("AI service error.")

# --- PAGE 2: STAFF DASHBOARD ---
elif page == "Staff Dashboard":
    st.markdown("<h1 style='color:white;'>🛎️ Live Service Panel</h1>", unsafe_allow_html=True)
    if st.text_input("Staff Password", type="password") == "staff123":
        orders = load_data_safe(LIVE_DB)
        if not orders:
            st.info("No pending tasks.")
        else:
            for i, o in enumerate(orders):
                st.markdown(f"""<div class="order-card-live">
                    <span class="id-badge">{o['ID']}</span> <strong>ROOM {o['Room']}</strong><br>
                    Guest: {o['Guest']}<br>
                    Request: {o['Request']}<br>
                    <small>Received: {o['Time']}</small>
                </div>""", unsafe_allow_html=True)
                if st.button("Resolve Task", key=f"res_{i}"):
                    temp_df = pd.read_csv(LIVE_DB)
                    temp_df = temp_df.drop(i)
                    temp_df.to_csv(LIVE_DB, index=False)
                    st.rerun()

# --- PAGE 3: MANAGEMENT REPORTS ---
elif page == "Management Reports":
    st.markdown("<h1 style='color:white;'>📊 Strategic Reporting</h1>", unsafe_allow_html=True)
    if st.text_input("Manager Password", type="password") == "admin789":
        arch = load_data_safe(ARCHIVE_DB)
        if arch:
            df = pd.DataFrame(arch)
            st.dataframe(df)
            st.download_button("Download Archive (CSV)", df.to_csv(index=False), "SandView_Archive.csv")
        else: st.info("No records found.")

st.markdown(f'<div class="footer-credit">AI Developer: Vista Kaviani | Vistakavianii@gmail.com</div>', unsafe_allow_html=True)
