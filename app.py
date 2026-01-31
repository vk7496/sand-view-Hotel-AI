import streamlit as st
from groq import Groq
from datetime import datetime
import pandas as pd

# --- 1. CONFIGURATION & AI SETUP ---
st.set_page_config(page_title="Sand View Hotel | AI Smart Hub", layout="wide", page_icon="🏝️")

try:
    # Accessing the API Key from Streamlit Secrets
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("AI Configuration Error. Please verify the API Key in Secrets.")

# --- 2. PROFESSIONAL THEMEING (CSS) ---
st.markdown("""
    <style>
    .stApp { background: #fdfcfb; }
    [data-testid="stSidebar"] { background-color: #2C3E50; color: white; }
    .main-header { text-align: center; padding: 30px; background: linear-gradient(135deg, #2C3E50, #4CA1AF); color: white; border-radius: 15px; margin-bottom: 25px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #D4B996; color: white; height: 3.5em; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #C1A57B; border: none; color: white; }
    .order-card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #D4B996; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; color: #333; }
    .status-badge { background: #e8f5e9; color: #2e7d32; padding: 4px 10px; border-radius: 10px; font-size: 0.8em; font-weight: bold; }
    .footer { text-align: center; color: #7f8c8d; font-size: 0.9em; margin-top: 60px; border-top: 1px solid #eee; padding-top: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE MANAGEMENT ---
if 'orders' not in st.session_state: st.session_state.orders = []
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'menu_visible' not in st.session_state: st.session_state.menu_visible = False

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/beach.png") # Replace with Sand View Logo URL
    st.title("Sand View Hotel")
    st.markdown("---")
    page = st.radio("Navigation", ["Guest Experience", "Management Hub"])
    st.markdown("---")
    if st.session_state.user_data:
        st.success(f"Logged in: {st.session_state.user_data['name']} (Room {st.session_state.user_data['room']})")
        if st.button("Logout"):
            st.session_state.user_data = None
            st.rerun()

# --- 5. GUEST EXPERIENCE PAGE ---
if page == "Guest Experience":
    if not st.session_state.user_data:
        # Welcome Screen & Login
        st.markdown("<div class='main-header'><h1>SAND VIEW HOTEL</h1><p>Smart Concierge & Hospitality Hub</p></div>", unsafe_allow_html=True)
        st.image("https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
        
        with st.container():
            st.subheader("Guest Check-in (Digital Access)")
            col_l, col_r = st.columns(2)
            u_name = col_l.text_input("Full Name")
            u_room = col_r.text_input("Room Number")
            if st.button("Start My Stay"):
                if u_name and u_room:
                    st.session_state.user_data = {"name": u_name, "room": u_room}
                    st.rerun()
                else: st.warning("Please provide your name and room number.")
    else:
        st.title(f"Welcome, {st.session_state.user_data['name']} 🛎️")
        
        # Service Quick Buttons
        st.write("How can we assist you today?")
        btn_cols = st.columns(4)
        services = {
            "🍔 Room Service": "I want to see the menu.",
            "🚕 Book a Taxi": "I need a taxi to the city center.",
            "👕 Laundry": "I need laundry pick-up.",
            "🧖 Spa & Wellness": "What are your spa services?"
        }
        
        for idx, (label, query) in enumerate(services.items()):
            if btn_cols[idx % 4].button(label):
                st.session_state.chat_history.append({"role": "user", "content": query})
        
        # Simulated Online Menu
        if st.button("🍽️ VIEW RESTAURANT MENU"):
            st.session_state.menu_visible = not st.session_state.menu_visible
        
        if st.session_state.menu_visible:
            st.markdown("""
            <div style="background:#fff9f0; padding:15px; border-radius:10px; border:1px solid #D4B996;">
                <h4 style="color:#2C3E50;">Today's Specials</h4>
                <ul style="list-style:none; padding:0;">
                    <li>🍱 <b>Omani Mix Grill</b> - 7.500 OMR</li>
                    <li>🥗 <b>Arabic Mezze Platter</b> - 4.200 OMR</li>
                    <li>☕ <b>Traditional Omani Kahwa</b> - 1.500 OMR</li>
                </ul>
                <small><i>To order, simply tell the AI below what you'd like!</i></small>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Chat Interface (Powered by Groq)
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Ask me about Oman, hotel services, or place an order..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "You are the AI Assistant for Sand View Hotel, Oman. If the guest wants food, service, taxi, or check-out, strictly start your reply with '[REQUEST]'. Be luxury, polite, and help with Oman tourism questions."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5
                    )
                    ai_reply = response.choices[0].message.content
                    st.markdown(ai_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})

                    if "[REQUEST]" in ai_reply:
                        st.session_state.orders.append({
                            "room": st.session_state.user_data['room'],
                            "guest": st.session_state.user_data['name'],
                            "task": prompt,
                            "time": datetime.now().strftime("%H:%M"),
                            "status": "New"
                        })
                        st.toast(f"New request from Room {st.session_state.user_data['room']} sent to Management.", icon="🔔")
                except: st.error("AI service temporarily unavailable.")

# --- 6. MANAGEMENT HUB (ADMIN) ---
elif page == "Management Hub":
    st.title("📊 Hotel Operational Dashboard")
    
    tab_live, tab_analysis = st.tabs(["🛎️ Live Requests", "📈 Guest Analytics"])

    with tab_live:
        if not st.session_state.orders:
            st.info("No active requests at the moment.")
        else:
            st.toast("Management Alert: New unread requests!", icon="⚠️")
            for i, order in enumerate(st.session_state.orders):
                st.markdown(f"""
                <div class="order-card">
                    <div style="display:flex; justify-content:space-between;">
                        <strong>Room {order['room']} - {order['guest']}</strong>
                        <span class="status-badge">{order['status']}</span>
                    </div>
                    <p style="margin-top:10px;">{order['task']}</p>
                    <small>Received at: {order['time']}</small>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Complete Task", key=f"complete_{i}"):
                    st.session_state.orders.pop(i)
                    st.rerun()

    with tab_analysis:
        st.subheader("Service Demand Analysis")
        if len(st.session_state.chat_history) > 0:
            st.write("AI-driven insights for management optimization:")
            # Mock Data for Analysis
            analytics_data = pd.DataFrame({
                "Service": ["Room Service", "Taxi", "Laundry", "Check-out"],
                "Requests": [12, 5, 3, 2]
            }).set_index("Service")
            st.bar_chart(analytics_data)
        else:
            st.info("Data will appear here after guest interaction.")

# --- 7. COPYRIGHT & DEVELOPER SIGNATURE ---
st.markdown(f"""
    <div class="footer">
        <p>© 2026 Sand View Hotel AI Infrastructure | Proprietary System</p>
        <p>Developed by: <b>Vista Kaviani</b> | AI Developer</p>
        <p>Contact: Vistakavianii@gmail.com</p>
    </div>
    """, unsafe_allow_html=True)
