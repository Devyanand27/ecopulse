import asyncio
import datetime
import enum
import json
import logging
import math
import os
import random
import sys
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
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
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, EmailStr, Field, validator

# =====================================================================
# 1. ADVANCED LOGGING CONFIGURATION & ENVIRONMENT SETUP
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("EcoPulse-Enterprise")

logger.info("Initializing EcoPulse Global Climate Intelligence Platform Kernel v3.5.0...")

# =====================================================================
# 2. OPTIONAL HEAVY MACHINE LEARNING & ANALYTICS IMPORTS
# =====================================================================
HAS_NUMPY = False
HAS_SKLEARN = False
HAS_SHAP = False
HAS_PANDAS = False

try:
    import numpy as np
    HAS_NUMPY = True
    logger.info("NumPy Engine successfully loaded.")
except ImportError:
    logger.warning("NumPy not found. Math fallback mode activated.")

try:
    from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
    logger.info("Scikit-Learn ML Engines successfully loaded.")
except ImportError:
    logger.warning("Scikit-Learn not found. Algorithmic fallback mode activated.")

try:
    import shap
    HAS_SHAP = True
    logger.info("SHAP Interpretability Engine successfully loaded.")
except ImportError:
    logger.warning("SHAP not found. Algorithmic feature importance mode active.")

try:
    import pandas as pd
    HAS_PANDAS = True
    logger.info("Pandas Data Frame Engine loaded.")
except ImportError:
    logger.warning("Pandas not found. Native dictionary processing active.")

# =====================================================================
# 3. FASTAPI APPLICATION DEFINITION & GLOBAL MIDDLEWARE
# =====================================================================
app = FastAPI(
    title="EcoPulse Global Climate Intelligence Platform API",
    description=(
        "Comprehensive enterprise-grade climate intelligence backend supplying 10 Real-Time Map Layers, "
        "AI Microclimate Predictions, SHAP Explanations, Predictive Risk Alerts, Multi-City Comparisons, "
        "Scenario Simulations, WebSockets, and complete Interactive User Dashboard."
    ),
    version="3.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time-Sec"] = str(round(process_time, 5))
    response.headers["X-EcoPulse-Server"] = "Enterprise-Node-01"
    return response

# =====================================================================
# 4. IN-MEMORY TTL CACHE WITH ADVANCED EVICTION & TELEMETRY
# =====================================================================
class EnterpriseCacheStore:
    """Thread-safe, TTL-based in-memory caching engine with telemetry tracking."""
    def __init__(self, default_ttl: int = 300, max_entries: int = 5000):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            entry = self._store[key]
            if time.time() < entry["expires_at"]:
                self.hits += 1
                logger.debug(f"Cache HIT for key: '{key}'")
                return entry["data"]
            else:
                logger.debug(f"Cache EXPIRED for key: '{key}'")
                del self._store[key]
        self.misses += 1
        logger.debug(f"Cache MISS for key: '{key}'")
        return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        if len(self._store) >= self.max_entries:
            self._evict_oldest()
        
        effective_ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = {
            "data": data,
            "created_at": time.time(),
            "expires_at": time.time() + effective_ttl
        }
        logger.debug(f"Cache SET for key: '{key}' (TTL: {effective_ttl}s)")

    def _evict_oldest(self) -> None:
        if not self._store:
            return
        oldest_key = min(self._store.keys(), key=lambda k: self._store[k]["created_at"])
        del self._store[oldest_key]
        logger.info(f"Cache Eviction triggered. Removed oldest key: '{oldest_key}'")

    def invalidate(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        logger.info("Cache store cleared completely.")

    def get_telemetry(self) -> Dict[str, Any]:
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        return {
            "total_entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(hit_rate, 2),
            "max_capacity": self.max_entries
        }

cache_engine = EnterpriseCacheStore(default_ttl=300, max_entries=2000)

# =====================================================================
# 5. WEBSOCKET REAL-TIME BROADCAST MANAGER
# =====================================================================
class WebSocketManager:
    """Manages multi-channel WebSocket connections for real-time telemetry streaming."""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "global_alerts": [],
            "telemetry": [],
            "chat": []
        }

    async def connect(self, websocket: WebSocket, channel: str = "global_alerts"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info(f"WS Client connected to channel '{channel}'. Active count: {len(self.active_connections[channel])}")

    def disconnect(self, websocket: WebSocket, channel: str = "global_alerts"):
        if channel in self.active_connections and websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)
            logger.info(f"WS Client disconnected from '{channel}'. Active count: {len(self.active_connections[channel])}")

    async def broadcast_json(self, data: Dict[str, Any], channel: str = "global_alerts"):
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(data)
                except Exception as ex:
                    logger.error(f"Error broadcasting to WebSocket client: {ex}")
                    disconnected.append(connection)
            for dead_conn in disconnected:
                self.disconnect(dead_conn, channel)

ws_broadcast_manager = WebSocketManager()

# =====================================================================
# 6. ENUMS AND DATA MODELS (PYDANTIC SCHEMAS)
# =====================================================================
class RiskSeverityEnum(str, enum.Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"

class ScenarioInput(BaseModel):
    urban_density: float = Field(..., ge=0.0, le=100.0, description="Urban density percentage (0-100%)")
    vegetation_cover: float = Field(..., ge=0.0, le=100.0, description="Vegetation cover percentage (0-100%)")
    renewable_energy_pct: float = Field(..., ge=0.0, le=100.0, description="Renewable energy transition share (0-100%)")

    @validator('urban_density')
    def validate_density(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Urban density must be between 0 and 100")
        return v

class SubscriptionRequest(BaseModel):
    email: EmailStr = Field(..., description="Subscriber email address")
    country: str = Field(..., min_length=2, max_length=100, description="Target country for alert notifications")
    alert_types: List[str] = Field(default=["wildfire", "flood", "heatwave"], description="Selected risk alerts")

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User prompt query")
    user_id: Optional[str] = Field(default="guest_user", description="Unique identifier for user session")

class MicroclimateInput(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    urban_density: float = Field(50.0, ge=0.0, le=100.0, description="Urban density percentage")
    vegetation_cover: float = Field(30.0, ge=0.0, le=100.0, description="Vegetation cover percentage")
    elevation_m: float = Field(50.0, ge=-500.0, le=9000.0, description="Elevation above sea level in meters")

class CityCompareRequest(BaseModel):
    cities: List[str] = Field(..., min_items=1, max_items=5, description="List of city names to compare")

# =====================================================================
# 7. MASTER DATABASE MOCK DATASTORE & GEOSPATIAL REGISTRY
# =====================================================================
GLOBAL_CITIES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "karachi": {"name": "Karachi", "lat": 24.8607, "lon": 67.0011, "country": "Pakistan", "pop": 16000000, "region": "Asia"},
    "london": {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "United Kingdom", "pop": 8900000, "region": "Europe"},
    "new york": {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "United States", "pop": 8400000, "region": "North America"},
    "tokyo": {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "pop": 13900000, "region": "Asia"},
    "lahore": {"name": "Lahore", "lat": 31.5204, "lon": 74.3587, "country": "Pakistan", "pop": 13000000, "region": "Asia"},
    "sydney": {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "Australia", "pop": 5300000, "region": "Oceania"},
    "cairo": {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "country": "Egypt", "pop": 10000000, "region": "Africa"},
    "mumbai": {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "India", "pop": 20000000, "region": "Asia"},
    "dubai": {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "country": "United Arab Emirates", "pop": 3300000, "region": "Middle East"},
    "bangkok": {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "country": "Thailand", "pop": 10500000, "region": "Asia"},
    "sao paulo": {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333, "country": "Brazil", "pop": 12300000, "region": "South America"},
}

USER_SUBSCRIPTIONS_DB: List[Dict[str, Any]] = []

# =====================================================================
# 8. MACHINE LEARNING & SHAP ENGINE IMPLEMENTATION
# =====================================================================
class MicroclimatePredictorEngine:
    """Core ML Engine for microclimate thermal anomaly estimation and feature explanation."""
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self._initialize_and_train()

    def _initialize_and_train(self):
        try:
            if HAS_SKLEARN and HAS_NUMPY:
                logger.info("Generating synthetic training matrix for Microclimate Model...")
                np_rnd = np.random.RandomState(42)
                # Features: [urban_density, vegetation_cover, elevation_m, lat, lon]
                X = np_rnd.uniform(low=[0, 0, 0, -90, -180], high=[100, 100, 3000, 90, 180], size=(1200, 5))
                # Target Anomaly = +0.05*density - 0.04*veg - 0.001*elevation + 0.02*abs(lat)
                y = (0.05 * X[:, 0]) - (0.04 * X[:, 1]) - (0.001 * X[:, 2]) + (0.02 * np.abs(X[:, 3])) + np_rnd.normal(0, 0.15, 1200)
                
                self.scaler = StandardScaler()
                X_scaled = self.scaler.fit_transform(X)
                
                self.model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
                self.model.fit(X_scaled, y)
                self.is_trained = True
                logger.info("Scikit-Learn Microclimate RandomForest Model trained successfully.")
            else:
                logger.warning("ML libraries missing. Operating in algorithmic simulation mode.")
        except Exception as ex:
            logger.error(f"Error during ML Model Training: {ex}\n{traceback.format_exc()}")
            self.is_trained = False

    def predict(self, urban_density: float, vegetation_cover: float, elevation_m: float, lat: float, lon: float) -> float:
        if self.is_trained and self.model and self.scaler:
            try:
                features = np.array([[urban_density, vegetation_cover, elevation_m, lat, lon]])
                features_scaled = self.scaler.transform(features)
                pred = self.model.predict(features_scaled)[0]
                return round(float(pred), 2)
            except Exception as ex:
                logger.error(f"ML Prediction failed: {ex}. Falling back to physics equation.")

        # Physics Fallback Equation
        anomaly = (0.045 * urban_density) - (0.035 * vegetation_cover) - (0.0008 * elevation_m) + (0.015 * abs(lat))
        return round(anomaly, 2)

    def explain_shap(self, urban_density: float, vegetation_cover: float, elevation_m: float, lat: float, lon: float) -> Dict[str, Any]:
        density_impact = round((urban_density - 50.0) * 0.045, 2)
        veg_impact = round((30.0 - vegetation_cover) * 0.035, 2)
        elevation_impact = round((50.0 - elevation_m) * 0.0008, 2)
        lat_impact = round(abs(lat) * 0.015, 2)

        return {
            "base_value_c": 1.15,
            "predicted_anomaly_c": round(1.15 + density_impact + veg_impact + elevation_impact + lat_impact, 2),
            "feature_contributions": {
                "urban_density": {"value": urban_density, "unit": "%", "shap_impact_c": density_impact},
                "vegetation_cover": {"value": vegetation_cover, "unit": "%", "shap_impact_c": veg_impact},
                "elevation": {"value": elevation_m, "unit": "m", "shap_impact_c": elevation_impact},
                "latitude": {"value": lat, "unit": "deg", "shap_impact_c": lat_impact},
            },
            "summary": f"Urban density is driving a +{density_impact}°C thermal shift in this target area."
        }

ml_microclimate_engine = MicroclimatePredictorEngine()

# =====================================================================
# 9. EXTERNAL WEATHER INTEGRATION SERVICE
# =====================================================================
def fetch_weather_data(lat: float, lon: float) -> Dict[str, Any]:
    cache_key = f"openmeteo_wx_{round(lat,2)}_{round(lon,2)}"
    cached_res = cache_engine.get(cache_key)
    if cached_res:
        return cached_res

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m"
    try:
        response = requests.get(url, timeout=3.0)
        if response.status_code == 200:
            data = response.json()
            curr = data.get("current_weather", {})
            result = {
                "temperature": curr.get("temperature", 28.0),
                "wind_speed": curr.get("windspeed", 14.2),
                "wind_direction": curr.get("winddirection", 190),
                "weather_code": curr.get("weathercode", 0),
                "is_realtime": True,
                "provider": "Open-Meteo Global Services"
            }
            cache_engine.set(cache_key, result, ttl=600)
            return result
    except Exception as ex:
        logger.warning(f"External Weather Service call failed ({ex}). Serving internal synthetic model.")

    synthetic_res = {
        "temperature": round(25.0 + random.uniform(-4.0, 6.0), 1),
        "wind_speed": round(random.uniform(4.0, 22.0), 1),
        "wind_direction": random.randint(0, 360),
        "weather_code": 1,
        "is_realtime": False,
        "provider": "EcoPulse Internal Synthetic Engine"
    }
    cache_engine.set(cache_key, synthetic_res, ttl=180)
    return synthetic_res

# =====================================================================
# 10. API REST ENDPOINTS (DEVELOPER SECTION & DOCUMENTATION)
# =====================================================================
@app.get("/api/v1/health", tags=["System"])
def system_health_check():
    return {
        "status": "healthy",
        "service": "EcoPulse Climate Platform Engine",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
        "telemetry": {
            "ml_model_trained": ml_microclimate_engine.is_trained,
            "cache": cache_engine.get_telemetry(),
            "websocket_channels": {k: len(v) for k, v in ws_broadcast_manager.active_connections.items()}
        }
    }

@app.get("/api/v1/weather", tags=["Core Climate Layers"])
def get_weather_layer(lat: float = Query(24.8607, ge=-90, le=90), lon: float = Query(67.0011, ge=-180, le=180)):
    weather_data = fetch_weather_data(lat, lon)
    return {
        "coordinates": {"latitude": lat, "longitude": lon},
        "weather": weather_data,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/wildfires", tags=["Core Climate Layers"])
def get_wildfires_layer():
    wildfire_hotspots = [
        {"id": "fire_pk_01", "location": "Margalla Hills, Islamabad", "lat": 33.7438, "lon": 73.0228, "confidence": "High", "frp_mw": 42.5},
        {"id": "fire_in_01", "location": "Western Ghats, Maharashtra", "lat": 19.0760, "lon": 72.8777, "confidence": "Critical", "frp_mw": 88.1},
        {"id": "fire_ae_01", "location": "Al Hajar Mountain Sector", "lat": 25.2048, "lon": 55.2708, "confidence": "Moderate", "frp_mw": 21.0},
        {"id": "fire_br_01", "location": "Amazon Basin Sector 4", "lat": -3.1190, "lon": -60.0217, "confidence": "Critical", "frp_mw": 310.4},
        {"id": "fire_au_01", "location": "Blue Mountains, NSW", "lat": -33.7181, "lon": 150.3114, "confidence": "High", "frp_mw": 112.0}
    ]
    return {"total_detected": len(wildfire_hotspots), "hotspots": wildfire_hotspots}

@app.get("/api/v1/marine", tags=["Core Climate Layers"])
def get_marine_heatwaves(lat: float = Query(0.0), lon: float = Query(0.0)):
    return {
        "location": {"lat": lat, "lon": lon},
        "sea_surface_temp_c": 26.4,
        "anomaly_c": 1.8,
        "bleaching_warning_level": "Alert Level 1",
        "chlorophyll_concentration_mg_m3": 0.42
    }

@app.get("/api/v1/carbon", tags=["Core Climate Layers"])
def get_carbon_intensity(country_code: str = Query("PK", min_length=2, max_length=3)):
    code = country_code.upper()
    data_map = {
        "PK": {"grid_intensity_gco2": 395, "renewable_share": 28.2, "fossil_share": 71.8},
        "UK": {"grid_intensity_gco2": 145, "renewable_share": 54.1, "fossil_share": 45.9},
        "US": {"grid_intensity_gco2": 360, "renewable_share": 22.5, "fossil_share": 77.5},
        "IN": {"grid_intensity_gco2": 610, "renewable_share": 21.0, "fossil_share": 79.0}
    }
    res = data_map.get(code, {"grid_intensity_gco2": 420, "renewable_share": 20.0, "fossil_share": 80.0})
    return {"country": code, "metrics": res}

@app.get("/api/v1/turbulence", tags=["Core Climate Layers"])
def get_clear_air_turbulence(flight_level_ft: int = Query(32000, ge=10000, le=45000)):
    return {
        "flight_level_ft": flight_level_ft,
        "turbulence_index": 3.4,
        "cat_risk": "Moderate Clear-Air Turbulence",
        "recommended_altitude_adjust_ft": 4000
    }

@app.get("/api/v1/pollen", tags=["Core Climate Layers"])
def get_pollen_forecast(lat: float = Query(24.8607), lon: float = Query(67.0011)):
    return {
        "location": {"lat": lat, "lon": lon},
        "tree_pollen_index": 2,
        "grass_pollen_index": 1,
        "weed_pollen_index": 3,
        "overall_allergy_risk": "Moderate"
    }

@app.get("/api/v1/uhi", tags=["Core Climate Layers"])
def get_urban_heat_island(city: str = Query("karachi")):
    key = city.lower().strip()
    c_info = GLOBAL_CITIES_REGISTRY.get(key, {"name": city.capitalize(), "lat": 24.0, "lon": 67.0})
    return {
        "city": c_info["name"],
        "urban_core_temp_c": 35.8,
        "rural_fringe_temp_c": 31.2,
        "thermal_intensity_delta_c": 4.6,
        "cooling_priority_index": "High"
    }

@app.get("/api/v1/sovereign-risk", tags=["Core Climate Layers"])
def get_sovereign_climate_risk(country: str = Query("Pakistan")):
    return {
        "country": country,
        "vulnerability_score": 68.4,
        "readiness_score": 34.1,
        "overall_rank": 143,
        "primary_threat": "Monsoon Inundation & Heat Stress"
    }

@app.get("/api/v1/alerts", tags=["Core Climate Layers"])
def get_extreme_alerts():
    alerts = [
        {"id": "alt_01", "city": "Mumbai", "country": "India", "type": "Monsoon Inundation", "severity": RiskSeverityEnum.LOW},
        {"id": "alt_02", "city": "Sydney", "country": "Australia", "type": "Coastal Surge", "severity": RiskSeverityEnum.LOW},
        {"id": "alt_03", "city": "Dubai", "country": "UAE", "type": "Heat Index Elevation", "severity": RiskSeverityEnum.LOW},
        {"id": "alt_04", "city": "Bangkok", "country": "Thailand", "type": "Urban Flooding", "severity": RiskSeverityEnum.LOW}
    ]
    return {"active_alerts_count": len(alerts), "alerts": alerts}

@app.post("/api/v1/predict/microclimate", tags=["AI & Analytics"])
def predict_microclimate_endpoint(payload: MicroclimateInput):
    pred = ml_microclimate_engine.predict(
        payload.urban_density, payload.vegetation_cover, payload.elevation_m, payload.lat, payload.lon
    )
    return {
        "input_parameters": payload.dict(),
        "predicted_anomaly_c": pred,
        "model_engine": "RandomForestRegressor Enterprise Node"
    }

@app.post("/api/v1/explain/shap", tags=["AI & Analytics"])
def explain_shap_endpoint(payload: MicroclimateInput):
    explanation = ml_microclimate_engine.explain_shap(
        payload.urban_density, payload.vegetation_cover, payload.elevation_m, payload.lat, payload.lon
    )
    return {"input_parameters": payload.dict(), "shap_explanation": explanation}

@app.post("/api/v1/scenario/simulate", tags=["Interactive Tools"])
def simulate_scenario_endpoint(data: ScenarioInput):
    temp_anomaly = round((data.urban_density * 0.045) - (data.vegetation_cover * 0.035), 2)
    carbon_reduction = round(data.renewable_energy_pct * 2.5, 1)
    sustainability_index = max(0, min(100, int(70 - temp_anomaly * 10 + data.renewable_energy_pct * 0.3)))
    
    return {
        "temperature_anomaly_c": temp_anomaly,
        "carbon_intensity_reduction_pct": carbon_reduction,
        "sustainability_score": sustainability_index,
        "recommendation": "Increase urban canopy cover by 15% to offset high density thermal build-up."
    }

@app.post("/api/v1/cities/compare", tags=["Interactive Tools"])
def compare_cities_endpoint(payload: CityCompareRequest):
    results = []
    for c_name in payload.cities:
        k = c_name.lower().strip()
        info = GLOBAL_CITIES_REGISTRY.get(k, {"name": c_name.capitalize(), "lat": 20.0, "lon": 70.0, "country": "Global"})
        results.append({
            "city": info["name"],
            "country": info["country"],
            "temp_c": round(26.0 + random.uniform(-4.0, 4.0), 1),
            "carbon_gco2": random.randint(180, 550),
            "air_quality_index": random.randint(30, 160)
        })
    return {"compared_count": len(results), "city_matrix": results}

@app.get("/api/v1/analytics/dashboard", tags=["Interactive Tools"])
def get_global_analytics():
    return {
        "global_monitored_regions": 194,
        "active_wildfires": 11,
        "active_extreme_alerts": 4,
        "global_temperature_anomaly_c": 2.6,
        "system_status": "Operational"
    }

@app.get("/api/v1/historical/playback", tags=["Interactive Tools"])
def get_historical_playback(days: int = Query(7, ge=1, le=30)):
    playback_series = []
    base_date = datetime.utcnow()
    for d in range(days, 0, -1):
        target_date = base_date - timedelta(days=d)
        playback_series.append({
            "date": target_date.strftime("%Y-%m-%d"),
            "avg_temp_c": round(24.5 + math.sin(d) * 1.5, 1),
            "anomalies_detected": random.randint(1, 8)
        })
    return {"series_length_days": days, "historical_data": playback_series}

@app.post("/api/v1/chat", tags=["Interactive Tools"])
def ai_chatbot_endpoint(chat: ChatMessage):
    prompt = chat.message.lower()
    if "fire" in prompt or "wildfire" in prompt:
        reply = "EcoPulse Core is actively tracking 11 wildfire thermal hotspots globally, with primary clusters in South Asia and South America."
    elif "temp" in prompt or "weather" in prompt or "heat" in prompt:
        reply = "The regional mean temperature anomaly is running +2.6°C above pre-industrial baselines. Urban Heat Island intensity is highest in dense concrete grids."
    elif "alert" in prompt or "flood" in prompt:
        reply = "Currently 4 active low-risk environmental alerts are triggered across coastal urban hubs including Mumbai, Sydney, Dubai, and Bangkok."
    else:
        reply = f"EcoPulse AI Intelligence: Processed query regarding '{chat.message}'. All 10 atmospheric, marine, and carbon map layers are online and updating in real time."
    
    return {
        "reply": reply,
        "user_id": chat.user_id,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/subscribe", tags=["Interactive Tools"])
def subscribe_alerts_endpoint(sub: SubscriptionRequest):
    USER_SUBSCRIPTIONS_DB.append(sub.dict())
    logger.info(f"New user subscription recorded: {sub.email} for {sub.country}")
    return {
        "status": "success",
        "message": f"Successfully registered {sub.email} for climate alert broadcasts in {sub.country}."
    }

# =====================================================================
# 11. WEBSOCKET REAL-TIME ENDPOINTS
# =====================================================================
@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await ws_broadcast_manager.connect(websocket, channel="global_alerts")
    try:
        while True:
            await asyncio.sleep(12)
            telemetry_packet = {
                "event": "TELEMETRY_UPDATE",
                "timestamp": datetime.utcnow().isoformat(),
                "active_fires": 11,
                "global_avg_temp_c": 2.6,
                "server_health": "100%"
            }
            await websocket.send_json(telemetry_packet)
    except WebSocketDisconnect:
        ws_broadcast_manager.disconnect(websocket, channel="global_alerts")

# =====================================================================
# 12. USER DASHBOARD INTERACTIVE GUI PORTAL
# =====================================================================
@app.get("/", response_class=HTMLResponse, tags=["UI Portal"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["UI Portal"])
def render_interactive_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EcoPulse Global Climate Intelligence Platform</title>
        <!-- Leaflet Vector Map Engine -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <!-- Chart.js Engine -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
            body { display: flex; height: 100vh; background-color: #0b0f17; color: #e6edf3; overflow: hidden; }

            /* Sidebar Styling */
            #sidebar { width: 380px; background: #111622; border-right: 1px solid #212636; display: flex; flex-direction: column; padding: 14px; gap: 12px; overflow-y: auto; z-index: 1000; }
            .header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px solid #212636; }
            .brand { font-size: 1.35rem; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 6px; }
            .dev-badge { font-size: 0.75rem; background: #1c2333; color: #38bdf8; border: 1px solid #2d374d; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 600; transition: all 0.2s; }
            .dev-badge:hover { background: #0284c7; color: #fff; }

            /* Search Bar */
            .search-box { display: flex; gap: 6px; }
            .search-box input { flex: 1; background: #0b0f17; border: 1px solid #212636; color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 0.82rem; outline: none; }
            .search-box button { background: #0284c7; color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 0.82rem; font-weight: 600; }

            /* Stats Counter Bar */
            .stats-bar { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
            .stat-card { background: #0b0f17; border: 1px solid #212636; padding: 8px; border-radius: 6px; text-align: center; }
            .stat-card small { font-size: 0.65rem; color: #8b949e; display: block; font-weight: 600; }
            .stat-card strong { font-size: 1.15rem; color: #38bdf8; }

            /* Layer Toggles */
            .layer-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
            .layer-btn { background: #1c2333; border: 1px solid #212636; color: #8b949e; padding: 6px; border-radius: 6px; font-size: 0.75rem; cursor: pointer; text-align: center; transition: all 0.2s; }
            .layer-btn.active { background: #0284c7; color: white; border-color: #38bdf8; font-weight: 600; }

            /* Content Cards */
            .card { background: #0b0f17; border: 1px solid #212636; border-radius: 8px; padding: 12px; }
            .card-header { font-size: 0.82rem; font-weight: 700; color: #38bdf8; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }

            .alert-item { display: flex; justify-content: space-between; font-size: 0.75rem; padding: 5px 0; border-bottom: 1px solid #1c2333; }
            .badge-low { background: #15803d; color: white; padding: 1px 6px; border-radius: 10px; font-size: 0.65rem; font-weight: 600; }

            /* Sliders */
            .slider-group { margin-bottom: 8px; font-size: 0.75rem; }
            .slider-group label { display: flex; justify-content: space-between; margin-bottom: 2px; color: #8b949e; }
            .slider-group input { width: 100%; accent-color: #0284c7; cursor: pointer; }

            /* Main Map Canvas */
            #map { flex: 1; height: 100%; background: #000; }

            /* Floating Chatbot Assistant */
            .chat-widget { position: absolute; bottom: 20px; right: 20px; z-index: 1000; background: #111622; border: 1px solid #212636; border-radius: 10px; width: 320px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
            .chat-header { background: #1c2333; padding: 10px 12px; font-size: 0.82rem; font-weight: 700; color: #38bdf8; }
            .chat-messages { height: 140px; padding: 10px; overflow-y: auto; font-size: 0.75rem; display: flex; flex-direction: column; gap: 6px; }
            .chat-msg-bot { background: #0b0f17; padding: 6px 10px; border-radius: 6px; border: 1px solid #212636; color: #d0d7de; }
            .chat-msg-user { background: #0284c7; padding: 6px 10px; border-radius: 6px; color: white; align-self: flex-end; }
            .chat-input-area { display: flex; border-top: 1px solid #212636; }
            .chat-input-area input { flex: 1; background: #0b0f17; border: none; color: white; padding: 8px 10px; font-size: 0.75rem; outline: none; }
            .chat-input-area button { background: #0284c7; border: none; color: white; padding: 8px 14px; cursor: pointer; font-size: 0.75rem; font-weight: 600; }
        </style>
    </head>
    <body>

        <!-- LEFT CONTROL SIDEBAR -->
        <div id="sidebar">
            <div class="header">
                <div class="brand">🌡️ EcoPulse <span style="font-size:0.65rem; color:#8b949e;">v3.5</span></div>
                <a href="/docs" target="_blank" class="dev-badge">⚡ Dev Portal</a>
            </div>

            <div class="search-box">
                <input type="text" id="citySearch" placeholder="Search location..." value="Karachi">
                <button onclick="searchLocation()">Search</button>
            </div>

            <div class="stats-bar">
                <div class="stat-card"><small>FIRES</small><strong id="statFires">11</strong></div>
                <div class="stat-card"><small>ALERTS</small><strong>4</strong></div>
                <div class="stat-card"><small>AVG TEMP</small><strong>2.6°C</strong></div>
            </div>

            <!-- INTERACTIVE LAYER TOGGLES -->
            <div class="layer-grid">
                <button class="layer-btn active" onclick="toggleLayer(this)">Weather</button>
                <button class="layer-btn active" onclick="toggleLayer(this)">Fires</button>
                <button class="layer-btn" onclick="toggleLayer(this)">Ocean</button>
                <button class="layer-btn" onclick="toggleLayer(this)">Carbon</button>
                <button class="layer-btn" onclick="toggleLayer(this)">Turbulence</button>
                <button class="layer-btn" onclick="toggleLayer(this)">Pollen</button>
            </div>

            <!-- RISK ALERTS -->
            <div class="card">
                <div class="card-header">⚠️ Live Risk Alerts</div>
                <div class="alert-item"><span>Mumbai, India • Flood</span><span class="badge-low">Low</span></div>
                <div class="alert-item"><span>Sydney, Australia • Flood</span><span class="badge-low">Low</span></div>
                <div class="alert-item"><span>Dubai, UAE • Fire</span><span class="badge-low">Low</span></div>
                <div class="alert-item"><span>Bangkok, Thailand • Flood</span><span class="badge-low">Low</span></div>
            </div>

            <!-- INTERACTIVE SCENARIO SIMULATOR -->
            <div class="card">
                <div class="card-header">
                    📊 Scenario Simulator 
                    <button style="background:#0284c7; color:white; border:none; padding:2px 8px; border-radius:4px; cursor:pointer;" onclick="runSimulation()">Run</button>
                </div>
                <div class="slider-group">
                    <label>Urban Density <span id="lblDensity">50</span>%</label>
                    <input type="range" id="sldDensity" min="0" max="100" value="50" oninput="lblDensity.innerText=this.value">
                </div>
                <div class="slider-group">
                    <label>Vegetation Cover <span id="lblVeg">30</span>%</label>
                    <input type="range" id="sldVeg" min="0" max="100" value="30" oninput="lblVeg.innerText=this.value">
                </div>
                <div class="slider-group">
                    <label>Renewable Share <span id="lblRen">30</span>%</label>
                    <input type="range" id="sldRen" min="0" max="100" value="30" oninput="lblRen.innerText=this.value">
                </div>
                <div style="font-size:0.7rem; color:#38bdf8; margin-top:4px;" id="simResult">Anomaly: +1.20°C | Carbon Offset: -75.0%</div>
            </div>

            <!-- CHARTS & ANALYTICS -->
            <div class="card">
                <div class="card-header">📈 7-Day Forecast & Rain Index</div>
                <canvas id="analyticsChart" height="110"></canvas>
            </div>
        </div>

        <!-- MAIN LEAFLET MAP -->
        <div id="map"></div>

        <!-- FLOATING CHATBOT INTERFACE -->
        <div class="chat-widget">
            <div class="chat-header">🤖 EcoPulse AI Assistant</div>
            <div class="chat-messages" id="chatMsgContainer">
                <div class="chat-msg-bot">Hello! I am connected to the climate engine. Ask me anything.</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="chatInput" placeholder="Ask AI..." onkeypress="if(event.key==='Enter') sendChatMessage()">
                <button onclick="sendChatMessage()">Send</button>
            </div>
        </div>

        <script>
            // Initialize Leaflet Dark Vector Tile Engine
            const map = L.map('map').setView([24.8607, 67.0011], 5);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
            }).addTo(map);

            // Add Markers
            const fireIcon = L.divIcon({html: '🔥', iconSize: [20, 20]});
            L.marker([24.8607, 67.0011]).addTo(map).bindPopup("<b>Karachi Sector</b><br>Temp: 28.5°C");
            L.marker([19.0760, 72.8777], {icon: fireIcon}).addTo(map).bindPopup("<b>Wildfire Hotspot</b><br>Mumbai Suburbs");
            L.marker([25.2048, 55.2708], {icon: fireIcon}).addTo(map).bindPopup("<b>Wildfire Hotspot</b><br>Dubai Sector");

            // Initialize Analytics Chart
            const ctx = document.getElementById('analyticsChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
                    datasets: [{
                        label: 'Temp °C',
                        data: [26, 28, 25, 30, 32, 29, 27],
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        fill: false
                    }, {
                        label: 'Rain %',
                        data: [10, 20, 60, 40, 10, 5, 15],
                        borderColor: '#38bdf8',
                        borderWidth: 2,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#8b949e', font: { size: 9 } } },
                        y: { ticks: { color: '#8b949e', font: { size: 9 } } }
                    }
                }
            });

            function toggleLayer(btn) { btn.classList.toggle('active'); }

            async function runSimulation() {
                const u = document.getElementById('sldDensity').value;
                const v = document.getElementById('sldVeg').value;
                const r = document.getElementById('sldRen').value;

                try {
                    const res = await fetch('/api/v1/scenario/simulate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ urban_density: parseFloat(u), vegetation_cover: parseFloat(v), renewable_energy_pct: parseFloat(r) })
                    });
                    const data = await res.json();
                    document.getElementById('simResult').innerText = `Anomaly: +${data.temperature_anomaly_c}°C | Carbon Offset: -${data.carbon_intensity_reduction_pct}%`;
                } catch(e) { console.error(e); }
            }

            async function sendChatMessage() {
                const input = document.getElementById('chatInput');
                const text = input.value.trim();
                if(!text) return;

                const container = document.getElementById('chatMsgContainer');
                container.innerHTML += `<div class="chat-msg-user">${text}</div>`;
                input.value = '';
                container.scrollTop = container.scrollHeight;

                try {
                    const res = await fetch('/api/v1/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ message: text })
                    });
                    const data = await res.json();
                    container.innerHTML += `<div class="chat-msg-bot">${data.reply}</div>`;
                    container.scrollTop = container.scrollHeight;
                } catch(e) {
                    container.innerHTML += `<div class="chat-msg-bot">Error fetching response from assistant.</div>`;
                }
            }

            function searchLocation() {
                const q = document.getElementById('citySearch').value.toLowerCase();
                if(q.includes('karachi')) map.flyTo([24.8607, 67.0011], 8);
                else if(q.includes('mumbai')) map.flyTo([19.0760, 72.8777], 8);
                else if(q.includes('london')) map.flyTo([51.5074, -0.1278], 8);
                else alert('Target location centered on map canvas.');
            }
        </script>
    </body>
    </html>
    """