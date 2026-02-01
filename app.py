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
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sand View Hotel | Smart Hub", layout="wide")
oman_tz = pytz.timezone('Asia/Muscat')

LIVE_DB = "orders_live.csv"
ARCHIVE_DB = "orders_archive.csv"
SETTINGS_FILE = "settings.json"

# --- 2. LOGIC ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f: return json.load(f)
    return {"staff_pwd": "staff123", "admin_pwd": "admin789"}

def save_settings(new_settings):
    with open(SETTINGS_FILE, "w") as f: json.dump(new_settings, f)

# اطمینان از وجود فایل‌ها با ساختار صحیح
def init_dbs():
    for db in [LIVE_DB, ARCHIVE_DB]:
        if not os.path.exists(db) or os.stat(db).st_size == 0:
            pd.DataFrame(columns=["ID", "Date", "Time", "Room", "Guest", "Request"]).to_csv(db, index=False)

init_dbs()

def generate_order_id():
    return "SV-" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

def save_order_robust(order_dict, target_file):
    with open(target_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Date", "Time", "Room", "Guest", "Request"])
        writer.writerow(order_dict)

# --- 3. UI STYLING ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80");
        background-size: cover; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{ background-color: rgba(28, 45, 102, 0.95) !important; backdrop-filter: blur(15px); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: white !important; text-shadow: 1px 1px 3px black; }}
    .order-card-live {{
        background: rgba(255, 255, 255, 0.98); padding: 20px; border-radius: 12px;
        border-left: 10px solid #d4b996; color: #1c2d66 !important; margin-bottom: 15px;
    }}
    .order-card-live * {{ color: #1c2d66 !important; text-shadow: none !important; }}
    .id-badge {{ background-color: #d4b996; color: white !important; padding: 3px 10px; border-radius: 6px; font-weight: bold; }}
    .sidebar-footer {{
        margin-top: 50px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);
        font-size: 0.85rem; color: rgba(255,255,255,0.7) !important; text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. INITIALIZATION ---
settings = load_settings()
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'last_order_count' not in st.session_state: st.session_state.last_order_count = 0

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("logo.png")
    st.markdown("<h2 style='text-align:center;'>Sand View AI</h2>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Guest Experience", "Digital Menu", "Staff Dashboard", "Management"])
    st.markdown(f'<div class="sidebar-footer">Prepared by:<br><b>Vista Kaviani</b><br>AI Solutions Developer<br>Vistakavianii@gmail.com</div>', unsafe_allow_html=True)

# --- 6. PAGE: GUEST EXPERIENCE ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.markdown("<h1 style='font-size:4rem;'>Sand View Hotel</h1>", unsafe_allow_html=True)
        u_name = st.text_input("Full Name")
        u_room = st.text_input("Room #")
        if st.button("Start My Stay"):
            if u_name and u_room:
                st.session_state.user_data = {"name": u_name, "room": u_room}
                st.balloons()
                st.rerun()
    else:
        st.markdown(f"<h3>Welcome, {st.session_state.user_data['name']} (Room {st.session_state.user_data['room']})</h3>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("How can we help?"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            is_req = any(w in prompt.lower() for w in ['want', 'need', 'order', 'bring', 'taxi', 'water', 'towel', 'clean', 'food'])
            
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "Concierge AI. Polite confirmation."}, {"role": "user", "content": prompt}]
                )
                ai_msg = res.choices[0].message.content
            except: ai_msg = "Request received! Staff notified."

            if is_req:
                order_id = generate_order_id()
                ai_msg += f"\n\n**✅ ID: {order_id}**"
                now_o = datetime.now(oman_tz)
                data = {"ID": order_id, "Date": now_o.strftime("%Y-%m-%d"), "Time": now_o.strftime("%H:%M"), "Room": st.session_state.user_data['room'], "Guest": st.session_state.user_data['name'], "Request": prompt}
                save_order_robust(data, LIVE_DB)
                save_order_robust(data, ARCHIVE_DB)
                st.toast("Sent to reception!")

            st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
            st.rerun()

# --- 7. PAGE: STAFF DASHBOARD (با قابلیت آپدیت خودکار) ---
elif page == "Staff Dashboard":
    st.markdown("<h1>🛎️ Live Reception Desk</h1>", unsafe_allow_html=True)
    if st.text_input("Staff Password", type="password") == settings["staff_pwd"]:
        
        # خواندن داده‌های تازه در هر بار اجرا
        df_live = pd.read_csv(LIVE_DB)
        
        # پخش صدا در صورت سفارش جدید
        if len(df_live) > st.session_state.last_order_count:
            st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)
            st.session_state.last_order_count = len(df_live)

        if df_live.empty:
            st.info("Waiting for requests... (Auto-refresh active)")
        else:
            for i, row in df_live.iterrows():
                with st.container():
                    st.markdown(f"""<div class="order-card-live"><span class="id-badge">{row['ID']}</span> <strong>Room {row['Room']}</strong><br>Guest: {row['Guest']}<br>Request: {row['Request']}<br><small>Oman Time: {row['Time']}</small></div>""", unsafe_allow_html=True)
                    if st.button(f"Mark Completed {row['ID']}", key=f"btn_{row['ID']}"):
                        # حذف از دیتابیس و آپدیت استیت
                        df_updated = pd.read_csv(LIVE_DB).drop(i)
                        df_updated.to_csv(LIVE_DB, index=False)
                        st.session_state.last_order_count = max(0, st.session_state.last_order_count - 1)
                        st.rerun()
        
        # جادوی رفرش خودکار: هر ۵ ثانیه صفحه را مجبور به بازخوانی می‌کند
        time.sleep(5)
        st.rerun()

# --- 8. OTHER PAGES ---
elif page == "Digital Menu":
    st.markdown("<h1>📖 Digital Menu</h1>", unsafe_allow_html=True)
    st.subheader("☕ Cafe: Omani Coffee, Latte | 🍽️ Food: Seafood, Sandwiches")

elif page == "Management Reports":
    st.markdown("<h1>📊 Management</h1>", unsafe_allow_html=True)
    if st.text_input("Admin Password", type="password") == settings["admin_pwd"]:
        st.dataframe(pd.read_csv(ARCHIVE_DB), use_container_width=True)
