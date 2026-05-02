from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import paho.mqtt.client as mqtt
import uvicorn
import os
from sqlalchemy import create_engine

# --- CONFIG ---
MQTT_BROKER = "metro.proxy.rlwy.net"
MQTT_PORT = 55113

# Initialize MQTT Client
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set("kundansmart", "Kundan@1985") 
mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT Connection Error: {e}")
    
    yield
    
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
db_url = os.getenv("DATABASE_URL")
if db_url:
    engine = create_engine(db_url, pool_size=5, max_overflow=10)

# 1. Login Endpoint
@app.post("/login")
def login(data: dict):
    if data.get("username") == "kundan" and data.get("password") == "Kundan@1985":
        return {"status": "success", "token": "user_session_abc_123"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# 2. Control Endpoint
@app.post("/control")
def control_device(data: dict):
    device_id = data.get("device_id", "smartplug")
    action = data.get("action")
    
    if action not in ["ON", "OFF", "RESET_WIFI"]:
        raise HTTPException(status_code=400, detail="Action must be ON, OFF, or RESET_WIFI")
        
    topic = f"{device_id}/control"
    
    if mqtt_client.is_connected():
        # retain=True ensures the command is saved if the device is offline
        mqtt_client.publish(topic, action, retain=True)
        return {"status": "dispatched", "topic": topic, "command": action}
    else:
        raise HTTPException(status_code=503, detail="MQTT Broker not reachable")

# 3. Health Check
@app.get("/")
def home():
    return {"message": "Tapo-like API is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)
