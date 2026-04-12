import streamlit as st
import paho.mqtt.client as mqtt
import time

# --- CONFIG ---
MQTT_BROKER = "93be88c856bc40329b96e8fba46ac044.s1.eu.hivemq.cloud"
MQTT_USER = "kundan"
MQTT_PASS = "Kundan@1985"

# Initialize session state for status
if "device_status" not in st.session_state:
    st.session_state.device_status = "OFF"

# Callback when status is received from ESP32
def on_message(client, userdata, msg):
    # Only update if the message is ON or OFF
    new_status = msg.payload.decode()
    if new_status in ["ON", "OFF"]:
        st.session_state.device_status = new_status

# Initialize MQTT Client
if "mqtt_client" not in st.session_state:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()
    client.on_message = on_message
    client.connect(MQTT_BROKER, 8883)
    client.subscribe("smartplug/status") # Listen to status from ESP32
    client.loop_start()
    st.session_state.mqtt_client = client

st.set_page_config(page_title="Smart Plug", layout="centered")

st.title("🔌 Smart Plug Control")
st.markdown("---")

# Display Live Status
status_color = "green" if st.session_state.device_status == "ON" else "red"
st.subheader(f"Current Status: :{status_color}[{st.session_state.device_status}]")

# Control Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🔴 TURN ON", use_container_width=True):
        st.session_state.mqtt_client.publish("smartplug/control", "ON")
        st.toast("Command Sent: ON")

with col2:
    if st.button("⚪ TURN OFF", use_container_width=True):
        st.session_state.mqtt_client.publish("smartplug/control", "OFF")
        st.toast("Command Sent: OFF")

st.markdown("---")

# Refresh the UI every 2 seconds to check for MQTT status updates
time.sleep(2)
st.rerun()
