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

# --- ۱. تنظیمات و زمان‌بندی ---
st.set_page_config(page_title="Sand View Hotel | Global Hub", layout="wide")
oman_tz = pytz.timezone('Asia/Muscat')

LIVE_DB = "orders_live.csv"
ARCHIVE_DB = "orders_archive.csv"
SETTINGS_FILE = "settings.json"

# --- ۲. توابع مدیریت داده ---
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

# --- ۳. رابط کاربری (Coastal Theme) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=80");
        background-size: cover; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{ background-color: rgba(28, 45, 102, 0.95) !important; backdrop-filter: blur(15px); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: white !important; text-shadow: 1px 1px 4px black; }}
    
    .order-card {{
        background: rgba(255, 255, 255, 0.98); padding: 22px; border-radius: 15px;
        border-left: 8px solid #d4b996; margin-bottom: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }}
    .order-card * {{ color: #1c2d66 !important; text-shadow: none !important; }}
    .id-tag {{ background-color: #d4b996; color: white !important; padding: 4px 12px; border-radius: 8px; font-weight: bold; font-size: 0.9rem; }}
    
    .translation-box {{ 
        background: #f0f4f8; padding: 10px; border-radius: 8px; margin-top: 10px;
        border: 1px dashed #1c2d66; color: #1c2d66 !important; font-weight: 600;
    }}
    
    .sidebar-footer {{
        margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);
        text-align: center; color: #d4b996 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- ۴. وضعیت نشست ---
settings = load_settings()
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'last_count' not in st.session_state: st.session_state.last_count = 0

# --- ۵. سایدبار و لوگو ---
with st.sidebar:
    st.image("logo.png", width=200) # لوگو هتل
    st.markdown("<h2 style='text-align:center;'>Sand View AI</h2>", unsafe_allow_html=True)
    page = st.radio("Menu", ["Guest Experience", "Digital Menu", "Staff Dashboard", "Management"])
    
    st.markdown(f"""
    <div class="sidebar-footer">
        Developed by:<br>
        <span style="color:white; font-size:1.1rem; font-weight:bold;">Vista Kaviani</span><br>
        <span style="font-size:0.8rem;">AI Solutions Developer  -vistakavianii@gmail.com</span>
    </div>
    """, unsafe_allow_html=True)

# --- ۶. صفحه مسافر (Universal Translator) ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.markdown("<h1 style='text-align:center; font-size:3rem;'>Welcome to Paradise</h1>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            name = st.text_input("Your Name")
            room = st.text_input("Room Number")
            if st.button("Enter Experience", use_container_width=True):
                if name and room:
                    st.session_state.user_data = {"name": name, "room": room}
                    st.rerun()
    else:
        st.markdown(f"### Hello, {st.session_state.user_data['name']} (Room {st.session_state.user_data['room']})")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])

        if prompt := st.chat_input("I need help with... / احتاج الى..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # هوشمندسازی ترجمه برای تمام زبان‌ها
                ai_response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    response_format={"type": "json_object"},
                    messages=[{
                        "role": "system", 
                        "content": """You are a multilingual hotel concierge. 
                        Detect the language of the input (could be ANY language).
                        1. Translate the request to clear, formal English.
                        2. Identify if the user wants/needs/orders something (is_order: true/false).
                        3. Provide a warm reply in the USER'S ORIGINAL language.
                        Return ONLY JSON: 
                        {"is_order": bool, "english": "string", "reply": "string"}"""
                    }, {"role": "user", "content": prompt}]
                )
                
                data = json.loads(ai_response.choices[0].message.content)
                is_order = data.get("is_order", False)
                translation = data.get("english", "")
                ai_msg = data.get("reply", "I've received your message.")

                if is_order:
                    oid = generate_order_id()
                    ai_msg += f"\n\n✅ **Request Logged: {oid}**"
                    now = datetime.now(oman_tz)
                    # ذخیره متن اصلی + ترجمه انگلیسی
                    order_entry = {
                        "ID": oid, "Date": now.strftime("%Y-%m-%d"), "Time": now.strftime("%H:%M"), 
                        "Room": st.session_state.user_data['room'], "Guest": st.session_state.user_data['name'], 
                        "Request": f"{prompt} | 🔠 Translation: {translation}"
                    }
                    save_order(order_entry, LIVE_DB)
                    save_order(order_entry, ARCHIVE_DB)
                    st.toast("Staff Notified!")

            except:
                ai_msg = "Staff has been notified of your request."

            st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
            st.rerun()

# --- ۷. منوی دیجیتال ---
elif page == "Digital Menu":
    st.markdown("<h1>📖 Digital Menu</h1>", unsafe_allow_html=True)
    st.write("Browse and ask the AI to order for you!")
    st.table(pd.DataFrame({
        "Item": ["Fresh Coconut", "Club Sandwich", "Omani Coffee", "Laundry Service"],
        "Price": ["2.5 OMR", "4.0 OMR", "1.5 OMR", "Varied"]
    }))

# --- ۸. داشبورد پذیرش (Staff Hub) ---
elif page == "Staff Dashboard":
    st.markdown("<h1>🛎️ Reception Dashboard</h1>", unsafe_allow_html=True)
    if st.text_input("Staff Code", type="password") == settings["staff_pwd"]:
        df = pd.read_csv(LIVE_DB)
        
        # صدای نوتیفیکیشن
        if len(df) > st.session_state.last_count:
            st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)
            st.session_state.last_count = len(df)

        if df.empty:
            st.info("No pending requests.")
        else:
            for i, row in df.iterrows():
                parts = row['Request'].split("|")
                st.markdown(f"""
                <div class="order-card">
                    <span class="id-tag">{row['ID']}</span> <b>Room {row['Room']}</b> - {row['Guest']}<br>
                    <p style='margin-top:10px;'><b>Guest Wrote:</b> {parts[0]}</p>
                    <div class="translation-box">🇬🇧 English: {parts[1] if len(parts)>1 else "N/A"}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Complete {row['ID']}", key=f"c_{row['ID']}"):
                    pd.read_csv(LIVE_DB).drop(i).to_csv(LIVE_DB, index=False)
                    st.session_state.last_count = max(0, st.session_state.last_count - 1)
                    st.rerun()
        time.sleep(5); st.rerun()

# --- ۹. مدیریت و امنیت ---
elif page == "Management":
    st.markdown("<h1>📊 Administration</h1>", unsafe_allow_html=True)
    if st.text_input("Admin Code", type="password") == settings["admin_pwd"]:
        t1, t2 = st.tabs(["Archives", "Settings"])
        with t1:
            if os.path.exists(ARCHIVE_DB):
                st.dataframe(pd.read_csv(ARCHIVE_DB))
        with t2:
            s_p = st.text_input("New Staff PWD", value=settings["staff_pwd"])
            a_p = st.text_input("New Admin PWD", value=settings["admin_pwd"])
            if st.button("Update Passwords"):
                save_settings({"staff_pwd": s_p, "admin_pwd": a_p})
                st.success("Security Updated!")
