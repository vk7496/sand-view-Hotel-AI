import streamlit as st
from groq import Groq
from datetime import datetime, timedelta
import pandas as pd
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Sand View Hotel | AI Infrastructure", layout="wide")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("API Error: Check Secrets.")

# --- DATABASE FILES ---
LIVE_DB = "orders_live.csv"
ARCHIVE_DB = "orders_archive.csv"

def load_data(file):
    if os.path.exists(file):
        return pd.read_csv(file).to_dict('records')
    return []

def save_to_live(order):
    orders = load_data(LIVE_DB)
    orders.append(order)
    pd.DataFrame(orders).to_csv(LIVE_DB, index=False)

def archive_order(order):
    archive = load_data(ARCHIVE_DB)
    archive.append(order)
    pd.DataFrame(archive).to_csv(ARCHIVE_DB, index=False)

def complete_order(index):
    orders = load_data(LIVE_DB)
    if 0 <= index < len(orders):
        orders.pop(index)
        pd.DataFrame(orders).to_csv(LIVE_DB, index=False)

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background: #fdfcfb; }
    .order-card { background: white; padding: 15px; border-radius: 10px; border-left: 6px solid #D4B996; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #333; }
    .footer { text-align: center; color: #888; font-size: 0.8em; margin-top: 50px; padding: 20px; border-top: 1px dotted #ccc; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("logo.png") 
    st.title("Sand View AI")
    page = st.radio("Navigation", ["Guest Experience", "Staff Dashboard", "Management Reports"])

# --- PAGE 1: GUEST CHAT ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        st.header("Welcome to Sand View Hotel")
        u_name = st.text_input("Full Name")
        u_room = st.text_input("Room Number")
        if st.button("Start AI Concierge"):
            if u_name and u_room:
                st.session_state.user_data = {"name": u_name, "room": u_room}
                st.rerun()
    else:
        st.subheader(f"Room {st.session_state.user_data['room']} | {st.session_state.user_data['name']}")
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Ask me anything..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                service_keywords = ['want', 'need', 'bring', 'order', 'taxi', 'clean', 'water', 'towel', 'food', 'check-out', 'breakfast', 'laundry']
                is_service = any(word in prompt.lower() for word in service_keywords)

                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "system", "content": "You are Sand View AI. If a guest asks for something, tell them you've notified the staff."},
                                  {"role": "user", "content": prompt}]
                    )
                    ai_reply = response.choices[0].message.content
                    st.markdown(ai_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})

                    if is_service:
                        order_details = {
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Time": datetime.now().strftime("%H:%M"),
                            "Room": st.session_state.user_data['room'],
                            "Guest": st.session_state.user_data['name'],
                            "Request": prompt
                        }
                        save_to_live(order_details) # ذخیره برای خدمه
                        archive_order(order_details) # ذخیره ابدی برای مدیر
                        st.toast("Request Sent! 🔔")
                except: st.error("AI Error.")

# --- PAGE 2: STAFF DASHBOARD ---
elif page == "Staff Dashboard":
    st.title("🛎️ Live Service Requests")
    pwd_staff = st.text_input("Staff Password", type="password")
    
    if pwd_staff == "staff123":
        live_orders = load_data(LIVE_DB)
        if not live_orders:
            st.info("No pending requests.")
        else:
            for i, order in enumerate(live_orders):
                st.markdown(f"""<div class="order-card">
                    <strong>Room {order['Room']} - {order['Guest']}</strong><br>
                    {order['Request']}<br><small>{order['Time']}</small>
                </div>""", unsafe_allow_html=True)
                if st.button("Mark Completed", key=f"done_{i}"):
                    complete_order(i)
                    st.rerun()
    elif pwd_staff: st.error("Access Denied")

# --- PAGE 3: MANAGEMENT REPORTS ---
elif page == "Management Reports":
    st.title("📊 Strategic Analytics")
    pwd_mgr = st.text_input("Manager Password", type="password")
    
    if pwd_mgr == "admin789":
        archive_data = load_data(ARCHIVE_DB)
        if archive_data:
            df = pd.DataFrame(archive_data)
            df['Date'] = pd.to_datetime(df['Date'])
            
            # فیلتر ۱ هفته اخیر به صورت خودکار
            one_week_ago = datetime.now() - timedelta(days=7)
            weekly_df = df[df['Date'] >= one_week_ago]
            
            st.subheader("Last 7 Days Activity")
            st.dataframe(weekly_df)
            
            # خروجی اکسل برای مدیر
            csv = weekly_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Weekly Analysis (CSV)", csv, "weekly_report.csv", "text/csv")
            
            # آمار کوچک برای مدیر
            st.metric("Total Requests (7 days)", len(weekly_df))
        else:
            st.info("No archive data found.")
    elif pwd_mgr: st.error("Access Denied")

# --- FOOTER ---
st.markdown(f"""<div class="footer">AI Developer: <b>Vista Kaviani</b> | Vistakavianii@gmail.com</div>""", unsafe_allow_html=True)
