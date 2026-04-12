import streamlit as st
import paho.mqtt.client as mqtt
import time

# --- CONFIG ---
MQTT_BROKER = "93be88c856bc40329b96e8fba46ac044.s1.eu.hivemq.cloud"
MQTT_USER = "kundan"
MQTT_PASS = "Kundan@1985"

# 1. Initialize session state
if "device_status" not in st.session_state:
    st.session_state.device_status = "OFF"

# 2. Callback for incoming status from ESP32
def on_message(client, userdata, msg):
    new_status = msg.payload.decode()
    if new_status in ["ON", "OFF"]:
        st.session_state.device_status = new_status

# 3. MQTT Setup
if "mqtt_client" not in st.session_state:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()
    client.on_message = on_message
    client.connect(MQTT_BROKER, 8883)
    client.subscribe("smartplug/status")
    client.loop_start()
    st.session_state.mqtt_client = client

st.set_page_config(page_title="Smart Plug", layout="centered")

# --- CUSTOM CSS FOR DYNAMIC COLORS ---
# This makes the "primary" button green and secondary red
st.markdown("""
    <style>
    /* Green Primary Button */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #28a745 !important;
        color: white !important;
        border: none;
    }
    /* Red Alert Button (When OFF) */
    div[data-testid="stButton"] button[kind="secondary"]:active {
        color: #dc3545 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔌 Smart Plug Control")
st.markdown("---")

# 4. Status Display
status_color = "green" if st.session_state.device_status == "ON" else "red"
st.markdown(f"### Current Status: :{status_color}[{st.session_state.device_status}]")

# 5. Dynamic Buttons
col1, col2 = st.columns(2)

with col1:
    # If device is ON, show as Primary (Green)
    btn_type = "primary" if st.session_state.device_status == "ON" else "secondary"
    if st.button("🔴 TURN ON", type=btn_type, use_container_width=True):
        st.session_state.mqtt_client.publish("smartplug/control", "ON")
        st.session_state.device_status = "ON"
        st.toast("Command Sent: ON ✅")
        time.sleep(0.5)
        st.rerun()

with col2:
    # Always secondary, but text turns red if current status is OFF
    if st.button("⚪ TURN OFF", use_container_width=True):
        st.session_state.mqtt_client.publish("smartplug/control", "OFF")
        st.session_state.device_status = "OFF"
        st.toast("Command Sent: OFF ⚪")
        time.sleep(0.5)
        st.rerun()

st.markdown("---")
st.caption("Auto-syncing with device every 2 seconds...")

# 6. Background sync
time.sleep(2)
st.rerun()
