from fastapi import FastAPI, HTTPException
import paho.mqtt.client as mqtt
import uvicorn

app = FastAPI()

# --- CONFIG ---
MQTT_BROKER = "metro.proxy.rlwy.net"
MQTT_PORT = 55113

# Initialize MQTT Client
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
# mqtt_client.username_pw_set("kundan", "Kundan@1985") # Uncomment if you set a password

@app.on_event("startup")
def startup_event():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()

# 1. Login Endpoint (Tapo-style)
@app.post("/login")
def login(data: dict):
    # In a real app, check these against your PostgreSQL database
    if data.get("username") == "kundan" and data.get("password") == "Kundan@1985":
        return {"status": "success", "token": "user_session_abc_123"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# 2. Control Endpoint (What your mobile app calls)
@app.post("/control")
def control_device(data: dict):
    device_id = data.get("device_id", "smartplug")
    action = data.get("action") # "ON" or "OFF"
    
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
    uvicorn.run(app, host="0.0.0.0", port=8080)
