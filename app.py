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
import base64

# --- 1. CONFIGURATION & TIMEZONE ---
st.set_page_config(page_title="Sand View Hotel | Reception Hub", layout="wide")
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

# --- 3. NOTIFICATION SOUND (HTML/JS) ---
def play_notification():
    # یک صدای کوتاه برای اطلاع‌رسانی سفارش جدید
    audio_url = "https://www.soundjay.com/buttons/beep-07a.mp3"
    st.markdown(f"""
        <audio autoplay>
            <source src="{audio_url}" type="audio/mpeg">
        </audio>
    """, unsafe_allow_html=True)

# --- 4. LUXURY UI & WHITE TEXT STYLING ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80");
        background-size: cover; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{ background-color: rgba(28, 45, 102, 0.95) !important; backdrop-filter: blur(15px); }}
    
    /* سفید کردن نوشته‌ها در داشبورد */
    h1, h2, h3, p, span, label {{ color: white !important; text-shadow: 1px 1px 3px black; }}
    
    .order-card-live {{
        background: rgba(255, 255, 255, 0.98); padding: 20px; border-radius: 12px;
        border-left: 10px solid #d4b996; color: #1c2d66 !important; margin-bottom: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }}
    .order-card-live * {{ color: #1c2d66 !important; text-shadow: none !important; }}
    
    .id-badge {{ background-color: #d4b996; color: white !important; padding: 3px 10px; border-radius: 6px; font-weight: bold; }}
    
    .footer-signature {{
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        text-align: center; color: white !important; font-size: 1rem;
        font-weight: bold; text-shadow: 2px 2px 5px black; z-index: 1000;
        background: rgba(0,0,0,0.3); padding: 5px 20px; border-radius: 30px;
    }}
    
    .menu-item {{ background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin-bottom: 5px; border: 1px solid rgba(255,255,255,0.2); }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. INITIALIZATION ---
settings = load_settings()
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'last_order_count' not in st.session_state: st.session_state.last_order_count = 0

with st.sidebar:
    st.image("logo.png")
    st.markdown("<h2 style='text-align:center;'>Sand View AI</h2>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Guest Experience", "Digital Menu", "Staff Dashboard", "Management"])

# --- 6. PAGE: GUEST EXPERIENCE ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.markdown("<h1 style='font-size:4rem;'>Sand View Hotel</h1>", unsafe_allow_html=True)
        col1, _ = st.columns([1.5, 1])
        with col1:
            u_name = st.text_input("Full Name")
            u_room = st.text_input("Room #")
            if st.button("Start My Stay"):
                if u_name and u_room:
                    st.session_state.user_data = {"name": u_name, "room": u_room}
                    st.balloons()
                    st.rerun()
    else:
        st.markdown(f"<h3>Welcome, {st.session_state.user_data['name']}</h3>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("How can we help?"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            is_req = any(w in prompt.lower() for w in ['want', 'need', 'order', 'bring', 'taxi', 'water', 'food', 'coffee', 'juice'])
            
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "You are a hotel concierge. Confirm requests."}, {"role": "user", "content": prompt}]
                )
                ai_msg = res.choices[0].message.content
            except: ai_msg = "Request received! Staff notified."

            if is_req:
                order_id = generate_order_id()
                ai_msg += f"\n\n**✅ ID: {order_id}**"
                now_o = datetime.now(oman_tz)
                save_order_robust({"ID": order_id, "Date": now_o.strftime("%Y-%m-%d"), "Time": now_o.strftime("%H:%M"), "Room": st.session_state.user_data['room'], "Guest": st.session_state.user_data['name'], "Request": prompt}, LIVE_DB)
                save_order_robust({"ID": order_id, "Date": now_o.strftime("%Y-%m-%d"), "Time": now_o.strftime("%H:%M"), "Room": st.session_state.user_data['room'], "Guest": st.session_state.user_data['name'], "Request": prompt}, ARCHIVE_DB)
                st.toast("Order sent to reception!")

            st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
            st.rerun()

# --- 7. PAGE: DIGITAL MENU ---
elif page == "Digital Menu":
    st.markdown("<h1>📖 Digital Menu</h1>", unsafe_allow_html=True)
    col_c, col_r = st.columns(2)
    with col_c:
        st.subheader("☕ Cafe")
        st.markdown('<div class="menu-item">Omani Coffee - 1.500 OMR</div>', unsafe_allow_html=True)
        st.markdown('<div class="menu-item">Fresh Apple Juice - 2.000 OMR</div>', unsafe_allow_html=True)
        st.markdown('<div class="menu-item">Cappuccino - 1.800 OMR</div>', unsafe_allow_html=True)
    with col_r:
        st.subheader("🍽️ Restaurant")
        st.markdown('<div class="menu-item">Grilled Seafood - 8.500 OMR</div>', unsafe_allow_html=True)
        st.markdown('<div class="menu-item">Club Sandwich - 3.500 OMR</div>', unsafe_allow_html=True)
        st.markdown('<div class="menu-item">Mezze Platter - 4.000 OMR</div>', unsafe_allow_html=True)

# --- 8. PAGE: STAFF DASHBOARD (RECEPTION) ---
elif page == "Staff Dashboard":
    st.markdown("<h1>🛎️ Live Reception Desk</h1>", unsafe_allow_html=True)
    if st.text_input("Staff Password", type="password") == settings["staff_pwd"]:
        if os.path.exists(LIVE_DB):
            df_live = pd.read_csv(LIVE_DB)
            
            # چک کردن برای سفارش جدید و پخش صدا
            if len(df_live) > st.session_state.last_order_count:
                play_notification()
                st.session_state.last_order_count = len(df_live)
            
            if df_live.empty: st.info("No active requests.")
            else:
                for i, row in df_live.iterrows():
                    st.markdown(f"""<div class="order-card-live"><span class="id-badge">{row['ID']}</span> <strong>Room {row['Room']}</strong><br>Guest: {row['Guest']}<br>Request: {row['Request']}<br><small>Oman Time: {row['Time']}</small></div>""", unsafe_allow_html=True)
                    if st.button(f"Mark Completed {row['ID']}", key=f"rec_{row['ID']}"):
                        pd.read_csv(LIVE_DB).drop(i).to_csv(LIVE_DB, index=False)
                        st.session_state.last_order_count -= 1
                        st.rerun()
        
        # رفرش خودکار هر ۳۰ ثانیه برای چک کردن سفارشات جدید
        # st.empty() # Placeholder for future auto-refresh logic if needed

# --- 9. PAGE: MANAGEMENT ---
elif page == "Management Reports":
    st.markdown("<h1>📊 Management</h1>", unsafe_allow_html=True)
    if st.text_input("Admin Password", type="password") == settings["admin_pwd"]:
        tab1, tab2 = st.tabs(["History", "Security"])
        with tab1:
            st.dataframe(pd.read_csv(ARCHIVE_DB), use_container_width=True)
        with tab2:
            ns = st.text_input("New Staff PWD", value=settings["staff_pwd"])
            na = st.text_input("New Admin PWD", value=settings["admin_pwd"])
            if st.button("Save Settings"):
                save_settings({"staff_pwd": ns, "admin_pwd": na})
                st.success("Updated!")

# --- FOOTER SIGNATURE ---
st.markdown('<div class="footer-signature">Prepared by vista kaviani _AI solutions developer<br>Vistakavianii@gmail.com</div>', unsafe_allow_html=True)
