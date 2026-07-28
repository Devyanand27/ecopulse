"""
EcoPulse – Global Climate Intelligence Platform
FastAPI backend with all endpoints, plus new:
- Risk Alerts (/api/risk-alerts)
- Scenario Simulator (/api/scenario)
- Multi-City Comparison (/api/compare)
- WebSocket, caching, ML prediction
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import asyncio
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

from data_fetchers import (
    fetch_weather, fetch_fires, fetch_ocean_temp,
    fetch_carbon_intensity, fetch_turbulence, fetch_pollen,
    fetch_uhi, fetch_risk_score, fetch_alerts,
    fetch_historical
)

# -------------------------------------------------------------------
# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Load ML models (if available)
model = None
scaler = None
explainer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, scaler, explainer
    try:
        model = joblib.load('model.pkl')
        scaler = joblib.load('scaler.pkl')
        explainer = joblib.load('explainer.pkl')
        logger.info("ML models loaded successfully.")
    except Exception as e:
        logger.warning(f"Could not load models: {e}. Predictions will use fallback.")
    yield

app = FastAPI(title="EcoPulse API", version="3.3", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# In‑memory cache
cache = {}
def get_cached(key, ttl=300):
    if key in cache and (datetime.utcnow() - cache[key]['time']).seconds < ttl:
        return cache[key]['data']
    return None

def set_cache(key, data):
    cache[key] = {'data': data, 'time': datetime.utcnow()}

# -------------------------------------------------------------------
# Health
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# -------------------------------------------------------------------
# 10 Feature Endpoints (unchanged)
# -------------------------------------------------------------------
@app.get("/api/weather")
async def weather(lat: float = Query(...), lon: float = Query(...)):
    cache_key = f"weather_{lat}_{lon}"
    cached = get_cached(cache_key, ttl=600)
    if cached: return cached
    data = await fetch_weather(lat, lon)
    set_cache(cache_key, data)
    return data

@app.get("/api/fires")
async def fires(min_lon: float = -180, min_lat: float = -90,
                max_lon: float = 180, max_lat: float = 90):
    cache_key = f"fires_{min_lon}_{min_lat}_{max_lon}_{max_lat}"
    cached = get_cached(cache_key, ttl=300)
    if cached: return cached
    data = await fetch_fires((min_lon, min_lat, max_lon, max_lat))
    set_cache(cache_key, data)
    return data

@app.get("/api/ocean")
async def ocean(lat: float = Query(...), lon: float = Query(...)):
    cache_key = f"ocean_{lat}_{lon}"
    cached = get_cached(cache_key, ttl=3600)
    if cached: return cached
    data = await fetch_ocean_temp(lat, lon)
    set_cache(cache_key, data)
    return data

@app.get("/api/carbon")
async def carbon(country: str = "US"):
    cache_key = f"carbon_{country}"
    cached = get_cached(cache_key, ttl=1800)
    if cached: return cached
    data = await fetch_carbon_intensity(country)
    set_cache(cache_key, data)
    return data

@app.get("/api/turbulence")
async def turbulence(min_lon: float = -180, min_lat: float = -90,
                     max_lon: float = 180, max_lat: float = 90):
    cache_key = f"turbulence_{min_lon}_{min_lat}_{max_lon}_{max_lat}"
    cached = get_cached(cache_key, ttl=600)
    if cached: return cached
    data = await fetch_turbulence((min_lon, min_lat, max_lon, max_lat))
    set_cache(cache_key, data)
    return data

@app.get("/api/pollen")
async def pollen(lat: float = Query(...), lon: float = Query(...)):
    cache_key = f"pollen_{lat}_{lon}"
    cached = get_cached(cache_key, ttl=3600)
    if cached: return cached
    data = await fetch_pollen(lat, lon)
    set_cache(cache_key, data)
    return data

@app.get("/api/uhi")
async def uhi(city: str = Query(...)):
    cache_key = f"uhi_{city}"
    cached = get_cached(cache_key, ttl=1800)
    if cached: return cached
    data = await fetch_uhi(city)
    set_cache(cache_key, data)
    return data

@app.get("/api/risk-score")
async def risk_score(country: str = "US"):
    cache_key = f"risk_{country}"
    cached = get_cached(cache_key, ttl=3600)
    if cached: return cached
    data = await fetch_risk_score(country)
    set_cache(cache_key, data)
    return data

@app.get("/api/alerts")
async def alerts(min_lon: float = -180, min_lat: float = -90,
                 max_lon: float = 180, max_lat: float = 90):
    cache_key = f"alerts_{min_lon}_{min_lat}_{max_lon}_{max_lat}"
    cached = get_cached(cache_key, ttl=120)
    if cached: return cached
    data = await fetch_alerts((min_lon, min_lat, max_lon, max_lat))
    set_cache(cache_key, data)
    return data

# -------------------------------------------------------------------
# ML Prediction
# -------------------------------------------------------------------
@app.post("/api/predict")
async def predict_temperature(features: dict):
    if model is None:
        anomaly = (features.get('elevation', 0) * 0.01 -
                   features.get('urban_density', 0) * 0.02 +
                   features.get('veg_index', 0) * 0.5 -
                   features.get('water_dist', 0) * 0.1 +
                   np.sin(features.get('hour', 12)/24 * 2*np.pi) * 1.5)
        return {"anomaly": float(anomaly), "shap_values": None}
    input_df = pd.DataFrame([[
        features.get('elevation', 0),
        features.get('urban_density', 0),
        features.get('veg_index', 0),
        features.get('water_dist', 0),
        features.get('hour', 12)
    ]], columns=['elevation', 'urban_density', 'veg_index', 'water_dist', 'hour'])
    scaled = scaler.transform(input_df)
    pred = model.predict(scaled)[0]
    shap_vals = None
    if explainer:
        shap_vals = explainer.shap_values(scaled).tolist()
    return {"anomaly": float(pred), "shap_values": shap_vals}

# -------------------------------------------------------------------
# Analytics
# -------------------------------------------------------------------
@app.get("/api/analytics")
async def get_analytics():
    try:
        fires = await fetch_fires()
        alerts = await fetch_alerts()
        cities = [(30,70), (40,-100), (20,77), (35,105)]
        temps = []
        for lat, lon in cities:
            w = await fetch_weather(lat, lon)
            if w and w.get('current'):
                temps.append(w['current']['temperature_2m'])
        avg_temp = round(sum(temps)/len(temps),1) if temps else 20.0
        return {
            "total_fires": len(fires),
            "total_alerts": len(alerts),
            "avg_temperature": avg_temp,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {"total_fires": 0, "total_alerts": 0, "avg_temperature": 20.0, "timestamp": datetime.utcnow().isoformat()}

# -------------------------------------------------------------------
# Historical
# -------------------------------------------------------------------
@app.get("/api/historical")
async def get_historical(lat: float = Query(...), lon: float = Query(...),
                         days: int = Query(7, ge=1, le=30)):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    data = await fetch_historical(lat, lon, start_date.isoformat(), end_date.isoformat())
    return data


# -------------------------------------------------------------------
# Subscribe
# -------------------------------------------------------------------
subscribers = []
subscribers = {}  # email -> country

# ===================================================================
# SEND EMAIL FUNCTION
# ===================================================================
async def send_alert_email(email: str, alert_type: str, city: str, country: str, severity: str, description: str):
    """Send actual email notification using SMTP"""
    sender_email = os.getenv("EMAIL_SENDER", "")
    sender_password = os.getenv("EMAIL_PASSWORD", "")
    
    if not sender_email or not sender_password:
        print(f"⚠️ Email credentials not set. Would send: {alert_type} to {email}")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = f"⚠️ Climate Alert: {alert_type} in {city}, {country}"
        
        body = f"""
🌍 EcoPulse Climate Alert

📍 Location: {city}, {country}
⚠️ Alert Type: {alert_type}
🔴 Severity: {severity.upper()}
📝 Description: {description}

🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

💡 Action Required:
• Stay informed through local news
• Follow instructions from local authorities
• Check EcoPulse dashboard for updates: https://ecopulse-1-b2lm.onrender.com/

---
🌿 EcoPulse – Global Climate Intelligence Platform
"Know the climate. Act on it."
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✅ Email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False
    
@app.post("/api/subscribe")
async def subscribe(email: str = Query(...), country: str = Query("Pakistan")):
    subscribers[email] = country  
    return {"status": "subscribed", "email": email, "country": country}
@app.get("/api/subscribers")
async def list_subscribers():
    return {"subscribers": subscribers}

# ===================================================================
# TRIGGER ALERTS (Send emails to all subscribers)
# ===================================================================
@app.post("/api/trigger-alerts")
async def trigger_alerts():
    """Trigger alerts – send emails to all subscribers based on their country"""
    alerts = await fetch_alerts()
    if not alerts:
        return {"status": "no_alerts", "message": "No active alerts to send"}
    
    # Group alerts by country
    country_alerts = {}
    for alert in alerts:
        country = alert.get("country", "Unknown")
        if country not in country_alerts:
            country_alerts[country] = []
        country_alerts[country].append(alert)
    
    # Send emails to subscribers
    sent_count = 0
    for email, country in subscribers.items():
        if country in country_alerts:
            for alert in country_alerts[country]:
                await send_alert_email(
                    email,
                    alert['type'],
                    alert.get('city', 'Unknown'),
                    country,
                    alert['severity'],
                    alert.get('description', 'Weather alert')
                )
                sent_count += 1
                await asyncio.sleep(1)  # Rate limit (1 email per second)
    
    return {
        "status": "sent", 
        "count": sent_count,
        "message": f"Sent {sent_count} alerts to subscribers"
    }
# -------------------------------------------------------------------
# Chatbot
# -------------------------------------------------------------------
@app.get("/api/chat")
@app.post("/api/chat")
async def chat(message: str = Query(...)):
    msg = message.lower().strip()
    if not msg:
        return {"reply": "Please ask a question."}
    if "weather" in msg or "temperature" in msg:
        return {"reply": "🌤️ Click on the map to see current weather and 7‑day forecast."}
    elif "fire" in msg or "wildfire" in msg:
        return {"reply": "🔥 Check the Fires layer on the map for active wildfires."}
    elif "alert" in msg or "warning" in msg:
        return {"reply": "⚠️ Alerts are shown as bell icons. Click them for details."}
    elif "rain" in msg or "precipitation" in msg:
        return {"reply": "🌧️ Rain probability is shown in the popup when you click the map."}
    elif "carbon" in msg or "pollution" in msg:
        return {"reply": "💨 Carbon intensity is shown under the Carbon layer."}
    elif "pollen" in msg:
        return {"reply": "🌿 Pollen levels are shown under the Pollen layer."}
    elif "humidity" in msg:
        return {"reply": "💧 Humidity is displayed in the popup when you click the map."}
    else:
        return {"reply": "🤖 I'm your climate assistant. Try asking about weather, fires, alerts, rain, carbon, pollen, or humidity."}

# ===================================================================
# NEW: Predictive Risk Alerts
# ===================================================================
# Predefined cities for risk monitoring
RISK_CITIES = [
    {"name": "Karachi", "lat": 24.86, "lon": 67.01},
    {"name": "Lahore", "lat": 31.52, "lon": 74.36},
    {"name": "Islamabad", "lat": 33.68, "lon": 73.05},
    {"name": "Mumbai", "lat": 19.08, "lon": 72.88},
    {"name": "Delhi", "lat": 28.61, "lon": 77.23},
    {"name": "London", "lat": 51.51, "lon": -0.13},
    {"name": "New York", "lat": 40.71, "lon": -74.01},
    {"name": "Tokyo", "lat": 35.68, "lon": 139.76},
]

async def compute_city_risk(lat, lon):
    """Return fire_risk (0-3) and flood_risk (0-1) for a city."""
    try:
        w = await fetch_weather(lat, lon)
        if not w or not w.get('current'):
            return {"fire_risk": 0, "flood_risk": 0, "temp": 0, "humidity": 0, "wind": 0, "rain_prob": 0}
        temp = w['current']['temperature_2m']
        humidity = w['current']['relative_humidity_2m']
        wind = w['current']['wind_speed_10m']
        rain_prob = w.get('daily', {}).get('precipitation_probability_max', [0])[0] or 0
        fire = (1 if temp > 30 else 0) + (1 if humidity < 20 else 0) + (1 if wind > 20 else 0)
        flood = 1 if rain_prob > 80 else 0
        return {
            "fire_risk": min(fire, 3),
            "flood_risk": flood,
            "temp": temp,
            "humidity": humidity,
            "wind": wind,
            "rain_prob": rain_prob
        }
    except Exception as e:
        logger.warning(f"Risk compute error: {e}")
        return {"fire_risk": 0, "flood_risk": 0, "temp": 0, "humidity": 0, "wind": 0, "rain_prob": 0}

@app.get("/api/risk-alerts")
async def risk_alerts():
    """Return list of cities with risk scores >0."""
    results = []
    for city in RISK_CITIES:
        risks = await compute_city_risk(city['lat'], city['lon'])
        if risks['fire_risk'] > 0 or risks['flood_risk'] > 0:
            results.append({
                "name": city['name'],
                "lat": city['lat'],
                "lon": city['lon'],
                "fire_risk": risks['fire_risk'],
                "flood_risk": risks['flood_risk'],
                "temp": risks['temp'],
                "humidity": risks['humidity'],
                "wind": risks['wind'],
                "rain_prob": risks['rain_prob']
            })
    return {"alerts": results, "timestamp": datetime.utcnow().isoformat()}

# ===================================================================
# NEW: Scenario Simulator
# ===================================================================
@app.post("/api/scenario")
async def scenario_simulator(params: dict):
    """
    Accept: urban_density (0-100), veg_index (0-1), renewable_percent (0-100)
    Return predicted anomaly and carbon intensity change.
    """
    urban = params.get('urban_density', 50)
    veg = params.get('veg_index', 0.5)
    renewable = params.get('renewable_percent', 30)
    # Predict anomaly using ML (fallback linear)
    if model is None:
        anomaly = (urban * 0.01 - veg * 0.5) * 2  # rough
    else:
        input_df = pd.DataFrame([[50, urban, veg, 2, 12]],
                                columns=['elevation','urban_density','veg_index','water_dist','hour'])
        scaled = scaler.transform(input_df)
        anomaly = model.predict(scaled)[0]
    # Carbon intensity change: lower renewable -> higher intensity
    base_carbon = 400
    carbon_reduction = renewable * 3  # max 300 reduction
    new_carbon = max(100, base_carbon - carbon_reduction)
    return {
        "anomaly": float(anomaly),
        "carbon_intensity": new_carbon,
        "renewable_percent": renewable
    }

# ===================================================================
# NEW: Multi-City Comparison
# ===================================================================
CITY_COORDS = {
    "Karachi": (24.86, 67.01),
    "Lahore": (31.52, 74.36),
    "Islamabad": (33.68, 73.05),
    "Mumbai": (19.08, 72.88),
    "Delhi": (28.61, 77.23),
    "London": (51.51, -0.13),
    "New York": (40.71, -74.01),
    "Tokyo": (35.68, 139.76),
    "Sydney": (-33.87, 151.21),
    "Cape Town": (-33.92, 18.42),
}

async def get_city_metrics(city_name):
    lat, lon = CITY_COORDS[city_name]
    # Fetch multiple data points in parallel
    weather_task = fetch_weather(lat, lon)
    fires_task = fetch_fires()
    carbon_task = fetch_carbon_intensity("US")  # placeholder, use actual country later
    uhi_task = fetch_uhi(city_name)
    risk_task = fetch_risk_score("US")
    w = await weather_task
    fires = await fires_task
    carbon = await carbon_task
    uhi = await uhi_task
    risk = await risk_task
    # Count fires near city (within 2 degrees)
    near_fires = sum(1 for f in fires if abs(f['lat']-lat) < 2 and abs(f['lon']-lon) < 2)
    temp = w.get('current', {}).get('temperature_2m', 0) if w else 0
    return {
        "city": city_name,
        "temperature": round(temp, 1),
        "fires_nearby": near_fires,
        "carbon_intensity": carbon.get('carbon_intensity', 0) if carbon else 0,
        "uhi_intensity": uhi.get('uhi_intensity', 0) if uhi else 0,
        "risk_score": risk.get('score', 0) if risk else 0
    }

@app.post("/api/compare")
async def compare_cities(cities: List[str] = Query(...)):
    """Compare metrics for up to 5 cities."""
    if len(cities) > 5:
        raise HTTPException(400, "Maximum 5 cities allowed")
    results = []
    for city in cities:
        if city not in CITY_COORDS:
            continue
        metrics = await get_city_metrics(city)
        results.append(metrics)
    return {"comparison": results, "timestamp": datetime.utcnow().isoformat()}

# -------------------------------------------------------------------
# WebSocket
# -------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for conn in self.active_connections:
            try:
                await conn.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({"type": "init", "data": "Connected"}))
        while True:
            await asyncio.sleep(15)
            update = {
                "type": "update",
                "timestamp": datetime.utcnow().isoformat(),
                "fires": len(await fetch_fires()),
                "alerts": len(await fetch_alerts()),
            }
            await websocket.send_text(json.dumps(update))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# -------------------------------------------------------------------
# Serve frontend
# -------------------------------------------------------------------
@app.get("/")
async def serve_dashboard():
    return FileResponse("dashboard.html")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse("manifest.json")

@app.get("/sw.js")
async def serve_sw():
    return FileResponse("sw.js")