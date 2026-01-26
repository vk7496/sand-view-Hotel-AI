import streamlit as st
import pandas as pd
from datetime import datetime

# تنظیمات صفحه
st.set_page_config(page_title="Sand View Hotel - AI Hub", layout="wide")

# استایل اختصاصی برای تم ساحلی (Sand View)
st.markdown("""
    <style>
    .main { background-color: #fdfcfb; }
    .stButton>button { background-color: #D4B996; color: #2C3E50; border-radius: 10px; }
    .order-card { 
        padding: 20px; border-radius: 15px; border-left: 5px solid #D4B996;
        background-color: white; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_view_to_html=True)

# شبیه‌سازی دیتابیس سفارشات در حافظه
if 'orders' not in st.session_state:
    st.session_state.orders = [
        {"room": "304", "item": "2x Club Sandwich", "time": "11:20", "status": "Verified by AI"},
        {"room": "102", "item": "Late Check-out (2 PM)", "time": "11:25", "status": "Pending Review"}
    ]

# طراحی سایدبار
with st.sidebar:
    st.image("https://img.icons8.com/color/96/beach.png", width=100)
    st.title("Sand View Admin")
    page = st.radio("Navigate to:", ["Guest View (AI Chat)", "Internal Order Hub"])

# ۱. بخش مسافر (Guest View)
if page == "Guest View (AI Chat)":
    st.title("🏝️ Sand View AI Concierge")
    st.info("Try asking for room service or a late check-out.")
    
    chat_input = st.chat_input("How can I help you today?")
    if chat_input:
        with st.chat_message("user"):
            st.write(chat_input)
        with st.chat_message("assistant"):
            if "order" in chat_input.lower() or "sandwich" in chat_input.lower():
                st.write("I've captured your order! I'm sending it directly to our Kitchen Hub now (Bypassing WhatsApp for faster service).")
                # اضافه کردن سفارش جدید به لیست
                new_order = {"room": "205", "item": chat_input, "time": datetime.now().strftime("%H:%M"), "status": "Verified by AI"}
                st.session_state.orders.append(new_order)
            else:
                st.write("Certainly! I'm here to assist with your stay at Sand View.")

# ۲. بخش مدیریت (Internal Order Hub) - این همان بخشی است که هتل می‌خواست
elif page == "Internal Order Hub":
    st.title("👨‍🍳 Kitchen & Service Dashboard")
    st.write("This dashboard replaces WhatsApp notifications with organized, actionable tasks.")
    
    col1, col2 = st.columns(2)
    
    for i, order in enumerate(st.session_state.orders):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
                <div class="order-card">
                    <h4 style="margin:0;">Room {order['room']}</h4>
                    <p style="margin:5px 0;"><b>Request:</b> {order['item']}</p>
                    <span style="font-size:0.8em; color:gray;">Time: {order['time']} | Status: {order['status']}</span>
                </div>
            """, unsafe_allow_view_to_html=True)
            if st.button(f"Mark as Completed", key=f"btn_{i}"):
                st.success(f"Order for Room {order['room']} cleared!")
