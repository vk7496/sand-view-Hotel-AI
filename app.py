import streamlit as st
from groq import Groq
from datetime import datetime
import pandas as pd
import os
import csv
import random
import string
import json
import pytz

# --- 1. CONFIGURATION & TIMEZONE ---
st.set_page_config(page_title="Sand View Hotel | AI Hub", layout="wide")
oman_tz = pytz.timezone('Asia/Muscat')

LIVE_DB = "orders_live.csv"
ARCHIVE_DB = "orders_archive.csv"
SETTINGS_FILE = "settings.json"

# --- 2. SECURITY & DATA LOGIC ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f: return json.load(f)
    return {"staff_pwd": "staff123", "admin_pwd": "admin789"}

def save_settings(new_settings):
    with open(SETTINGS_FILE, "w") as f: json.dump(new_settings, f)

for db in [LIVE_DB, ARCHIVE_DB]:
    if not os.path.exists(db) or os.stat(db).st_size == 0:
        pd.DataFrame(columns=["ID", "Date", "Time", "Room", "Guest", "Request"]).to_csv(db, index=False)

def generate_order_id():
    return "SV-" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

def save_order_robust(order_dict, target_file):
    with open(target_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Date", "Time", "Room", "Guest", "Request"])
        writer.writerow(order_dict)

# --- 3. UI/UX STYLING (Responsive & Glassmorphism) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80");
        background-size: cover; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{ background-color: rgba(28, 45, 102, 0.95) !important; backdrop-filter: blur(15px); }}
    .order-card-live {{
        background: rgba(255, 255, 255, 0.98); padding: 20px; border-radius: 12px;
        border-left: 10px solid #d4b996; color: #1c2d66; margin-bottom: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }}
    .id-badge {{ background-color: #d4b996; color: white; padding: 3px 10px; border-radius: 6px; font-weight: bold; }}
    .footer-custom {{
        position: fixed; bottom: 15px; right: 25px; color: white;
        font-size: 0.9rem; text-shadow: 2px 2px 4px black; z-index: 999;
    }}
    @media (max-width: 640px) {{
        .footer-custom {{ position: relative; text-align: center; right: 0; color: #eee; margin-top: 30px; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. INITIALIZATION ---
settings = load_settings()
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

with st.sidebar:
    st.image("logo.png")
    st.markdown("<h2 style='text-align:center; color:white;'>Sand View AI</h2>", unsafe_allow_html=True)
    page = st.radio("Menu", ["Guest Experience", "Staff Dashboard", "Management Reports"])

# --- 5. PAGE 1: GUEST EXPERIENCE ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.markdown("<h1 style='color:white; text-shadow:2px 2px 15px black; font-size:4rem;'>Welcome to Sand View</h1>", unsafe_allow_html=True)
        col_log, _ = st.columns([1.5, 1])
        with col_log:
            u_name = st.text_input("Full Name")
            u_room = st.text_input("Room #")
            if st.button("Start AI Experience"):
                if u_name and u_room:
                    st.session_state.user_data = {"name": u_name, "room": u_room}
                    st.balloons()
                    st.success(f"Welcome {u_name}! We are delighted to have you in room {u_room}. Our AI concierge is ready to assist you.")
                    st.rerun()
    else:
        st.markdown(f"<h3 style='color:white;'>Enjoy your stay, {st.session_state.user_data['name']}</h3>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("Ask for water, a taxi, or room service..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            is_req = any(w in prompt.lower() for w in ['want', 'need', 'order', 'bring', 'taxi', 'water', 'towel', 'clean', 'food', 'breakfast'])

            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "Hotel AI. Be polite and confirm services."}, {"role": "user", "content": prompt}]
                )
                ai_msg = res.choices[0].message.content
            except: ai_msg = "Your request has been received and the staff is notified."

            if is_req:
                order_id = generate_order_id()
                ai_msg += f"\n\n**✅ ID: {order_id} (Staff Notified)**"
                now_oman = datetime.now(oman_tz)
                record = {"ID": order_id, "Date": now_oman.strftime("%Y-%m-%d"), "Time": now_oman.strftime("%H:%M"), "Room": st.session_state.user_data['room'], "Guest": st.session_state.user_data['name'], "Request": prompt}
                save_order_robust(record, LIVE_DB)
                save_order_robust(record, ARCHIVE_DB)
                st.toast(f"Request {order_id} Registered!", icon="🛎️")

            st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
            st.rerun()

# --- 6. PAGE 2: STAFF DASHBOARD ---
elif page == "Staff Dashboard":
    st.markdown("<h1 style='color:white;'>🛎️ Live Orders</h1>", unsafe_allow_html=True)
    if st.text_input("Staff Password", type="password") == settings["staff_pwd"]:
        if os.path.exists(LIVE_DB):
            df_live = pd.read_csv(LIVE_DB)
            if df_live.empty: st.info("No active requests.")
            else:
                for i, row in df_live.iterrows():
                    st.markdown(f"""<div class="order-card-live"><span class="id-badge">{row['ID']}</span> <strong>Room {row['Room']}</strong><br>Guest: {row['Guest']}<br>Request: {row['Request']}<br><small>Time: {row['Time']} (Oman)</small></div>""", unsafe_allow_html=True)
                    if st.button(f"Mark Completed {row['ID']}", key=f"btn_{row['ID']}"):
                        pd.read_csv(LIVE_DB).drop(i).to_csv(LIVE_DB, index=False)
                        st.rerun()
    elif st.button("Change Password"): st.info("Only Manager can update passwords.")

# --- 7. PAGE 3: MANAGEMENT ---
elif page == "Management Reports":
    st.markdown("<h1 style='color:white;'>📊 Management Hub</h1>", unsafe_allow_html=True)
    if st.text_input("Manager Password", type="password") == settings["admin_pwd"]:
        t1, t2 = st.tabs(["Performance History", "Security Panel"])
        with t1:
            if os.path.exists(ARCHIVE_DB):
                df_arch = pd.read_csv(ARCHIVE_DB)
                st.dataframe(df_arch, use_container_width=True)
                st.download_button("Download Full History", df_arch.to_csv(index=False), "SandView_Report.csv")
        with t2:
            st.subheader("System Access Control")
            new_s = st.text_input("Staff Password", value=settings["staff_pwd"])
            new_a = st.text_input("Manager Password", value=settings["admin_pwd"])
            if st.button("Update Passwords"):
                save_settings({"staff_pwd": new_s, "admin_pwd": new_a})
                st.success("Passwords updated successfully!")

# --- FOOTER ---
st.markdown('<div class="footer-custom">Prepared by vista kaviani _AI solutions developer</div>', unsafe_allow_html=True)
