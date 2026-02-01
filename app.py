import streamlit as st
from groq import Groq
from datetime import datetime
import pandas as pd
import os
import csv
import random
import string
import json

# --- 1. CONFIGURATION & DATABASE SETUP ---
st.set_page_config(page_title="Sand View Hotel | AI Hub", layout="wide")

LIVE_DB = "orders_live.csv"
ARCHIVE_DB = "orders_archive.csv"
SETTINGS_FILE = "settings.json"

# Function to load/save security settings
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f: return json.load(f)
        except: pass
    return {"staff_pwd": "staff123", "admin_pwd": "admin789"}

def save_settings(new_settings):
    with open(SETTINGS_FILE, "w") as f: json.dump(new_settings, f)

# Initialize CSV databases if missing
for db in [LIVE_DB, ARCHIVE_DB]:
    if not os.path.exists(db):
        pd.DataFrame(columns=["ID", "Date", "Time", "Room", "Guest", "Request"]).to_csv(db, index=False)

def generate_order_id():
    return "SV-" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

def save_order_robust(order_dict, target_file):
    with open(target_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=order_dict.keys())
        writer.writerow(order_dict)

# --- 2. LUXURY UI CUSTOMIZATION (CSS) ---
st.markdown("""
    <style>
    .stApp {
        background: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80");
        background-size: cover; background-attachment: fixed;
    }
    section[data-testid="stSidebar"] { background-color: rgba(28, 45, 102, 0.9) !important; backdrop-filter: blur(15px); }
    section[data-testid="stSidebar"] * { color: white !important; }
    .stChatMessage { background-color: rgba(255, 255, 255, 0.1) !important; backdrop-filter: blur(10px); border-radius: 15px; color: white !important; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .order-card-live { background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 12px; border-left: 8px solid #d4b996; color: #1c2d66; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .id-badge { background-color: #d4b996; color: white; padding: 3px 10px; border-radius: 6px; font-weight: bold; font-family: monospace; }
    .footer-credit { position: fixed; bottom: 15px; right: 25px; color: rgba(255,255,255,0.7); font-size: 0.85rem; text-shadow: 1px 1px 2px black; }
    .stButton>button { border-radius: 20px; background: linear-gradient(135deg, #d4b996, #a68b6a); border: none; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION & SIDEBAR ---
settings = load_settings()
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

with st.sidebar:
    st.image("logo.png") # Make sure logo.png is in your GitHub
    st.markdown("<h2 style='text-align:center;'>Sand View AI</h2>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Guest Experience", "Staff Dashboard", "Management Reports"])

# --- 4. GUEST EXPERIENCE ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.markdown("<h1 style='color:white; text-shadow:2px 2px 15px black; font-size:4.5rem; margin-top:50px;'>Sand View Hotel</h1>", unsafe_allow_html=True)
        col_log, _ = st.columns([1.6, 1])
        with col_log:
            u_name = st.text_input("Full Name", placeholder="Enter your name")
            u_room = st.text_input("Room Number", placeholder="e.g. 201")
            if st.button("Start My Stay"):
                if u_name and u_room:
                    st.session_state.user_data = {"name": u_name, "room": u_room}
                    st.rerun()
    else:
        st.markdown(f"<h3 style='color:white; text-shadow:1px 1px 5px black;'>Room {st.session_state.user_data['room']} | Welcome, {st.session_state.user_data['name']}</h3>", unsafe_allow_html=True)
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("How can we assist you today?"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            keywords = ['want', 'need', 'order', 'bring', 'taxi', 'water', 'towel', 'clean', 'food', 'breakfast', 'laundry', 'check-out']
            is_req = any(w in prompt.lower() for w in keywords)

            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "You are Sand View AI. Be polite and confirm requests."},
                              {"role": "user", "content": prompt}]
                )
                ai_msg = res.choices[0].message.content
            except:
                ai_msg = "Your request has been received and our team is on the way."

            if is_req:
                order_id = generate_order_id()
                ai_msg += f"\n\n**✅ Tracking ID: {order_id}**"
                record = {"ID": order_id, "Date": datetime.now().strftime("%Y-%m-%d"), "Time": datetime.now().strftime("%H:%M"), 
                          "Room": st.session_state.user_data['room'], "Guest": st.session_state.user_data['name'], "Request": prompt}
                save_order_robust(record, LIVE_DB)
                save_order_robust(record, ARCHIVE_DB)
                st.toast(f"Request {order_id} sent!", icon="🛎️")

            st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
            st.rerun()

# --- 5. STAFF DASHBOARD ---
elif page == "Staff Dashboard":
    st.markdown("<h1 style='color:white; text-shadow:2px 2px 10px black;'>🛎️ Staff Operations</h1>", unsafe_allow_html=True)
    if st.text_input("Staff Password", type="password") == settings["staff_pwd"]:
        try:
            orders = pd.read_csv(LIVE_DB).to_dict('records')
            if not orders: st.info("No active requests.")
            else:
                for i, o in enumerate(orders):
                    st.markdown(f"""<div class="order-card-live">
                        <span class="id-badge">{o['ID']}</span> <strong>ROOM {o['Room']}</strong><br>
                        <b>Guest:</b> {o['Guest']}<br><b>Request:</b> {o['Request']}<br>
                        <small>Time: {o['Time']}</small></div>""", unsafe_allow_html=True)
                    if st.button("Mark Resolved", key=f"res_{i}"):
                        df = pd.read_csv(LIVE_DB).drop(i)
                        df.to_csv(LIVE_DB, index=False)
                        st.rerun()
        except: st.warning("Database update in progress... please refresh.")
    elif st.button("Change Password"): st.info("Manager access required to change passwords.")

# --- 6. MANAGEMENT & SECURITY ---
elif page == "Management Reports":
    st.markdown("<h1 style='color:white; text-shadow:2px 2px 10px black;'>📊 Strategic Reports</h1>", unsafe_allow_html=True)
    if st.text_input("Manager Password", type="password") == settings["admin_pwd"]:
        t1, t2 = st.tabs(["📈 Data Archive", "🔐 Security"])
        with t1:
            try:
                df_arch = pd.read_csv(ARCHIVE_DB)
                st.dataframe(df_arch, use_container_width=True)
                st.download_button("Download Full History (CSV)", df_arch.to_csv(index=False), "SandView_History.csv")
            except: st.info("No data in archive yet.")
        with t2:
            st.subheader("System Security Settings")
            ns = st.text_input("New Staff Password", value=settings["staff_pwd"])
            na = st.text_input("New Manager Password", value=settings["admin_pwd"])
            if st.button("Update Passwords"):
                save_settings({"staff_pwd": ns, "admin_pwd": na})
                st.success("Security settings updated!")
                st.rerun()

st.markdown(f'<div class="footer-credit">AI Infrastructure by Vista Kaviani | Vistakavianii@gmail.com</div>', unsafe_allow_html=True)
