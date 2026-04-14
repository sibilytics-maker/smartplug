import streamlit as st
import paho.mqtt.client as mqtt
import time

# --- CONFIG ---
MQTT_BROKER = "metro.proxy.rlwy.net"
MQTT_PORT = 55113
MQTT_USER = "kundansmart"
MQTT_PASS = "Kundan@1985"

if "device_status" not in st.session_state:
    st.session_state.device_status = "OFF"

def on_message(client, userdata, msg):
    new_status = msg.payload.decode()
    if new_status in ["ON", "OFF"]:
        st.session_state.device_status = new_status

if "mqtt_client" not in st.session_state:
    # Initialize the client inside the session state block
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    # client.tls_set() # Commented out for Railway TCP Proxy
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe("smartplug/status")
    client.loop_start()
    st.session_state.mqtt_client = client

st.set_page_config(page_title="Smart Plug", layout="centered")

st.title("🔌 Smart Plug Control")
st.markdown("---")

# 1. Status Display
status_color = "green" if st.session_state.device_status == "ON" else "red"
st.markdown(f"### Current Status: :{status_color}[{st.session_state.device_status}]")

# 2. Dynamic Buttons
col1, col2 = st.columns(2)

# Select emoji based on status
on_emoji = "🟢" if st.session_state.device_status == "ON" else "⚪"
off_emoji = "⚪" if st.session_state.device_status == "ON" else "🔴"

with col1:
    if st.button(f"{on_emoji} TURN ON", use_container_width=True):
        st.session_state.mqtt_client.publish("smartplug/control", "ON")
        st.session_state.device_status = "ON"
        st.toast("Command Sent: ON ✅")
        time.sleep(0.5)
        st.rerun()

with col2:
    if st.button(f"{off_emoji} TURN OFF", use_container_width=True):
        st.session_state.mqtt_client.publish("smartplug/control", "OFF")
        st.session_state.device_status = "OFF"
        st.toast("Command Sent: OFF ⚪")
        time.sleep(0.5)
        st.rerun()

st.markdown("---")
st.caption("Auto-syncing with device every 2 seconds...")

# 3. Background sync
time.sleep(2)
st.rerun()
