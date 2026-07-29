"""
EcoPulse – Global Climate Intelligence Platform
Complete FastAPI backend with all endpoints:
- 10 Climate Features (Weather, Fires, Ocean, Carbon, Turbulence, Pollen, UHI, Risk, Alerts, Historical)
- Enhanced Analytics with city-level metrics
- Multi-City Comparison (ANY city in the world with autocomplete)
- Predictive Risk Alerts (16 cities with severity)
- Scenario Simulator (urban density, vegetation, renewables)
- Email Subscription & Trigger Alerts (country-specific)
- Chatbot, WebSocket, Caching, ML Prediction (with fallback)
- Reverse Geocoding for dynamic city selection
Version: 3.4 | Python 3.11+
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
import smtplib
import httpx
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------
# IMPORTS from data_fetchers
# -------------------------------------------------------------------
from data_fetchers import (
    fetch_weather,
    fetch_fires,
    fetch_ocean_temp,
    fetch_carbon_intensity,
    fetch_turbulence,
    fetch_pollen,
    fetch_uhi,
    fetch_risk_score,
    fetch_alerts,
    fetch_historical,
    fetch_risk_alerts,
)

# -------------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# ML MODELS (load with lifespan)
# -------------------------------------------------------------------
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
        logger.info("✅ ML models loaded successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Could not load ML models: {e}. Predictions will use fallback.")
    yield

# -------------------------------------------------------------------
# FASTAPI APP
# -------------------------------------------------------------------
app = FastAPI(
    title="EcoPulse API",
    version="3.4",
    description="Global Climate Intelligence Platform",
    lifespan=lifespan
)

# CORS – allow all origins for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# IN‑MEMORY CACHE
# -------------------------------------------------------------------
cache = {}

def get_cached(key: str, ttl: int = 300):
    """Retrieve cached data if not expired."""
    if key in cache and (datetime.utcnow() - cache[key]['time']).seconds < ttl:
        return cache[key]['data']
    return None

def set_cache(key: str, data: Any):
    """Store data in cache with timestamp."""
    cache[key] = {'data': data, 'time': datetime.utcnow()}

# -------------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ===================================================================
# 1. WEATHER
# ===================================================================
@app.get("/api/weather")
async def weather(lat: float = Query(...), lon: float = Query(...)):
    cache_key = f"weather_{lat}_{lon}"
    cached = get_cached(cache_key, ttl=600)
    if cached:
        return cached
    data = await fetch_weather(lat, lon)
    set_cache(cache_key, data)
    return data

# ===================================================================
# 2. FIRES
# ===================================================================
@app.get("/api/fires")
async def fires(
    min_lon: float = -180,
    min_lat: float = -90,
    max_lon: float = 180,
    max_lat: float = 90
):
    cache_key = f"fires_{min_lon}_{min_lat}_{max_lon}_{max_lat}"
    cached = get_cached(cache_key, ttl=300)
    if cached:
        return cached
    data = await fetch_fires((min_lon, min_lat, max_lon, max_lat))
    set_cache(cache_key, data)
    return data

# ===================================================================
# 3. OCEAN
# ===================================================================
@app.get("/api/ocean")
async def ocean(lat: float = Query(...), lon: float = Query(...)):
    cache_key = f"ocean_{lat}_{lon}"
    cached = get_cached(cache_key, ttl=3600)
    if cached:
        return cached
    data = await fetch_ocean_temp(lat, lon)
    set_cache(cache_key, data)
    return data

# ===================================================================
# 4. CARBON INTENSITY
# ===================================================================
@app.get("/api/carbon")
async def carbon(country: str = "US"):
    cache_key = f"carbon_{country}"
    cached = get_cached(cache_key, ttl=1800)
    if cached:
        return cached
    data = await fetch_carbon_intensity(country)
    set_cache(cache_key, data)
    return data

# ===================================================================
# 5. TURBULENCE
# ===================================================================
@app.get("/api/turbulence")
async def turbulence(
    min_lon: float = -180,
    min_lat: float = -90,
    max_lon: float = 180,
    max_lat: float = 90
):
    cache_key = f"turbulence_{min_lon}_{min_lat}_{max_lon}_{max_lat}"
    cached = get_cached(cache_key, ttl=600)
    if cached:
        return cached
    data = await fetch_turbulence((min_lon, min_lat, max_lon, max_lat))
    set_cache(cache_key, data)
    return data

# ===================================================================
# 6. POLLEN
# ===================================================================
@app.get("/api/pollen")
async def pollen(lat: float = Query(...), lon: float = Query(...)):
    cache_key = f"pollen_{lat}_{lon}"
    cached = get_cached(cache_key, ttl=3600)
    if cached:
        return cached
    data = await fetch_pollen(lat, lon)
    set_cache(cache_key, data)
    return data

# ===================================================================
# 7. URBAN HEAT ISLAND (UHI)
# ===================================================================
@app.get("/api/uhi")
async def uhi(city: str = Query(...)):
    cache_key = f"uhi_{city}"
    cached = get_cached(cache_key, ttl=1800)
    if cached:
        return cached
    data = await fetch_uhi(city)
    set_cache(cache_key, data)
    return data

# ===================================================================
# 8. SOVEREIGN RISK SCORE
# ===================================================================
@app.get("/api/risk-score")
async def risk_score(country: str = "US"):
    cache_key = f"risk_{country}"
    cached = get_cached(cache_key, ttl=3600)
    if cached:
        return cached
    data = await fetch_risk_score(country)
    set_cache(cache_key, data)
    return data

# ===================================================================
# 9. EXTREME ALERTS
# ===================================================================
@app.get("/api/alerts")
async def alerts(
    min_lon: float = -180,
    min_lat: float = -90,
    max_lon: float = 180,
    max_lat: float = 90
):
    cache_key = f"alerts_{min_lon}_{min_lat}_{max_lon}_{max_lat}"
    cached = get_cached(cache_key, ttl=120)
    if cached:
        return cached
    data = await fetch_alerts((min_lon, min_lat, max_lon, max_lat))
    set_cache(cache_key, data)
    return data

# ===================================================================
# 10. HISTORICAL DATA
# ===================================================================
@app.get("/api/historical")
async def historical(
    lat: float = Query(...),
    lon: float = Query(...),
    days: int = Query(7, ge=1, le=30)
):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    data = await fetch_historical(lat, lon, start_date.isoformat(), end_date.isoformat())
    return data

# ===================================================================
# ML PREDICTION (with fallback)
# ===================================================================
@app.post("/api/predict")
async def predict_temperature(features: dict):
    """
    Predict temperature anomaly using XGBoost (or linear fallback).
    Input: elevation, urban_density, veg_index, water_dist, hour
    """
    if model is None:
        # Linear fallback
        anomaly = (
            features.get('elevation', 0) * 0.01
            - features.get('urban_density', 0) * 0.02
            + features.get('veg_index', 0) * 0.5
            - features.get('water_dist', 0) * 0.1
            + np.sin(features.get('hour', 12) / 24 * 2 * np.pi) * 1.5
        )
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

# ===================================================================
# ANALYTICS (Enhanced with city-level metrics)
# ===================================================================
@app.get("/api/analytics")
async def get_analytics():
    """Return global stats and city-level temperature, humidity, wind, risk scores."""
    try:
        fires = await fetch_fires()
        alerts = await fetch_alerts()

        # List of cities for detailed metrics
        city_list = [
            {"name": "Karachi", "lat": 24.86, "lon": 67.01},
            {"name": "Lahore", "lat": 31.52, "lon": 74.36},
            {"name": "Islamabad", "lat": 33.68, "lon": 73.05},
            {"name": "Mumbai", "lat": 19.08, "lon": 72.88},
            {"name": "Delhi", "lat": 28.61, "lon": 77.23},
        ]

        city_names = []
        city_temps = []
        city_humidity = []
        city_wind = []
        risk_scores = []

        for city in city_list:
            w = await fetch_weather(city["lat"], city["lon"])
            if w and w.get('current'):
                city_names.append(city["name"])
                city_temps.append(w['current']['temperature_2m'])
                city_humidity.append(w['current']['relative_humidity_2m'])
                city_wind.append(w['current']['wind_speed_10m'])
                # Fetch risk score for country (simplified)
                country_map = {
                    "Karachi": "PK",
                    "Lahore": "PK",
                    "Islamabad": "PK",
                    "Mumbai": "IN",
                    "Delhi": "IN"
                }
                country = country_map.get(city["name"], "US")
                risk = await fetch_risk_score(country)
                risk_scores.append(risk.get('score', 50))

        # Compute averages
        avg_temp = round(sum(city_temps) / len(city_temps), 1) if city_temps else 20.0
        avg_humidity = round(sum(city_humidity) / len(city_humidity), 1) if city_humidity else 50.0
        avg_wind = round(sum(city_wind) / len(city_wind), 1) if city_wind else 10.0

        # Fallback if no data
        if not city_names:
            city_names = ["Karachi", "Lahore", "Islamabad", "Mumbai", "Delhi"]
            city_temps = [22, 24, 20, 26, 28]
            city_humidity = [60, 55, 65, 70, 50]
            city_wind = [12, 10, 8, 15, 9]
            risk_scores = [60, 55, 70, 45, 50]

        return {
            "total_fires": len(fires),
            "total_alerts": len(alerts),
            "avg_temperature": avg_temp,
            "avg_humidity": avg_humidity,
            "avg_wind": avg_wind,
            "city_names": city_names,
            "city_temps": city_temps,
            "city_humidity": city_humidity,
            "city_wind": city_wind,
            "risk_scores": risk_scores,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {
            "total_fires": 0,
            "total_alerts": 0,
            "avg_temperature": 20.0,
            "avg_humidity": 50.0,
            "avg_wind": 10.0,
            "city_names": ["Karachi", "Lahore", "Islamabad", "Mumbai", "Delhi"],
            "city_temps": [22, 24, 20, 26, 28],
            "city_humidity": [60, 55, 65, 70, 50],
            "city_wind": [12, 10, 8, 15, 9],
            "risk_scores": [60, 55, 70, 45, 50],
            "timestamp": datetime.utcnow().isoformat()
        }

# ===================================================================
# REVERSE GEOCODING (Dynamic City Comparison)
# ===================================================================
country_cache = {}

async def get_country_code(lat: float, lon: float) -> str:
    """Get country code from lat/lon using Nominatim reverse geocoding."""
    cache_key = f"{lat:.2f},{lon:.2f}"
    if cache_key in country_cache:
        return country_cache[cache_key]

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "EcoPulse/3.0"})
            resp.raise_for_status()
            data = resp.json()
            address = data.get("address", {})
            # Try to get country code from address
            if "country_code" in address:
                country_code = address["country_code"].upper()
            else:
                # Fallback to country name mapping
                country = address.get("country", "")
                if "Pakistan" in country:
                    country_code = "PK"
                elif "India" in country:
                    country_code = "IN"
                elif "United States" in country:
                    country_code = "US"
                elif "United Kingdom" in country:
                    country_code = "UK"
                else:
                    country_code = "US"
            country_cache[cache_key] = country_code
            return country_code
    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        return "US"

# ===================================================================
# DYNAMIC CITY METRICS (Any city in the world)
# ===================================================================
async def fetch_uhi_by_coords(lat: float, lon: float, city_name: str = None):
    """Compute UHI intensity using coordinates directly."""
    try:
        # Use a point ~20km away as rural
        rural_lat = lat + random.uniform(0.15, 0.3)
        rural_lon = lon + random.uniform(0.15, 0.3)

        urban_w = await fetch_weather(lat, lon)
        rural_w = await fetch_weather(rural_lat, rural_lon)
        urban_temp = urban_w.get("current", {}).get("temperature_2m", 25)
        rural_temp = rural_w.get("current", {}).get("temperature_2m", 22)
        uhi_intensity = round(urban_temp - rural_temp, 1)

        return {
            "city": city_name or f"{lat:.2f},{lon:.2f}",
            "urban_temp": urban_temp,
            "rural_temp": rural_temp,
            "uhi_intensity": uhi_intensity
        }
    except Exception:
        return {
            "city": city_name or f"{lat:.2f},{lon:.2f}",
            "urban_temp": round(random.uniform(25, 40), 1),
            "rural_temp": round(random.uniform(20, 35), 1),
            "uhi_intensity": round(random.uniform(0, 8), 1)
        }

async def get_city_metrics_by_coords(city_name: str, lat: float, lon: float, country_code: str = "US"):
    """Fetch metrics for any city using lat/lon and country code."""
    try:
        w = await fetch_weather(lat, lon)
        fires = await fetch_fires()
        carbon = await fetch_carbon_intensity(country_code)
        uhi = await fetch_uhi_by_coords(lat, lon, city_name)
        risk = await fetch_risk_score(country_code)

        # Count fires near city
        near_fires = sum(1 for f in fires if abs(f['lat']-lat) < 2 and abs(f['lon']-lon) < 2)
        temp = w.get('current', {}).get('temperature_2m', 0) if w else 0

        return {
            "city": city_name,
            "temperature": round(temp, 1),
            "fires_nearby": near_fires,
            "carbon_intensity": carbon.get('carbon_intensity', 0) if carbon else 0,
            "uhi_intensity": uhi.get('uhi_intensity', 0) if uhi else 0,
            "risk_score": risk.get('score', 0) if risk else 0,
        }
    except Exception as e:
        logger.error(f"Error fetching metrics for {city_name}: {e}")
        return {
            "city": city_name,
            "temperature": round(random.uniform(15, 35), 1),
            "fires_nearby": random.randint(0, 5),
            "carbon_intensity": random.randint(200, 500),
            "uhi_intensity": round(random.uniform(0, 6), 1),
            "risk_score": random.randint(30, 80),
        }

@app.post("/api/compare-coords")
async def compare_coords(cities: List[Dict[str, Any]] = Body(...)):
    """
    Compare metrics for user-selected cities provided with lat/lon.
    Input: [{"name": "Karachi", "lat": 24.86, "lon": 67.01}, ...]
    """
    if len(cities) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 cities allowed")

    results = []
    for city in cities:
        name = city.get("name", f"{city['lat']:.2f},{city['lon']:.2f}")
        lat = city.get("lat")
        lon = city.get("lon")
        if lat is None or lon is None:
            continue

        # Get country code via reverse geocoding (cached)
        country_code = await get_country_code(lat, lon)

        metrics = await get_city_metrics_by_coords(name, lat, lon, country_code)
        results.append(metrics)

    return {"comparison": results, "timestamp": datetime.utcnow().isoformat()}

# ===================================================================
# EMAIL & SUBSCRIPTION
# ===================================================================
subscribers = {}  # email -> country

async def send_alert_email(
    email: str,
    alert_type: str,
    city: str,
    country: str,
    severity: str,
    description: str
) -> bool:
    """Send a real email via Gmail SMTP using app password."""
    sender_email = os.getenv("EMAIL_SENDER", "")
    sender_password = os.getenv("EMAIL_PASSWORD", "")

    if not sender_email or not sender_password:
        logger.warning(f"⚠️ Email credentials not set. Would send: {alert_type} to {email}")
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
• Check EcoPulse dashboard: https://ecopulse-1-b2lm.onrender.com/

---
🌿 EcoPulse – Global Climate Intelligence Platform
"Know the climate. Act on it."
"""
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        logger.info(f"✅ Email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"❌ Email error: {e}")
        return False

@app.post("/api/subscribe")
async def subscribe(
    email: str = Query(...),
    country: str = Query("Pakistan")
):
    """Subscribe a user to alerts for a specific country."""
    subscribers[email] = country
    return {"status": "subscribed", "email": email, "country": country}

@app.get("/api/subscribers")
async def list_subscribers():
    """Return all subscribed users (for debugging)."""
    return {"subscribers": subscribers}

@app.post("/api/trigger-alerts")
async def trigger_alerts():
    """Trigger alerts for all subscribers based on their chosen country."""
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
                await asyncio.sleep(1)  # Rate limit 1 email/sec

    return {
        "status": "sent",
        "count": sent_count,
        "message": f"Sent {sent_count} alerts to subscribers"
    }

# ===================================================================
# CHATBOT
# ===================================================================
@app.get("/api/chat")
@app.post("/api/chat")
async def chat(message: str = Query(...)):
    """Simple AI assistant for climate-related queries."""
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
        return {"reply": "🤖 I'm your climate assistant. Ask about weather, fires, alerts, rain, carbon, pollen, or humidity."}

# ===================================================================
# PREDICTIVE RISK ALERTS (16 cities with severity)
# ===================================================================
@app.get("/api/risk-alerts")
async def risk_alerts():
    """Return risk alerts for 16 global cities with severity levels."""
    alerts = await fetch_risk_alerts()
    return {"alerts": alerts, "timestamp": datetime.utcnow().isoformat()}

# ===================================================================
# SCENARIO SIMULATOR
# ===================================================================
@app.post("/api/scenario")
async def scenario_simulator(params: dict):
    """
    Simulate impact of urban density, vegetation, and renewable energy.
    Returns anomaly and carbon intensity.
    """
    urban = params.get('urban_density', 50)
    veg = params.get('veg_index', 0.5)
    renewable = params.get('renewable_percent', 30)

    # Predict anomaly (ML fallback)
    if model is None:
        anomaly = (urban * 0.01 - veg * 0.5) * 2
    else:
        input_df = pd.DataFrame(
            [[50, urban, veg, 2, 12]],
            columns=['elevation', 'urban_density', 'veg_index', 'water_dist', 'hour']
        )
        scaled = scaler.transform(input_df)
        anomaly = model.predict(scaled)[0]

    # Carbon intensity: base 400 gCO₂/kWh, reduced by renewable %
    base_carbon = 400
    carbon_reduction = renewable * 3  # max 300 reduction
    new_carbon = max(100, base_carbon - carbon_reduction)

    return {
        "anomaly": float(anomaly),
        "carbon_intensity": new_carbon,
        "renewable_percent": renewable
    }

# ===================================================================
# LEGACY MULTI‑CITY COMPARISON (Predefined cities for backward compatibility)
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
    "Tehran": (35.68, 51.38),
    "Dubai": (25.20, 55.27),
    "Singapore": (1.35, 103.82),
    "Hong Kong": (22.31, 114.16),
    "Bangkok": (13.75, 100.50),
    "Jakarta": (-6.20, 106.81),
}

COUNTRY_MAP = {
    "Karachi": "PK",
    "Lahore": "PK",
    "Islamabad": "PK",
    "Mumbai": "IN",
    "Delhi": "IN",
    "London": "UK",
    "New York": "US",
    "Tokyo": "JP",
    "Sydney": "AU",
    "Cape Town": "ZA",
    "Tehran": "IR",
    "Dubai": "AE",
    "Singapore": "SG",
    "Hong Kong": "CN",
    "Bangkok": "TH",
    "Jakarta": "ID",
}

async def get_city_metrics_predefined(city_name: str) -> dict:
    """Fetch all metrics for a single city (predefined)."""
    lat, lon = CITY_COORDS[city_name]
    country = COUNTRY_MAP.get(city_name, "US")

    try:
        w = await fetch_weather(lat, lon)
        fires = await fetch_fires()
        carbon = await fetch_carbon_intensity(country)
        uhi = await fetch_uhi(city_name)
        risk = await fetch_risk_score(country)

        near_fires = sum(
            1 for f in fires
            if abs(f['lat'] - lat) < 2 and abs(f['lon'] - lon) < 2
        )

        temp = w.get('current', {}).get('temperature_2m', 0) if w else 0

        return {
            "city": city_name,
            "temperature": round(temp, 1),
            "fires_nearby": near_fires,
            "carbon_intensity": carbon.get('carbon_intensity', 0) if carbon else 0,
            "uhi_intensity": uhi.get('uhi_intensity', 0) if uhi else 0,
            "risk_score": risk.get('score', 0) if risk else 0,
        }

    except Exception as e:
        logger.error(f"Error fetching metrics for {city_name}: {e}")
        return {
            "city": city_name,
            "temperature": 0,
            "fires_nearby": 0,
            "carbon_intensity": 0,
            "uhi_intensity": 0,
            "risk_score": 0,
        }

@app.post("/api/compare")
async def compare_cities(cities: List[str] = Query(...)):
    """Compare metrics for up to 5 predefined cities."""
    if len(cities) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 cities allowed")

    results = []
    for city in cities:
        if city in CITY_COORDS:
            metrics = await get_city_metrics_predefined(city)
            results.append(metrics)

    return {
        "comparison": results,
        "timestamp": datetime.utcnow().isoformat()
    }

# ===================================================================
# WEBSOCKET (Real‑time updates)
# ===================================================================
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
            except Exception:
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

# ===================================================================
# SERVE FRONTEND
# ===================================================================
@app.get("/")
async def serve_dashboard():
    return FileResponse("dashboard.html")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse("manifest.json")

@app.get("/sw.js")
async def serve_sw():
    return FileResponse("sw.js")

# ===================================================================
# ROOT
# ===================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )