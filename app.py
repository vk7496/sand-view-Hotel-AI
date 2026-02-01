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

# --- ۱. تنظیمات اولیه و زمان مسقط ---
st.set_page_config(page_title="Sand View Hotel | Smart Hub", layout="wide")
oman_tz = pytz.timezone('Asia/Muscat')

LIVE_DB = "orders_live.csv"
ARCHIVE_DB = "orders_archive.csv"
SETTINGS_FILE = "settings.json"

# --- ۲. منطق دیتابیس و تنظیمات ---
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

# --- ۳. استایل‌دهی ظاهری (Coastal Luxury) ---
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
    
    .translation-text {{ color: #d4b996 !important; font-style: italic; font-weight: bold; margin-top: 5px; display: block; border-top: 1px solid #eee; padding-top: 5px; }}
    
    .sidebar-footer {{
        margin-top: 50px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);
        font-size: 0.85rem; color: rgba(255,255,255,0.7) !important; text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- ۴. مقداردهی اولیه استیت‌ها ---
settings = load_settings()
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'last_order_count' not in st.session_state: st.session_state.last_order_count = 0

# --- ۵. سایدبار و امضای توسعه‌دهنده ---
with st.sidebar:
    st.image("logo.png", width=150) # جایگزین لوگو
    st.markdown("<h2 style='text-align:center;'>Sand View AI</h2>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Guest Experience", "Digital Menu", "Staff Dashboard", "Management Reports"])
    
    st.markdown(f"""
    <div class="sidebar-footer">
        Prepared by:<br>
        <b>Vista Kaviani</b><br>
        AI Solutions Developer<br>
        <span style="font-size:0.75rem;">Vistakavianii@gmail.com</span>
    </div>
    """, unsafe_allow_html=True)

# --- ۶. بخش مسافر (Guest Experience) ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.markdown("<h1 style='font-size:3.5rem; text-align:center;'>Welcome to Sand View</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            u_name = st.text_input("Full Name / الاسم الكامل")
            u_room = st.text_input("Room Number / رقم الغرفة")
            if st.button("Start My Experience", use_container_width=True):
                if u_name and u_room:
                    st.session_state.user_data = {"name": u_name, "room": u_room}
                    st.balloons(); st.rerun()
    else:
        st.markdown(f"<h3>Enjoy your stay, {st.session_state.user_data['name']} (Room {st.session_state.user_data['room']})</h3>", unsafe_allow_html=True)
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("I need something... / احتاج الى..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # مرحله ۱: تشخیص هوشمند نیت (هر زبانی)
                analysis_res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "Analyze user input in ANY language. If they want to order, need something, book something, or need a service, reply ONLY 'ORDER'. Otherwise 'CHAT'."}, 
                              {"role": "user", "content": prompt}]
                )
                intent = analysis_res.choices[0].message.content.strip().upper()

                # مرحله ۲: ترجمه به انگلیسی برای پرسنل
                trans_res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "Translate the request to English. Only the translation."}, 
                              {"role": "user", "content": prompt}]
                )
                translated_text = trans_res.choices[0].message.content.strip()

                # مرحله ۳: پاسخ به مسافر
                response_res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": "You are a hotel concierge. Confirm the request in the user's language."}, 
                              {"role": "user", "content": prompt}]
                )
                ai_msg = response_res.choices[0].message.content

                if "ORDER" in intent:
                    order_id = generate_order_id()
                    ai_msg += f"\n\n✅ **ID: {order_id}**"
                    now_o = datetime.now(oman_tz)
                    # ثبت متن اصلی و ترجمه
                    record = {"ID": order_id, "Date": now_o.strftime("%Y-%m-%d"), "Time": now_o.strftime("%H:%M"), 
                              "Room": st.session_state.user_data['room'], "Guest": st.session_state.user_data['name'], 
                              "Request": f"{prompt} | Translation: {translated_text}"}
                    save_order(record, LIVE_DB)
                    save_order(record, ARCHIVE_DB)
                    st.toast(f"Request {order_id} Registered!")

            except:
                ai_msg = "Your request is received and being processed."

            st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
            st.rerun()

# --- ۷. منوی دیجیتال ---
elif page == "Digital Menu":
    st.markdown("<h1>📖 Hotel Menu</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div style='background:rgba(0,0,0,0.4); padding:20px; border-radius:15px;'>
        <h3>☕ Cafe</h3>
        - Omani Coffee: 1.500 OMR<br>- Fresh Juice: 2.000 OMR<br>- Signature Tea: 0.800 OMR
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div style='background:rgba(0,0,0,0.4); padding:20px; border-radius:15px;'>
        <h3>🍽️ Restaurant</h3>
        - Grilled Salmon: 8.500 OMR<br>- Club Sandwich: 3.500 OMR<br>- Mezze Platter: 4.200 OMR
        </div>""", unsafe_allow_html=True)

# --- ۸. پنل پرسنل (Staff Dashboard) با آپدیت خودکار ---
elif page == "Staff Dashboard":
    st.markdown("<h1>🛎️ Live Reception</h1>", unsafe_allow_html=True)
    if st.text_input("Staff Password", type="password") == settings["staff_pwd"]:
        df_live = pd.read_csv(LIVE_DB)
        
        # صدای نوتیفیکیشن ملایم برای سفارش جدید
        if len(df_live) > st.session_state.last_order_count:
            st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)
            st.session_state.last_order_count = len(df_live)

        if df_live.empty:
            st.info("No active requests. System is monitoring...")
        else:
            for i, row in df_live.iterrows():
                parts = row['Request'].split("|")
                original = parts[0]
                trans = parts[1] if len(parts) > 1 else ""
                
                st.markdown(f"""<div class="order-card-live">
                    <span class="id-badge">{row['ID']}</span> <b>Room {row['Room']}</b> | {row['Guest']}<br>
                    <b>Message:</b> {original}<br>
                    <span class="translation-text">{trans}</span>
                    <br><small>Time: {row['Time']} (Oman)</small></div>""", unsafe_allow_html=True)
                
                if st.button(f"Mark Completed {row['ID']}", key=f"btn_{row['ID']}"):
                    pd.read_csv(LIVE_DB).drop(i).to_csv(LIVE_DB, index=False)
                    st.session_state.last_order_count = max(0, st.session_state.last_order_count - 1)
                    st.rerun()
        
        # رفرش خودکار هر ۵ ثانیه مخصوص دسکتاپ پذیرش
        time.sleep(5); st.rerun()

# --- ۹. پنل مدیریت (Management Reports) ---
elif page == "Management Reports":
    st.markdown("<h1>📊 Management Hub</h1>", unsafe_allow_html=True)
    if st.text_input("Manager Password", type="password") == settings["admin_pwd"]:
        tab1, tab2 = st.tabs(["7-Day Analytics", "System Security"])
        
        with tab1:
            if os.path.exists(ARCHIVE_DB):
                df_all = pd.read_csv(ARCHIVE_DB)
                df_all['Date'] = pd.to_datetime(df_all['Date'])
                last_7_days = datetime.now() - timedelta(days=7)
                df_weekly = df_all[df_all['Date'] >= last_7_days]
                
                st.subheader("Orders from Last 7 Days")
                st.dataframe(df_weekly, use_container_width=True)
                st.download_button("Download Weekly Report", df_weekly.to_csv(index=False), "SandView_Report.csv")
        
        with tab2:
            st.subheader("Update Passwords")
            col_p1, col_p2 = st.columns(2)
            new_s = col_p1.text_input("New Staff Password", value=settings["staff_pwd"])
            new_a = col_p2.text_input("New Manager Password", value=settings["admin_pwd"])
            if st.button("Apply Security Changes"):
                save_settings({"staff_pwd": new_s, "admin_pwd": new_a})
                st.success("Passwords updated successfully!")
