import streamlit as st
from groq import Groq
from datetime import datetime
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Sand View Hotel | AI Hub", layout="wide")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("API Error: Check Secrets.")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background: #fdfcfb; }
    .order-card { background: white; padding: 15px; border-radius: 10px; border-left: 6px solid #D4B996; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .footer { text-align: center; color: #888; font-size: 0.8em; margin-top: 50px; padding: 20px; border-top: 1px dotted #ccc; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
if 'orders' not in st.session_state: st.session_state.orders = []
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏝️ Sand View")
    page = st.radio("Menu", ["Guest Chat", "Staff Dashboard"])
    st.markdown("---")
    if st.session_state.user_data:
        st.info(f"Room: {st.session_state.user_data['room']}")

# --- PAGE 1: GUEST CHAT ---
if page == "Guest Chat":
    if not st.session_state.user_data:
        st.header("Welcome to Sand View")
        u_name = st.text_input("Full Name")
        u_room = st.text_input("Room Number")
        if st.button("Access AI Concierge"):
            if u_name and u_room:
                st.session_state.user_data = {"name": u_name, "room": u_room}
                st.rerun()
    else:
        st.subheader(f"How can we help you, {st.session_state.user_data['name']}?")
        
        # نمایش چت
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Type your request here..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                # منطق حساسیت بالا: تشخیص خودکار هرگونه درخواست خدماتی
                service_keywords = ['want', 'need', 'bring', 'order', 'taxi', 'clean', 'water', 'towel', 'food', 'check-out']
                is_service_request = any(word in prompt.lower() for word in service_keywords)

                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "You are the Sand View Hotel AI. If the guest asks for any service, food, or item, provide a helpful response and ensure the staff will be notified. Always be polite."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ai_reply = response.choices[0].message.content
                    st.markdown(ai_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})

                    # ثبت خودکار سفارش بدون نیاز به تایید مسافر
                    if is_service_request:
                        new_order = {
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Time": datetime.now().strftime("%H:%M"),
                            "Room": st.session_state.user_data['room'],
                            "Guest": st.session_state.user_data['name'],
                            "Request": prompt
                        }
                        st.session_state.orders.append(new_order)
                        st.toast("Staff Notified! 🔔", icon="✅")
                except: st.error("AI is offline.")

# --- PAGE 2: STAFF DASHBOARD (SECURE) ---
elif page == "Staff Dashboard":
    st.title("🔒 Staff Control Panel")
    
    # قفل رمز عبور
    password = st.text_input("Enter Staff Password", type="password")
    if password == "sand2024": # رمز عبور را اینجا تغییر دهید
        tab_live, tab_report = st.tabs(["🛎️ Live Orders", "📊 Weekly Report"])

        with tab_live:
            if not st.session_state.orders:
                st.info("No active requests.")
            else:
                for i, order in enumerate(st.session_state.orders):
                    st.markdown(f"""
                    <div class="order-card">
                        <strong>Room {order['Room']} - {order['Guest']}</strong><br>
                        Request: {order['Request']}<br>
                        <small>Time: {order['Time']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Mark as Completed", key=f"done_{i}"):
                        st.session_state.orders.pop(i)
                        st.rerun()

        with tab_report:
            st.subheader("Weekly Operations Report")
            if st.session_state.orders:
                df = pd.DataFrame(st.session_state.orders)
                st.dataframe(df)
                
                # دکمه دانلود گزارش برای مدیریت
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Weekly Report (CSV)",
                    data=csv,
                    file_name=f"SandView_Report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                )
            else:
                st.write("No data available for report yet.")
    elif password != "":
        st.error("Incorrect Password")

# --- FOOTER ---
st.markdown(f"""
    <div class="footer">
        © 2024 Sand View Hotel | AI Infrastructure developed by <b>Vista Kaviani</b><br>
        Email: Vistakavianii@gmail.com
    </div>
    """, unsafe_allow_html=True)
