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

# Lifespan manager replaces the deprecated on_event startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MQTT
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
    yield
    # Shutdown: Disconnect
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

app = FastAPI(lifespan=lifespan)

# Allow Chrome/Web apps to connect (Fixes the 405 error in your logs)
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
    engine = create_engine(db_url)

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
    
    if action not in ["ON", "OFF"]:
        raise HTTPException(status_code=400, detail="Action must be ON or OFF")
        
    topic = f"{device_id}/control"
    mqtt_client.publish(topic, action)
    return {"status": "dispatched", "topic": topic, "command": action}

# 3. Health Check
@app.get("/")
def home():
    return {"message": "Tapo-like API is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)
