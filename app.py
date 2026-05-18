from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import paho.mqtt.client as mqtt
import uvicorn
import os
import asyncio
from sqlalchemy import create_engine

# --- CONFIG ---
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883

# Initialize MQTT Client
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
#mqtt_client.username_pw_set("kundansmart", "Kundan@1985") 
mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

import time

# Flexible Timer Background Task
async def schedule_action(device_id: str, action: str, delay_seconds: int):
    await asyncio.sleep(delay_seconds)
    topic = f"{device_id}/control"
    if mqtt_client.is_connected():
        mqtt_client.publish(topic, action, retain=True)
        print(f"Timer Expired: Sent {action} command to {device_id}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Try connecting up to 5 times
    for i in range(5):
        try:
            print(f"Attempting MQTT connection (Attempt {i+1}/5)...")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            mqtt_client.loop_start()
            print("Successfully connected to MQTT Broker!")
            break
        except Exception as e:
            print(f"MQTT Connection Error: {e}")
            time.sleep(2) # Wait 2 seconds before retrying
    
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
def control_device(data: dict, background_tasks: BackgroundTasks):
    # device_id is dynamic to support multiple unique plugs (sibi101, sibi102, etc.)
    device_id = data.get("device_id", "smartplug")
    action = data.get("action")
    timer_minutes = data.get("timer", 0) 
    
    if action not in ["ON", "OFF", "RESET_WIFI"]:
        raise HTTPException(status_code=400, detail="Action must be ON, OFF, or RESET_WIFI")
        
    topic = f"{device_id}/control"
    
    if mqtt_client.is_connected():
        # Perform the immediate requested action
        mqtt_client.publish(topic, action, retain=True)
        
        # Dual-Logic Timer:
        # If user sends ON with timer -> It will Auto-OFF after X minutes
        # If user sends OFF with timer -> It will Auto-ON after X minutes
        if int(timer_minutes) > 0:
            delay_seconds = int(timer_minutes) * 60
            next_action = "OFF" if action == "ON" else "ON"
            
            background_tasks.add_task(schedule_action, device_id, next_action, delay_seconds)
            
            return {
                "status": "dispatched", 
                "device": device_id, 
                "immediate_action": action, 
                "scheduled_action": next_action,
                "delay": f"{timer_minutes} minutes"
            }
            
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
