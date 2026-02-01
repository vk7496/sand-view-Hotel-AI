import streamlit as st
from groq import Groq
from datetime import datetime, timedelta
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

# --- 2. CORE LOGIC ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f: return json.load(f)
    return {"staff_pwd": "staff123", "admin_pwd": "admin789"}

def save_settings(new_settings):
    with open(SETTINGS_FILE, "w") as f: json.dump(new_settings, f)

def init_dbs():
    for db in [LIVE_DB, ARCHIVE_DB]:
        if not os.path.exists(db) or os.stat(db).st_size == 0:
            pd.DataFrame(columns=["ID", "Date", "Time", "Room", "Guest", "Request"]).to_csv(db, index=False)

init_dbs()

def generate_order_id():
    return "SV-" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

def save_order(order_dict, target_file):
    with open(target_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Date", "Time", "Room", "Guest", "Request"])
        writer.writerow(order_dict)

# --- 3. UI/UX STYLING ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80");
        background-size: cover; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{ background-color: rgba(28, 45, 102, 0.95) !important; backdrop-filter: blur(15px); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: white !important; text-shadow: 1px 1px 4px black; }}
    .order-card-live {{
        background: rgba(255, 255, 255, 0.98); padding: 20px; border-radius: 12px;
        border-left: 10px solid #d4b996; color: #1c2d66 !important; margin-bottom: 15px;
    }}
    .order-card-live * {{ color: #1c2d66 !important; text-shadow: none !important; }}
    .id-badge {{ background-color: #d4b996; color: white !important; padding: 3px 10px; border-radius: 6px; font-weight: bold; }}
    .sidebar-footer {{
        margin-top: 30px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);
        font-size: 0.85rem; color: rgba(255,255,255,0.7) !important; text-align: center;
    }}
    .menu-box {{ background: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px; border: 1px solid #d4b996; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. INITIALIZATION ---
settings = load_settings()
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'last_order_count' not in st.session_state: st.session_state.last_order_count = 0

with st.sidebar:
    st.image("logo.png")
    st.markdown("<h2 style='text-align:center;'>Sand View AI</h2>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Guest Experience", "Digital Menu", "Staff Dashboard", "Management Reports"])
    st.markdown(f'<div class="sidebar-footer">Prepared by:<br><b>Vista Kaviani</b><br>AI Solutions Developer<br>Vistakavianii@gmail.com</div>', unsafe_allow_html=True)

# --- 5. PAGE: GUEST EXPERIENCE (Multi-Language Support) ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.markdown("<h1 style='font-size:3.5rem;'>Sand View Hotel</h1>", unsafe_allow_html=True)
        u_name = st.text_input("Full Name / الاسم الكامل")
        u_room = st.text_input("Room Number / رقم الغرفة")
        if st.button("Enter / دخول"):
            if u_name and u_room:
                st.session_state.user_data = {"name": u_name, "room": u_room}
                st.balloons()
                st.rerun()
    else:
        st.markdown(f"<h3>Welcome, {st.session_state.user_data['name']} (Room {st.session_state.user_data['room']})</h3>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("How can I help you? / كيف يمكنني مساعدتك؟"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # هوش مصنوعی برای تشخیص هر نوع زبان (فارسی، عربی، انگلیسی)
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # سیستم را مجبور می‌کنیم تشخیص دهد آیا این یک درخواست سرویس است یا خیر
                check_res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "Analyze the user input. If it is a request for any hotel service, food, water, cleaning, or taxi in ANY language (Persian, Arabic, English), reply with only the word 'ORDER'. Otherwise reply 'CHAT'."}, 
                              {"role": "user", "content": prompt}]
                )
                intent = check_res.choices[0].message.content.strip()

                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "You are a friendly hotel concierge. Respond in the SAME language as the guest."}, 
                              {"role": "user", "content": prompt}]
                )
                ai_msg = res.choices[0].message.content
            except:
                intent = "ORDER" # در صورت خطا، جانب احتیاط را رعایت می‌کنیم
                ai_msg = "Request received! Staff notified."

            if "ORDER" in intent.upper():
                order_id = generate_order_id()
                ai_msg += f"\n\n✅ **ID: {order_id}**"
                now_o = datetime.now(oman_tz)
                data = {"ID": order_id, "Date": now_o.strftime("%Y-%m-%d"), "Time": now_o.strftime("%H:%M"), "Room": st.session_state.user_data['room'], "Guest": st.session_state.user_data['name'], "Request": prompt}
                save_order(data, LIVE_DB)
                save_order(data, ARCHIVE_DB)
                st.toast(f"Request {order_id} sent!")

            st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
            st.rerun()

# --- 6. PAGE: DIGITAL MENU ---
elif page == "Digital Menu":
    st.markdown("<h1>📖 Digital Menu / القائمة الرقمية</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class="menu-box"><h3>☕ Cafe & Bar</h3>
        - Omani Coffee Special: 1.500 OMR<br>
        - Fresh Mango Juice: 2.200 OMR<br>
        - Karak Tea: 0.800 OMR<br>
        - Espresso: 1.200 OMR</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="menu-box"><h3>🍽️ Restaurant</h3>
        - Grilled Kingfish: 7.500 OMR<br>
        - Chicken Kabuli: 5.500 OMR<br>
        - Arabic Mezze Platter: 4.000 OMR<br>
        - Club Sandwich: 3.500 OMR</div>""", unsafe_allow_html=True)

# --- 7. PAGE: STAFF DASHBOARD ---
elif page == "Staff Dashboard":
    st.markdown("<h1>🛎️ Staff Hub</h1>", unsafe_allow_html=True)
    pwd_input = st.text_input("Staff Password", type="password")
    if pwd_input == settings["staff_pwd"]:
        df_live = pd.read_csv(LIVE_DB)
        if len(df_live) > st.session_state.last_order_count:
            st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)
            st.session_state.last_order_count = len(df_live)

        if df_live.empty: st.info("No active orders.")
        else:
            for i, row in df_live.iterrows():
                st.markdown(f"""<div class="order-card-live"><span class="id-badge">{row['ID']}</span> <b>Room {row['Room']}</b> | {row['Guest']}<br>Request: {row['Request']}<br><small>{row['Time']} (Oman)</small></div>""", unsafe_allow_html=True)
                if st.button(f"Mark Done {row['ID']}", key=f"s_{row['ID']}"):
                    pd.read_csv(LIVE_DB).drop(i).to_csv(LIVE_DB, index=False)
                    st.session_state.last_order_count = max(0, st.session_state.last_order_count - 1)
                    st.rerun()
        time.sleep(5)
        st.rerun()

# --- 8. PAGE: MANAGEMENT & ARCHIVE ---
elif page == "Management Reports":
    st.markdown("<h1>📊 Management Panel</h1>", unsafe_allow_html=True)
    if st.text_input("Manager Password", type="password") == settings["admin_pwd"]:
        t1, t2 = st.tabs(["Reports & Downloads", "Security Settings"])
        
        with t1:
            if os.path.exists(ARCHIVE_DB):
                df_all = pd.read_csv(ARCHIVE_DB)
                # فیلتر کردن برای ۷ روز گذشته
                df_all['Date'] = pd.to_datetime(df_all['Date'])
                last_week = datetime.now() - timedelta(days=7)
                df_weekly = df_all[df_all['Date'] >= last_week]
                
                st.subheader("Orders from Last 7 Days")
                st.dataframe(df_weekly, use_container_width=True)
                st.download_button("Download Weekly Report (CSV)", df_weekly.to_csv(index=False), "SandView_Weekly.csv")
        
        with t2:
            st.subheader("Change Access Passwords")
            new_staff = st.text_input("New Staff Password", value=settings["staff_pwd"])
            new_admin = st.text_input("New Manager Password", value=settings["admin_pwd"])
            if st.button("Update Passwords"):
                save_settings({"staff_pwd": new_staff, "admin_pwd": new_admin})
                st.success("Passwords updated successfully!")
