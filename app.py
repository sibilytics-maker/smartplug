import streamlit as st
import paho.mqtt.client as mqtt
import time

# --- CONFIG ---
MQTT_BROKER = "93be88c856bc40329b96e8fba46ac044.s1.eu.hivemq.cloud"
MQTT_USER = "kundan"
MQTT_PASS = "Kundan@1985"

st.set_page_config(page_title="Smart Plug", layout="centered")

if "mqtt_client" not in st.session_state:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()
    client.connect(MQTT_BROKER, 8883)
    client.loop_start()
    st.session_state.mqtt_client = client

st.title("🔌 Smart Plug Control")
st.markdown("---")

# Main Page Buttons (Mobile Friendly)
col1, col2 = st.columns(2)

with col1:
    if st.button("🔴 TURN ON", use_container_width=True):
        st.session_state.mqtt_client.publish("smartplug/control", "ON")
        st.toast("Switching ON...")

with col2:
    if st.button("⚪ TURN OFF", use_container_width=True):
        st.session_state.mqtt_client.publish("smartplug/control", "OFF")
        st.toast("Switching OFF...")

st.markdown("---")
st.info("Status updates every 5 seconds from device.")
