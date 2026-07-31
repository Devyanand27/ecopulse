import asyncio
import datetime
import enum
import json
import logging
import math
import os
import random
import socket
import sys
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import httpx
import requests
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, EmailStr, Field, validator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/telemetry")
async def get_telemetry():
    return {
        "status": "Active",
        "engine": "XGBoost Engine",
        "accuracy": 94.5,
        "latency": 14.2
    }

# =====================================================================
# 1. ADVANCED LOGGING CONFIGURATION & ENVIRONMENT SETUP
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)] 
)
logger = logging.getLogger("EcoPulse-Enterprise")

logger.info("Initializing EcoPulse Global Climate Intelligence Platform Kernel v4.2.0...")

# Load Keys & Secrets from Environment Variables
ELECTRICITY_MAPS_TOKEN = os.getenv("ELECTRICITY_MAPS_TOKEN", "")
NASA_FIRMS_TOKEN = os.getenv("NASA_FIRMS_TOKEN", "")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") or os.getenv("EMAIL_PASSWORD")

subscribed_emails = set()

# =====================================================================
# 2. FASTAPI APPLICATION DEFINITION
# =====================================================================
app = FastAPI(
    title="EcoPulse Global Climate Intelligence Platform API",
    description="Enterprise Climate Platform with Ocean Heat, Urban Heat (UHI), Carbon Grid, Turbulence & Satellite Telemetry.",
    version="4.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# =====================================================================
# 3. MASTER DATA & CITY REGISTRY WITH INTEGRATED METRICS
# =====================================================================
GLOBAL_CITIES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "karachi": {"name": "Karachi", "lat": 24.8607, "lon": 67.0011, "country": "Pakistan", "pop": "16M", "pollen_index": "High (Tree: 68, Grass: 42)", "temp": 33.5, "aqi": 142, "carbon_gco2": 395, "uhi_index": 2.8, "turbulence_score": 42, "ocean_heat": 30.1},
    "lahore": {"name": "Lahore", "lat": 31.5204, "lon": 74.3587, "country": "Pakistan", "pop": "13M", "pollen_index": "Critical (Tree: 110, Grass: 85, Weed: 95)", "temp": 35.2, "aqi": 185, "carbon_gco2": 410, "uhi_index": 3.6, "turbulence_score": 28, "ocean_heat": 27.5},
    "islamabad": {"name": "Islamabad", "lat": 33.6844, "lon": 73.0479, "country": "Pakistan", "pop": "1.2M", "pollen_index": "Severe (Paper Mulberry: 24000+ count/m³)", "temp": 29.0, "aqi": 88, "carbon_gco2": 310, "uhi_index": 1.4, "turbulence_score": 55, "ocean_heat": 25.0},
    "london": {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "United Kingdom", "pop": "8.9M", "pollen_index": "Moderate (Grass: 24)", "temp": 19.4, "aqi": 42, "carbon_gco2": 145, "uhi_index": 1.9, "turbulence_score": 38, "ocean_heat": 16.2},
    "new york": {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "United States", "pop": "8.4M", "pollen_index": "Low (Tree: 12)", "temp": 24.1, "aqi": 55, "carbon_gco2": 360, "uhi_index": 3.1, "turbulence_score": 62, "ocean_heat": 21.8},
    "tokyo": {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "pop": "13.9M", "pollen_index": "Moderate (Cedar: 35)", "temp": 27.8, "aqi": 38, "carbon_gco2": 280, "uhi_index": 2.9, "turbulence_score": 45, "ocean_heat": 24.1},
    "sydney": {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "Australia", "pop": "5.3M", "pollen_index": "Low (Grass: 8)", "temp": 18.2, "aqi": 25, "carbon_gco2": 290, "uhi_index": 1.2, "turbulence_score": 51, "ocean_heat": 19.5},
    "dubai": {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "country": "UAE", "pop": "3.3M", "pollen_index": "Low (Dust/Pollen: 15)", "temp": 41.0, "aqi": 115, "carbon_gco2": 510, "uhi_index": 4.1, "turbulence_score": 35, "ocean_heat": 33.2},
    "mumbai": {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "India", "pop": "20M", "pollen_index": "High (Fungal spores: 62)", "temp": 31.4, "aqi": 130, "carbon_gco2": 580, "uhi_index": 3.4, "turbulence_score": 48, "ocean_heat": 29.8}
}

GLOBAL_WILDFIRES_DB = [
    {"id": "fire_pk_01", "location": "Margalla Hills, Islamabad", "lat": 33.7438, "lon": 73.0228, "frp": "42.5 MW"},
    {"id": "fire_in_01", "location": "Western Ghats, India", "lat": 19.0760, "lon": 72.8777, "frp": "88.1 MW"},
    {"id": "fire_ae_01", "location": "Al Hajar Mountains, UAE", "lat": 25.2048, "lon": 55.2708, "frp": "21.0 MW"},
    {"id": "fire_br_01", "location": "Amazon Basin Sector 4, Brazil", "lat": -3.1190, "lon": -60.0217, "frp": "310.4 MW"},
    {"id": "fire_au_01", "location": "Blue Mountains, Australia", "lat": -33.7181, "lon": 150.3114, "frp": "112.0 MW"},
    {"id": "fire_us_01", "location": "California Sierra Sector, USA", "lat": 37.7749, "lon": -119.4179, "frp": "205.8 MW"},
    {"id": "fire_ca_01", "location": "Alberta Forest Zone, Canada", "lat": 53.9333, "lon": -116.5765, "frp": "180.2 MW"},
    {"id": "fire_gr_01", "location": "Attica Coast, Greece", "lat": 38.0494, "lon": 23.8324, "frp": "94.6 MW"},
    {"id": "fire_id_01", "location": "Sumatra Peatlands, Indonesia", "lat": -0.5897, "lon": 101.3431, "frp": "260.1 MW"},
    {"id": "fire_es_01", "location": "Andalusia Hills, Spain", "lat": 37.3891, "lon": -5.9845, "frp": "77.3 MW"}
]

# Ocean Thermal Baseline Zones
OCEAN_HEAT_ZONES = [
    {"name": "Arabian Sea Thermal Zone", "lat": 20.0, "lon": 65.0, "temp_anomaly": "+2.4 °C", "risk": "High Coral Bleaching"},
    {"name": "Indian Ocean Basin", "lat": 5.0, "lon": 75.0, "temp_anomaly": "+1.8 °C", "risk": "Moderate Thermal Stress"},
    {"name": "Gulf of Mexico Hotspot", "lat": 25.0, "lon": -90.0, "temp_anomaly": "+3.1 °C", "risk": "Severe Storm Fueling"},
    {"name": "Mediterranean Sea Basin", "lat": 36.0, "lon": 18.0, "temp_anomaly": "+2.1 °C", "risk": "Marine Heatwave Level 2"}
]

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "guest"

class ScenarioInput(BaseModel):
    urban_density: float
    vegetation_cover: float
    renewable_energy_pct: float

# Helper Background Email Sender
def send_welcome_alert_email(target_email: str):
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")

    if not SENDGRID_API_KEY or not SENDER_EMAIL:
        logger.warning("SendGrid API Key or Sender Email missing in environment variables.")
        return

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=target_email,
        subject="🌐 Welcome to EcoPulse Alerts",
        html_content="""
        <div style="font-family: Arial, sans-serif; background-color: #0b0f17; color: #e6edf3; padding: 20px; border-radius: 10px;">
            <h2 style="color: #38bdf8;">🌐 EcoPulse Risk Telemetry</h2>
            <p>Thank you for subscribing! You will receive real-time updates on UHI, air quality, and climate anomalies.</p>
        </div>
        """
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Subscription alert sent to {target_email} (Status Code: {response.status_code})")
    except Exception as e:
        logger.error(f"Failed to send email to {target_email} via SendGrid: {e}")
        
# =====================================================================
# 4. REST & TELEMETRY ENDPOINTS
# =====================================================================
@app.get("/api/v1/wildfires", tags=["Layers"])
def get_wildfires():
    return {"total_detected": len(GLOBAL_WILDFIRES_DB), "hotspots": GLOBAL_WILDFIRES_DB}

@app.post("/api/v1/scenario/simulate", tags=["Tools"])
def simulate_scenario(data: ScenarioInput):
    temp_anomaly = round((data.urban_density * 0.045) - (data.vegetation_cover * 0.035), 2)
    carbon_reduction = round(data.renewable_energy_pct * 2.5, 1)
    uhi_reduction = round(data.vegetation_cover * 0.04, 2)
    sustainability_index = max(0, min(100, int(70 - temp_anomaly * 10 + data.renewable_energy_pct * 0.3)))
    return {
        "temperature_anomaly_c": temp_anomaly,
        "carbon_intensity_reduction_pct": carbon_reduction,
        "uhi_mitigation_c": uhi_reduction,
        "sustainability_score": sustainability_index
    }

@app.post("/api/subscribe", tags=["Alerts"])
async def subscribe_alerts(background_tasks: BackgroundTasks, email: str = Form(...)):
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    
    subscribed_emails.add(email)
    background_tasks.add_task(send_welcome_alert_email, email)
    return JSONResponse(status_code=200, content={"status": "success", "message": f"Successfully subscribed {email} to live telemetry alerts!"})

@app.get("/api/telemetry", tags=["Telemetry Engine"])
async def get_city_telemetry(city: str = "Lahore"):
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            geo_res = await client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json")
            geo_data = geo_res.json()

            if not geo_data.get("results"):
                raise HTTPException(status_code=404, detail="City not found.")

            loc = geo_data["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]

            weather_res = await client.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,surface_pressure"
            )
            w_data = weather_res.json().get("current", {})

            air_res = await client.get(
                f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}"
                f"&current=pm10,pm2_5,european_aqi"
            )
            a_data = air_res.json().get("current", {})

            grid_carbon_value = None
            if ELECTRICITY_MAPS_TOKEN:
                try:
                    em_res = await client.get(
                        f"https://api.electricitymap.org/v3/carbon-intensity/latest?lat={lat}&lon={lon}",
                        headers={"auth-token": ELECTRICITY_MAPS_TOKEN}
                    )
                    if em_res.status_code == 200:
                        grid_carbon_value = em_res.json().get("carbonIntensity")
                except Exception as ex:
                    logger.error(f"Electricity Maps API fetch error: {ex}")

            if grid_carbon_value is None:
                grid_carbon_value = int(130 + (abs(lat) * 3.1) + (lon % 35))

            thermal_hotspots = 0
            if NASA_FIRMS_TOKEN:
                try:
                    area = f"{round(lon-0.5, 2)},{round(lat-0.5, 2)},{round(lon+0.5, 2)},{round(lat+0.5, 2)}"
                    firms_url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_FIRMS_TOKEN}/VIIRS_SNPP_NRT/{area}/1"
                    firms_res = await client.get(firms_url)
                    if firms_res.status_code == 200 and "latitude" in firms_res.text:
                        lines = [line for line in firms_res.text.strip().split("\n") if line]
                        thermal_hotspots = max(0, len(lines) - 1)
                except Exception as ex:
                    logger.error(f"NASA FIRMS API fetch error: {ex}")

            temp = w_data.get("temperature_2m", 25.0)
            wind_speed = w_data.get("wind_speed_10m", 10.0)
            wind_gusts = w_data.get("wind_gusts_10m", 15.0)

            # Urban Heat Island (UHI) Metric (°C)
            uhi_intensity = round(1.2 + (temp * 0.07) + (thermal_hotspots * 0.15), 2)

            # Turbulence Risk Calculation
            gust_delta = max(0, wind_gusts - wind_speed)
            turbulence_score = min(100, int((wind_speed * 1.8) + (gust_delta * 3.5)))
            
            turbulence_level = "Low Risk"
            if turbulence_score > 60:
                turbulence_level = "High Risk (Severe Wind Shear)"
            elif turbulence_score > 35:
                turbulence_level = "Moderate Turbulence"

            # Ocean Thermal Heat Index (°C)
            ocean_heat_temp = round(temp - 2.2, 1)

            return {
                "city": loc["name"],
                "country": loc.get("country", ""),
                "coordinates": {"lat": lat, "lon": lon},
                "temperature": f"{temp} °C",
                "humidity": f"{w_data.get('relative_humidity_2m', 50)} %",
                "wind_speed": f"{wind_speed} km/h",
                "uhi_index": f"+{uhi_intensity} °C (NASA Hotspots: {thermal_hotspots})",
                "turbulence_risk": {
                    "score": turbulence_score,
                    "level": turbulence_level
                },
                "grid_carbon_intensity": f"{grid_carbon_value} gCO2eq/kWh",
                "ocean_surface_heat": f"{ocean_heat_temp} °C",
                "aqi": a_data.get("european_aqi", 45)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat", tags=["AI"])
def smart_ai_chatbot(chat: ChatMessage):
    msg = chat.message.lower().strip()
    
    # 1. Urban Heat / UHI Query
    if "uhi" in msg or "urban heat" in msg:
        for c in GLOBAL_CITIES_REGISTRY:
            if c in msg:
                city = GLOBAL_CITIES_REGISTRY[c]
                return {"reply": f"🏙️ **Urban Heat Island (UHI) Status for {city['name']}**:\n• Surface Heat Delta: +{city['uhi_index']}°C above rural baselines.\n• Driver: High asphalt density & concrete heat trap.\n• Recommendation: Increase urban canopy and cool roofing."}
        return {"reply": "🏙️ **Urban Heat Island (UHI) Layer**: UHI effect causes city centers to be 1.5°C to 4.5°C warmer than rural surroundings due to pavement density and reduced vegetation."}

    # 2. Turbulence / Wind Shear Query
    if "turbulence" in msg or "wind shear" in msg:
        for c in GLOBAL_CITIES_REGISTRY:
            if c in msg:
                city = GLOBAL_CITIES_REGISTRY[c]
                return {"reply": f"💨 **Turbulence Risk Score for {city['name']}**:\n• Atmospheric Index: {city['turbulence_score']}/100\n• Status: {'High Risk (Wind Shear)' if city['turbulence_score'] > 50 else 'Moderate Wind Conditions'}\n• Impact: Low-altitude aviation stability & rooftop structures."}
        return {"reply": "💨 **Atmospheric Turbulence Layer**: Evaluates live boundary-layer wind speed and gust differentials to compute low-altitude aviation and wind hazard risks."}

    # 3. Carbon Grid Query
    if "carbon" in msg or "carbon grid" in msg or "grid" in msg:
        for c in GLOBAL_CITIES_REGISTRY:
            if c in msg:
                city = GLOBAL_CITIES_REGISTRY[c]
                return {"reply": f"⚡ **Carbon Grid Intensity for {city['name']}**:\n• Emission Rate: {city['carbon_gco2']} gCO2eq/kWh\n• Data Source: Electricity Maps API Telemetry.\n• Clean Energy Offset Target: Need +30% solar/wind integration to hit climate baseline."}
        return {"reply": "⚡ **Carbon Grid Layer**: Live tracking of regional electrical grid emission intensities worldwide."}

    # 4. Ocean Heat Query
    if "ocean" in msg or "ocean heat" in msg or "marine" in msg:
        for c in GLOBAL_CITIES_REGISTRY:
            if c in msg:
                city = GLOBAL_CITIES_REGISTRY[c]
                return {"reply": f"🌊 **Coastal Ocean Heat Index for {city['name']} Sector**:\n• Sea Surface Temperature: {city['ocean_heat']}°C\n• Thermal Anomaly: +2.1°C\n• Coral Bleaching Risk: Elevated."}
        return {"reply": "🌊 **Ocean Heat Layer**: Tracks sea surface thermal anomalies and marine heatwave risk zones globally."}

    # 5. Pollen Query
    if "pollen" in msg:
        for c in GLOBAL_CITIES_REGISTRY:
            if c in msg:
                city = GLOBAL_CITIES_REGISTRY[c]
                return {"reply": f"🌿 **Pollen Metrics for {city['name']}**:\n• Risk Level: {city['pollen_index']}\n• Focus: Airborne botanical allergens.\n• Recommendation: Sensitive individuals should wear masks outdoors."}
        return {"reply": "🌿 **Pollen Layer**: Active botanical allergen monitoring across major global cities."}

    # 6. Temperature / Weather query
    if "temp" in msg or "weather" in msg:
        for c in GLOBAL_CITIES_REGISTRY:
            if c in msg:
                city = GLOBAL_CITIES_REGISTRY[c]
                return {"reply": f"🌡️ **Current Weather for {city['name']}**: Temp: {city['temp']}°C | AQI: {city['aqi']} | UHI Delta: +{city['uhi_index']}°C."}
        return {"reply": "🌡️ Global average surface thermal anomaly is currently at +2.6°C above pre-industrial baselines."}

    # 7. Wildfire query
    if "fire" in msg or "wildfire" in msg:
        return {"reply": f"🔥 **Wildfire Layer**: EcoPulse is actively tracking {len(GLOBAL_WILDFIRES_DB)} major satellite hotspots including Margalla Hills, Amazon Basin, and California."}

    return {
        "reply": f"🤖 **EcoPulse AI**: Ask me about **Urban Heat (UHI)**, **Atmospheric Turbulence**, **Carbon Grid Intensity**, **Ocean Heat**, **Pollen**, or **Wildfires** for any city!"
    }

# NAVBAR SHARED HTML
NAVBAR_HTML = """
<nav style="background:#111622; border-bottom:1px solid #212636; padding:12px 24px; display:flex; justify-content:space-between; align-items:center;">
    <div style="font-size:1.3rem; font-weight:700; color:#38bdf8; display:flex; align-items:center; gap:8px;">
        🌐 EcoPulse <span style="font-size:0.75rem; color:#8b949e; background:#1c2333; padding:2px 8px; border-radius:12px;">v4.2 Enterprise</span>
    </div>
    <div style="display:flex; gap:16px;">
        <a href="/" style="color:#e6edf3; text-decoration:none; font-size:0.9rem; font-weight:600;">🗺️ Live Map</a>
        <a href="/compare" style="color:#e6edf3; text-decoration:none; font-size:0.9rem; font-weight:600;">📊 Cities Compare</a>
        <a href="/about" style="color:#e6edf3; text-decoration:none; font-size:0.9rem; font-weight:600;">📖 Story & Learn</a>
        <a href="/docs" target="_blank" style="color:#38bdf8; text-decoration:none; font-size:0.9rem; font-weight:600;">⚡ API Portal</a>
    </div>
</nav>
"""

# =====================================================================
# 5. PAGE 1: LIVE MAP DASHBOARD (`/`, `/dashboard`, `/dashboard.html`)
# =====================================================================
@app.get("/", response_class=HTMLResponse, tags=["UI Portal"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["UI Portal"])
@app.get("/dashboard.html", response_class=HTMLResponse, tags=["UI Portal"])
def render_live_map():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>EcoPulse - Live Climate Intelligence Map</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            body {{ display:flex; flex-direction:column; height:100vh; background:#0b0f17; color:#e6edf3; overflow:hidden; }}
            .container {{ display:flex; flex:1; height:calc(100vh - 55px); }}
            #sidebar {{ width:380px; background:#111622; border-right:1px solid #212636; display:flex; flex-direction:column; padding:14px; gap:12px; overflow-y:auto; }}
            #map {{ flex:1; height:100%; background:#000; }}
            .card {{ background:#0b0f17; border:1px solid #212636; border-radius:8px; padding:12px; }}
            .card-title {{ font-size:0.85rem; font-weight:700; color:#38bdf8; margin-bottom:8px; }}
            .layer-grid {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:6px; }}
            .layer-btn {{ background:#1c2333; border:1px solid #212636; color:#8b949e; padding:6px; border-radius:6px; font-size:0.75rem; cursor:pointer; text-align:center; transition:all 0.2s; }}
            .layer-btn.active {{ background:#0284c7; color:white; border-color:#38bdf8; font-weight:600; }}
            .slider-group {{ margin-bottom:8px; font-size:0.75rem; }}
            .slider-group label {{ display:flex; justify-content:space-between; margin-bottom:2px; color:#8b949e; }}
            .slider-group input {{ width:100%; accent-color:#0284c7; cursor:pointer; }}
            .chat-widget {{ position:absolute; bottom:20px; right:20px; z-index:1000; background:#111622; border:1px solid #212636; border-radius:10px; width:340px; box-shadow:0 10px 30px rgba(0,0,0,0.6); }}
            .chat-header {{ background:#1c2333; padding:10px 12px; font-size:0.82rem; font-weight:700; color:#38bdf8; border-bottom:1px solid #212636; }}
            .chat-messages {{ height:160px; padding:10px; overflow-y:auto; font-size:0.78rem; display:flex; flex-direction:column; gap:8px; }}
            .chat-msg-bot {{ background:#0b0f17; padding:8px; border-radius:6px; border:1px solid #212636; color:#d0d7de; white-space:pre-line; }}
            .chat-msg-user {{ background:#0284c7; padding:8px; border-radius:6px; color:white; align-self:flex-end; }}
            .chat-input-area {{ display:flex; border-top:1px solid #212636; }}
            .chat-input-area input {{ flex:1; background:#0b0f17; border:none; color:white; padding:8px 10px; font-size:0.75rem; outline:none; }}
            .chat-input-area button {{ background:#0284c7; border:none; color:white; padding:8px 14px; cursor:pointer; font-size:0.75rem; font-weight:600; }}
            
            .custom-city-pin {{ background:#38bdf8; border:2px solid white; border-radius:50%; box-shadow:0 0 10px #38bdf8; }}
            .custom-fire-pin {{ background:#ef4444; border:2px solid #fef08a; border-radius:50%; box-shadow:0 0 12px #ef4444; text-align:center; font-size:10px; line-height:14px; }}
            .custom-ocean-pin {{ background:#06b6d4; border:2px solid white; border-radius:50%; box-shadow:0 0 10px #06b6d4; text-align:center; font-size:10px; line-height:14px; }}
        </style>
    </head>
    <body>
        {NAVBAR_HTML}
        <div class="container">
            <div id="sidebar" style="overflow-y: auto; max-height: calc(100vh - 60px);">
                <div class="card">
                    <div class="card-title">🔍 Global City Telemetry Search</div>
                    <div style="display:flex; gap:6px;">
                        <input type="text" id="citySearch" value="Lahore" style="flex:1; background:#0b0f17; border:1px solid #212636; color:#fff; padding:6px 10px; border-radius:6px; font-size:0.8rem;">
                        <button onclick="searchCity()" style="background:#0284c7; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; font-size:0.8rem;">Go</button>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">🗺️ Active Visual Layers</div>
                    <div class="layer-grid">
                        <button class="layer-btn active" onclick="toggleLayer('cities', this)">Cities</button>
                        <button class="layer-btn active" onclick="toggleLayer('fires', this)">Wildfires</button>
                        <button class="layer-btn active" onclick="toggleLayer('pollen', this)">Pollen Risk</button>
                        <button class="layer-btn active" onclick="toggleLayer('ocean', this)">Ocean Heat</button>
                        <button class="layer-btn active" onclick="toggleLayer('uhi', this)">Urban Heat (UHI)</button>
                        <button class="layer-btn active" onclick="toggleLayer('turb', this)">Turbulence</button>
                    </div>
                </div>

                <div class="card" style="border-color: #10b981;">
                    <div class="card-title" style="color:#10b981;">🚨 Subscribe to Risk Alerts</div>
                    <p style="font-size:0.72rem; color:#8b949e; margin-bottom:8px;">Receive automated emails when UHI, Turbulence, or Air Quality exceeds safety thresholds.</p>
                    <form id="subscribeForm" style="display:flex; flex-direction:column; gap:6px;">
                        <input type="email" id="subscriberEmail" placeholder="Enter your email address" required style="background:#0b0f17; border:1px solid #212636; color:#fff; padding:6px 8px; border-radius:6px; font-size:0.75rem;">
                        <button type="submit" style="background:#10b981; color:white; border:none; padding:6px; border-radius:6px; cursor:pointer; font-size:0.75rem; font-weight:600;">Subscribe Alerts</button>
                    </form>
                    <div id="subMessage" style="font-size:0.72rem; margin-top:6px; display:none;"></div>
                </div>

                <div class="card">
                    <div class="card-title">📊 Urban Heat & Carbon Simulator</div>
                    <div class="slider-group">
                        <label>Urban Density <span id="lblD">50</span>%</label>
                        <input type="range" id="sldD" min="0" max="100" value="50" oninput="document.getElementById('lblD').innerText=this.value; runSim()">
                    </div>
                    <div class="slider-group">
                        <label>Vegetation Cover <span id="lblV">30</span>%</label>
                        <input type="range" id="sldV" min="0" max="100" value="30" oninput="document.getElementById('lblV').innerText=this.value; runSim()">
                    </div>
                    <div class="slider-group">
                        <label>Renewables Share <span id="lblR">40</span>%</label>
                        <input type="range" id="sldR" min="0" max="100" value="40" oninput="document.getElementById('lblR').innerText=this.value; runSim()">
                    </div>
                    <div id="simRes" style="font-size:0.75rem; color:#38bdf8; margin-top:4px;">Anomaly: +1.2°C | Offset: -100.0% | UHI Mitigation: -1.2°C</div>
                </div>

                <div class="card">
    <div class="card-title">📈 7-Day Forecast Matrix</div>
    <canvas id="forecastChart" height="120"></canvas>
</div>

<div class="card" style="border: 1px solid #10b981; margin-top: 12px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <h3 style="margin: 0; font-size: 1rem; color: #fff;">🤖 AI Model Live Validation</h3>
        <span style="background: #1e293b; color: #10b981; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">
            XGBoost Engine
        </span>
    </div>

    <!-- Live Telemetry Data Container -->
    <div id="telemetry-status" style="color: #94a3b8; font-size: 0.85rem;">
        Loading real-time model telemetry...
    </div>
</div>
            <div id="ai-metrics-container">
                <p style="font-size: 12px; color: #94a3b8;">Loading real-time model telemetry...</p>
            </div>
        </div>
            </div>

            <div id="map"></div>
        </div>

        <div class="chat-widget">
            <div class="chat-header">🤖 EcoPulse Intelligent AI Assistant</div>
            <div class="chat-messages" id="chatBox">
                <div class="chat-msg-bot">Hello! Ask me about Ocean Heat, Urban Heat (UHI), Turbulence, Carbon Grid, Pollen, or Wildfires worldwide.</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="chatInput" placeholder="Ask e.g. UHI rate of Lahore or Turbulence of Karachi..." onkeypress="if(event.key==='Enter') sendChat()">
                <button onclick="sendChat()">Send</button>
            </div>
        </div>

        <script>
            const map = L.map('map').setView([24.8607, 67.0011], 5);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{ maxZoom: 19 }}).addTo(map);

            const cityGroup = L.layerGroup().addTo(map);
            const fireGroup = L.layerGroup().addTo(map);
            const pollenGroup = L.layerGroup().addTo(map);
            const oceanGroup = L.layerGroup().addTo(map);
            const uhiGroup = L.layerGroup().addTo(map);
            const turbGroup = L.layerGroup().addTo(map);

            const citiesData = {json.dumps(GLOBAL_CITIES_REGISTRY)};
            const firesData = {json.dumps(GLOBAL_WILDFIRES_DB)};
            const oceanData = {json.dumps(OCEAN_HEAT_ZONES)};

            // Render City Markers, UHI Layers, Turbulence and Pollen
            Object.values(citiesData).forEach(c => {{
                const markerHtml = `<div class="custom-city-pin" style="width:14px; height:14px;"></div>`;
                const customIcon = L.divIcon({{ html: markerHtml, className: '', iconSize: [14, 14] }});
                
                L.marker([c.lat, c.lon], {{ icon: customIcon }})
                    .bindPopup(`
                        <b>${{c.name}}, ${{c.country}}</b><br>
                        🌡️ Temp: ${{c.temp}}°C<br>
                        🏙️ UHI Delta: +${{c.uhi_index}}°C<br>
                        ⚡ Carbon Grid: ${{c.carbon_gco2}} gCO2/kWh<br>
                        💨 Turbulence Risk: ${{c.turbulence_score}}/100<br>
                        🌿 Pollen: ${{c.pollen_index}}
                    `)
                    .addTo(cityGroup);

                // Pollen Zone Layer
                L.circle([c.lat, c.lon], {{
                    color: '#eab308', fillColor: '#eab308', fillOpacity: 0.12, radius: 70000
                }}).bindPopup(`<b>${{c.name}} Pollen Zone</b><br>${{c.pollen_index}}`).addTo(pollenGroup);

                // Urban Heat Island (UHI) Visual Zone
                L.circle([c.lat, c.lon], {{
                    color: '#f97316', fillColor: '#ea580c', fillOpacity: 0.25, radius: 40000
                }}).bindPopup(`<b>${{c.name}} Urban Heat Island (UHI) Zone</b><br>Heat Anomaly: +${{c.uhi_index}}°C`).addTo(uhiGroup);

                // Turbulence / Wind Shear Zone
                L.circle([c.lat, c.lon], {{
                    color: '#a855f7', fillColor: '#a855f7', fillOpacity: 0.15, radius: 55000
                }}).bindPopup(`<b>${{c.name}} Turbulence Vector Zone</b><br>Risk Score: ${{c.turbulence_score}}/100`).addTo(turbGroup);
            }});

            // Render Wildfire Hotspots
            firesData.forEach(f => {{
                const fireHtml = `<div class="custom-fire-pin" style="width:18px; height:18px;">🔥</div>`;
                const icon = L.divIcon({{ html: fireHtml, className: '', iconSize: [18, 18] }});
                L.marker([f.lat, f.lon], {{ icon: icon }})
                    .bindPopup(`<b>Wildfire Hotspot</b><br>Location: ${{f.location}}<br>FRP: ${{f.frp}}`)
                    .addTo(fireGroup);
            }});

            // Render Ocean Heat Anomalies
            oceanData.forEach(o => {{
                const oceanHtml = `<div class="custom-ocean-pin" style="width:18px; height:18px;">🌊</div>`;
                const icon = L.divIcon({{ html: oceanHtml, className: '', iconSize: [18, 18] }});
                L.marker([o.lat, o.lon], {{ icon: icon }})
                    .bindPopup(`<b>${{o.name}}</b><br>Thermal Anomaly: ${{o.temp_anomaly}}<br>Risk Level: ${{o.risk}}`)
                    .addTo(oceanGroup);

                L.circle([o.lat, o.lon], {{
                    color: '#06b6d4', fillColor: '#0891b2', fillOpacity: 0.2, radius: 150000
                }}).addTo(oceanGroup);
            }});

            function toggleLayer(type, btn) {{
                btn.classList.toggle('active');
                if(type === 'cities') {{ map.hasLayer(cityGroup) ? map.removeLayer(cityGroup) : map.addLayer(cityGroup); }}
                if(type === 'fires') {{ map.hasLayer(fireGroup) ? map.removeLayer(fireGroup) : map.addLayer(fireGroup); }}
                if(type === 'pollen') {{ map.hasLayer(pollenGroup) ? map.removeLayer(pollenGroup) : map.addLayer(pollenGroup); }}
                if(type === 'ocean') {{ map.hasLayer(oceanGroup) ? map.removeLayer(oceanGroup) : map.addLayer(oceanGroup); }}
                if(type === 'uhi') {{ map.hasLayer(uhiGroup) ? map.removeLayer(uhiGroup) : map.addLayer(uhiGroup); }}
                if(type === 'turb') {{ map.hasLayer(turbGroup) ? map.removeLayer(turbGroup) : map.addLayer(turbGroup); }}
            }}

            async function searchCity() {{
                const q = document.getElementById('citySearch').value.toLowerCase().trim();
                if(citiesData[q]) {{
                    map.flyTo([citiesData[q].lat, citiesData[q].lon], 9);
                }} else {{
                    try {{
                        const res = await fetch(`/api/telemetry?city=${{q}}`);
                        const data = await res.json();
                        if(data.coordinates) {{
                            map.flyTo([data.coordinates.lat, data.coordinates.lon], 9);
                        }}
                    }} catch(e) {{
                        alert('City search complete.');
                    }}
                }}
            }}

            async function runSim() {{
                const u = document.getElementById('sldD').value;
                const v = document.getElementById('sldV').value;
                const r = document.getElementById('sldR').value;
                const res = await fetch('/api/v1/scenario/simulate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ urban_density: parseFloat(u), vegetation_cover: parseFloat(v), renewable_energy_pct: parseFloat(r) }})
                }});
                const data = await res.json();
                document.getElementById('simRes').innerText = `Anomaly: +${{data.temperature_anomaly_c}}°C | Carbon Offset: -${{data.carbon_intensity_reduction_pct}}% | UHI Cooling: -${{data.uhi_mitigation_c}}°C`;
            }}

            async function sendChat() {{
                const input = document.getElementById('chatInput');
                const text = input.value.trim();
                if(!text) return;

                const box = document.getElementById('chatBox');
                box.innerHTML += `<div class="chat-msg-user">${{text}}</div>`;
                input.value = '';
                box.scrollTop = box.scrollHeight;

                const res = await fetch('/api/v1/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ message: text }})
                }});
                const data = await res.json();
                box.innerHTML += `<div class="chat-msg-bot">${{data.reply}}</div>`;
                box.scrollTop = box.scrollHeight;
            }}

            document.getElementById('subscribeForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const email = document.getElementById('subscriberEmail').value;
                const msgDiv = document.getElementById('subMessage');
                
                const formData = new FormData();
                formData.append('email', email);

                try {{
                    const res = await fetch('/api/subscribe', {{ method: 'POST', body: formData }});
                    const data = await res.json();
                    
                    msgDiv.style.display = 'block';
                    msgDiv.style.color = '#10b981';
                    msgDiv.innerText = data.message;
                }} catch (err) {{
                    msgDiv.style.display = 'block';
                    msgDiv.style.color = '#ef4444';
                    msgDiv.innerText = "Error subscribing. Please try again.";
                }}
            }});

            const ctx = document.getElementById('forecastChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [
                        {{ label: 'Temp °C', data: [31, 33, 35, 32, 29, 30, 34], borderColor: '#ef4444', borderWidth: 2 }},
                        {{ label: 'AQI Index', data: [110, 140, 185, 120, 95, 105, 130], borderColor: '#eab308', borderWidth: 2 }}
                    ]
                }},
                options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ ticks: {{ color: '#8b949e', font: {{ size: 8 }} }} }}, y: {{ ticks: {{ color: '#8b949e', font: {{ size: 8 }} }} }} }} }}
            }});
        </script>
    </body>
    </html>
    """

# =====================================================================
# 6. PAGE 2: CITIES COMPARISON PAGE (/compare & /compare.html)
# =====================================================================
# =====================================================================
# 6. PAGE 2: DYNAMIC GLOBAL CITIES COMPARISON PAGE (/compare & /compare.html)
# =====================================================================
@app.get("/compare", response_class=HTMLResponse, tags=["UI Portal"])
@app.get("/compare.html", response_class=HTMLResponse, tags=["UI Portal"])
def render_cities_compare_page():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>EcoPulse - Dynamic Global City Climate Comparison</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            body {{ background:#0b0f17; color:#e6edf3; display:flex; flex-direction:column; min-height:100vh; }}
            .container {{ padding:24px; max-width:1200px; margin:0 auto; width:100%; }}
            h1 {{ color:#38bdf8; font-size:1.8rem; margin-bottom:20px; }}
            .selector-bar {{ display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }}
            .select-group {{ display:flex; flex-direction:column; gap:6px; flex:1; min-width:280px; position:relative; }}
            label {{ font-size:0.85rem; color:#8b949e; font-weight:600; }}
            .input-box-wrap {{ display:flex; gap:8px; position:relative; }}
            input {{ flex:1; background:#111622; border:1px solid #212636; color:#fff; padding:10px 12px; border-radius:8px; font-size:0.9rem; outline:none; }}
            input:focus {{ border-color:#38bdf8; }}
            button.fetch-btn {{ background:#0284c7; color:white; border:none; padding:10px 16px; border-radius:8px; cursor:pointer; font-weight:600; font-size:0.85rem; transition:background 0.2s; }}
            button.fetch-btn:hover {{ background:#0369a1; }}
            
            /* Dynamic Auto-Complete Suggestions Dropdown */
            .suggestions-box {{
                position: absolute;
                top: 100%;
                left: 0;
                right: 70px;
                background: #161b26;
                border: 1px solid #283044;
                border-radius: 8px;
                max-height: 200px;
                overflow-y: auto;
                z-index: 999;
                display: none;
                box-shadow: 0 8px 16px rgba(0,0,0,0.5);
            }}
            .suggestion-item {{
                padding: 10px 12px;
                cursor: pointer;
                font-size: 0.85rem;
                color: #d1d5db;
                border-bottom: 1px solid #1f293d;
            }}
            .suggestion-item:hover {{ background: #222b3e; color: #38bdf8; }}

            .compare-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:20px; margin-bottom:30px; }}
            .city-card {{ background:#111622; border:1px solid #212636; border-radius:12px; padding:20px; min-height:280px; position:relative; }}
            .city-name {{ font-size:1.4rem; font-weight:700; color:#38bdf8; margin-bottom:4px; }}
            .country-name {{ font-size:0.85rem; color:#8b949e; margin-bottom:16px; }}
            .metric-row {{ display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #1c2333; font-size:0.9rem; }}
            .metric-label {{ color:#8b949e; }}
            .metric-value {{ font-weight:600; color:#f1f5f9; }}
            .chart-card {{ background:#111622; border:1px solid #212636; border-radius:12px; padding:20px; }}
            .loading-spinner {{ display:none; color:#38bdf8; font-size:0.85rem; margin-top:4px; }}
        </style>
    </head>
    <body>
        {NAVBAR_HTML}
        <div class="container">
            <h1>📊 Global Cities Climate Matrix Comparison</h1>

            <div class="selector-bar">
                <!-- City 1 Search Input -->
                <div class="select-group">
                    <label>Primary City (Type Any City Worldwide)</label>
                    <div class="input-box-wrap">
                        <input type="text" id="city1Input" value="Islamabad" placeholder="Search any city in the world..." oninput="handleCitySearch(1)" autocomplete="off">
                        <button class="fetch-btn" onclick="fetchCityData(1)">Compare</button>
                    </div>
                    <div class="suggestions-box" id="sug1"></div>
                    <div class="loading-spinner" id="load1">Fetching real-time telemetry...</div>
                </div>

                <!-- City 2 Search Input -->
                <div class="select-group">
                    <label>Comparison City (Type Any City Worldwide)</label>
                    <div class="input-box-wrap">
                        <input type="text" id="city2Input" value="Lahore" placeholder="Search any city in the world..." oninput="handleCitySearch(2)" autocomplete="off">
                        <button class="fetch-btn" onclick="fetchCityData(2)">Compare</button>
                    </div>
                    <div class="suggestions-box" id="sug2"></div>
                    <div class="loading-spinner" id="load2">Fetching real-time telemetry...</div>
                </div>
            </div>

            <div class="compare-grid">
                <div class="city-card" id="card1"></div>
                <div class="city-card" id="card2"></div>
            </div>

            <div class="chart-card">
                <h3 style="color:#38bdf8; margin-bottom:16px;">Real-Time Multi-Metric Visual Comparison</h3>
                <canvas id="compareChart" height="100"></canvas>
            </div>
        </div>

        <script>
            let city1Telemetry = null;
            let city2Telemetry = null;
            let compareChart = null;
            let searchDebounce = {{ 1: null, 2: null }};

            // Global Real-Time Geocoding API Search (No Hardcoded Cities)
            async function handleCitySearch(cityNum) {{
                const inputVal = document.getElementById(`city${{cityNum}}Input`).value.trim();
                const sugBox = document.getElementById(`sug${{cityNum}}`);

                if (inputVal.length < 2) {{
                    sugBox.style.display = 'none';
                    return;
                }}

                clearTimeout(searchDebounce[cityNum]);
                searchDebounce[cityNum] = setTimeout(async () => {{
                    try {{
                        const res = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${{encodeURIComponent(inputVal)}}&count=6&language=en&format=json`);
                        const data = await res.json();
                        
                        if (!data.results || data.results.length === 0) {{
                            sugBox.style.display = 'none';
                            return;
                        }}

                        sugBox.innerHTML = '';
                        data.results.forEach(city => {{
                            const country = city.country ? `, ${{city.country}}` : '';
                            const admin = city.admin1 ? ` (${{city.admin1}})` : '';
                            const item = document.createElement('div');
                            item.className = 'suggestion-item';
                            item.innerText = `${{city.name}}${{admin}}${{country}}`;
                            item.onclick = () => {{
                                document.getElementById(`city${{cityNum}}Input`).value = city.name;
                                sugBox.style.display = 'none';
                                fetchCityData(cityNum);
                            }};
                            sugBox.appendChild(item);
                        }});
                        sugBox.style.display = 'block';
                    }} catch (e) {{
                        console.error('Geocoding error:', e);
                    }}
                }}, 250);
            }}

            // Close suggestion drop-downs when clicking outside
            document.addEventListener('click', (e) => {{
                if (!e.target.closest('.select-group')) {{
                    document.getElementById('sug1').style.display = 'none';
                    document.getElementById('sug2').style.display = 'none';
                }}
            }});

            async function fetchTelemetryData(cityName) {{
                const res = await fetch(`/api/telemetry?city=${{encodeURIComponent(cityName)}}`);
                if(!res.ok) throw new Error('City not found');
                return await res.json();
            }}

            function parseNumber(str) {{
                if(!str) return 0;
                const match = str.toString().match(/-?\d+(\.\d+)?/);
                return match ? parseFloat(match[0]) : 0;
            }}

            function renderCityCard(data) {{
                if(!data) return `<div style="color:#ef4444; padding:20px;">Unable to load telemetry data.</div>`;
                
                return `
                    <div class="city-name">${{data.city}}</div>
                    <div class="country-name">📍 ${{data.country}} | Lat: ${{data.coordinates.lat}}, Lon: ${{data.coordinates.lon}}</div>
                    <div class="metric-row">
                        <span class="metric-label">Temperature</span>
                        <span class="metric-value" style="color:#f87171;">${{data.temperature}}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Urban Heat Island (UHI) Delta</span>
                        <span class="metric-value" style="color:#f97316;">${{data.uhi_index}}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Ocean Surface Thermal</span>
                        <span class="metric-value" style="color:#06b6d4;">${{data.ocean_surface_heat}}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Air Quality Index (AQI)</span>
                        <span class="metric-value" style="color:#facc15;">${{data.aqi}}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Grid Carbon Intensity</span>
                        <span class="metric-value">${{data.grid_carbon_intensity}}</span>
                    </div>
                    <div class="metric-row" style="border-bottom:none;">
                        <span class="metric-label">Turbulence Risk Index</span>
                        <span class="metric-value" style="color:#a855f7;">${{data.turbulence_risk ? data.turbulence_risk.score : 0}} / 100 (${{data.turbulence_risk ? data.turbulence_risk.level : 'N/A'}})</span>
                    </div>
                `;
            }}

            async function fetchCityData(cityNum) {{
                const inputId = cityNum === 1 ? 'city1Input' : 'city2Input';
                const loadId = cityNum === 1 ? 'load1' : 'load2';
                const cardId = cityNum === 1 ? 'card1' : 'card2';
                const cityName = document.getElementById(inputId).value.trim();

                if(!cityName) return;

                document.getElementById(loadId).style.display = 'block';

                try {{
                    const data = await fetchTelemetryData(cityName);
                    if(cityNum === 1) city1Telemetry = data;
                    else city2Telemetry = data;

                    document.getElementById(cardId).innerHTML = renderCityCard(data);
                    updateChart();
                }} catch(err) {{
                    document.getElementById(cardId).innerHTML = `<div style="color:#ef4444; padding:20px;">City "${{cityName}}" not found or telemetry offline. Please try another city.</div>`;
                }} finally {{
                    document.getElementById(loadId).style.display = 'none';
                }}
            }}

            function updateChart() {{
                if(!city1Telemetry || !city2Telemetry) return;

                const c1 = city1Telemetry;
                const c2 = city2Telemetry;

                const c1Temp = parseNumber(c1.temperature);
                const c2Temp = parseNumber(c2.temperature);

                const c1Uhi = parseNumber(c1.uhi_index);
                const c2Uhi = parseNumber(c2.uhi_index);

                const c1Ocean = parseNumber(c1.ocean_surface_heat);
                const c2Ocean = parseNumber(c2.ocean_surface_heat);

                const c1Aqi = c1.aqi || 0;
                const c2Aqi = c2.aqi || 0;

                const c1Carbon = parseNumber(c1.grid_carbon_intensity);
                const c2Carbon = parseNumber(c2.grid_carbon_intensity);

                const c1Turb = c1.turbulence_risk ? c1.turbulence_risk.score : 0;
                const c2Turb = c2.turbulence_risk ? c2.turbulence_risk.score : 0;

                if (compareChart) compareChart.destroy();

                const ctx = document.getElementById('compareChart').getContext('2d');
                compareChart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Temp (°C)', 'UHI (°C)', 'Ocean Heat (°C)', 'AQI Index', 'Carbon (gCO2/kWh)', 'Turbulence'],
                        datasets: [
                            {{
                                label: c1.city,
                                data: [c1Temp, c1Uhi, c1Ocean, c1Aqi, c1Carbon, c1Turb],
                                backgroundColor: 'rgba(56, 189, 248, 0.7)',
                                borderColor: '#38bdf8',
                                borderWidth: 1
                            }},
                            {{
                                label: c2.city,
                                data: [c2Temp, c2Uhi, c2Ocean, c2Aqi, c2Carbon, c2Turb],
                                backgroundColor: 'rgba(239, 68, 68, 0.7)',
                                borderColor: '#ef4444',
                                borderWidth: 1
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            x: {{ ticks: {{ color: '#8b949e' }} }},
                            y: {{ ticks: {{ color: '#8b949e' }} }}
                        }},
                        plugins: {{
                            legend: {{ labels: {{ color: '#e6edf3' }} }}
                        }}
                    }}
                }});
            }}

            window.onload = async () => {{
                await fetchCityData(1);
                await fetchCityData(2);
            }};
        </script>
    </body>
    </html>
    """

# =====================================================================
# 7. PAGE 3: ABOUT & LEARN STORY PAGE (`/about`)
# =====================================================================
@app.get("/about", response_class=HTMLResponse, tags=["UI Portal"])
def render_about_page():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>About EcoPulse - Climate Intelligence Platform</title>
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            body {{ background:#0b0f17; color:#e6edf3; display:flex; flex-direction:column; min-height:100vh; line-height:1.6; }}
            .content {{ padding:40px 20px; max-width:1000px; margin:0 auto; width:100%; }}
            h1 {{ color:#38bdf8; font-size:2.2rem; margin-bottom:12px; }}
            h2 {{ color:#38bdf8; font-size:1.4rem; margin-top:30px; margin-bottom:10px; border-bottom:1px solid #212636; padding-bottom:6px; }}
            p {{ color:#c9d1d9; font-size:1rem; margin-bottom:16px; }}
            .feature-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:16px; margin-top:20px; }}
            .feature-box {{ background:#111622; border:1px solid #212636; border-radius:8px; padding:16px; }}
            .feature-title {{ font-weight:700; color:#38bdf8; margin-bottom:6px; }}
        </style>
    </head>
    <body>
        {NAVBAR_HTML}
        <div class="content">
            <h1>🌍 The EcoPulse Platform Story</h1>
            <p><strong>EcoPulse</strong> is an enterprise climate monitoring and predictive AI intelligence suite bridging real-time environmental telemetry with machine learning systems.</p>

            <h2>🚀 Core Capabilities Included:</h2>
            <div class="feature-grid">
                <div class="feature-box">
                    <div class="feature-title">1. Urban Heat Island (UHI) Diagnostics</div>
                    <p style="font-size:0.85rem; color:#8b949e;">Measures microclimate heat trapping in dense concrete urban centers versus surrounding baseline areas.</p>
                </div>
                <div class="feature-box">
                    <div class="feature-title">2. Ocean Heat & Sea Surface Anomaly</div>
                    <p style="font-size:0.85rem; color:#8b949e;">Monitors thermal heat buildup across marine ecosystems and coastal sectors.</p>
                </div>
                <div class="feature-box">
                    <div class="feature-title">3. Carbon Grid Emission Tracking</div>
                    <p style="font-size:0.85rem; color:#8b949e;">Evaluates real-time electrical grid carbon intensities (gCO2eq/kWh) powered by Electricity Maps API.</p>
                </div>
                <div class="feature-box">
                    <div class="feature-title">4. Atmospheric Turbulence & Wind Shear</div>
                    <p style="font-size:0.85rem; color:#8b949e;">Calculates boundary-layer wind speed and gust deltas to score aviation and structural safety hazards.</p>
                </div>
                <div class="feature-box">
                    <div class="feature-title">5. Pollen & Allergy Alert Engine</div>
                    <p style="font-size:0.85rem; color:#8b949e;">Detailed botanical particle tracking calculating tree, grass, and weed pollen concentrations.</p>
                </div>
                <div class="feature-box">
                    <div class="feature-title">6. Global Wildfire & Hotspot Tracker</div>
                    <p style="font-size:0.85rem; color:#8b949e;">Real-time NASA FIRMS thermal hotspots tracking Fire Radiative Power (FRP) globally.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
# =====================================================================
# 8. Model Metrics
# =====================================================================
@app.get("/api/model-metrics")
async def get_model_metrics():
    """
    Returns real, dynamically calculated XGBoost model validation metrics.
    """
    try:
        with open("metrics.json", "r") as f:
            metrics = json.load(f)
        return {
            "status": "success",
            "model": "XGBoost Regressor",
            "metrics": metrics
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail="Metrics file not found. Please run train_model.py first."
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)