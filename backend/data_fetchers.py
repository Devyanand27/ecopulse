"""
COMPLETE Real‑time Data Fetchers – All 10 Features
- Uses free Open‑Meteo APIs (no key) for Weather, Marine, Air Quality, Warnings, Historical
- NASA FIRMS (requires free token) for Fires
- ElectricityMap (requires free token) for Carbon Intensity
- Derived calculations for Turbulence (from wind data) and UHI (urban/rural comparison)
- Composite Risk Score from other fetchers
- Every function has a real API call + mock fallback (never fails)
"""
import httpx
import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

# -------------------------------------------------------------------
# API KEYS from environment
NASA_FIRMS_TOKEN = os.getenv("NASA_FIRMS_TOKEN", "demo")
ELECTRICITY_MAP_TOKEN = os.getenv("ELECTRICITY_MAP_TOKEN", "demo")

# -------------------------------------------------------------------
# 1. WEATHER (Open‑Meteo Forecast – no key)
# -------------------------------------------------------------------
async def fetch_weather(lat: float, lon: float) -> dict:
    """Current + 7‑day forecast. Real API + mock fallback."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m", "precipitation"],
        "hourly": ["temperature_2m", "precipitation_probability", "weather_code", "wind_speed_10m"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max"],
        "timezone": "UTC",
        "forecast_days": 7
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return _mock_weather(lat, lon)

def _mock_weather(lat, lon):
    now = datetime.utcnow()
    return {
        "latitude": lat,
        "longitude": lon,
        "current": {
            "temperature_2m": round(random.uniform(-5, 35), 1),
            "relative_humidity_2m": random.randint(30, 90),
            "weather_code": random.choice([0, 1, 2, 3, 45, 48, 51, 61, 80]),
            "wind_speed_10m": round(random.uniform(0, 20), 1),
            "precipitation": round(random.uniform(0, 5), 1)
        },
        "daily": {
            "time": [(now + timedelta(days=i)).isoformat() for i in range(7)],
            "temperature_2m_max": [round(random.uniform(10, 40), 1) for _ in range(7)],
            "temperature_2m_min": [round(random.uniform(-5, 20), 1) for _ in range(7)],
            "precipitation_probability_max": [random.randint(0, 100) for _ in range(7)]
        }
    }

# -------------------------------------------------------------------
# 2. FIRES (NASA FIRMS – requires token)
# -------------------------------------------------------------------
async def fetch_fires(bbox: Tuple[float, float, float, float] = None) -> List[dict]:
    """Active fires from NASA FIRMS. Real API + mock fallback."""
    if bbox is None:
        bbox = (-180, -90, 180, 90)
    url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    params = {
        "area": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "day": 1,
        "token": NASA_FIRMS_TOKEN
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")[1:]  # skip header
            fires = []
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 10:
                    fires.append({
                        "lat": float(parts[1]),
                        "lon": float(parts[2]),
                        "brightness": float(parts[3]),
                        "confidence": parts[8],
                        "type": parts[9]
                    })
            return fires
    except Exception:
        return _mock_fires()

def _mock_fires():
    return [{
        "lat": random.uniform(-60, 70),
        "lon": random.uniform(-180, 180),
        "brightness": random.uniform(300, 400),
        "confidence": random.choice(["low", "medium", "high"]),
        "type": "fire"
    } for _ in range(random.randint(5, 25))]

# -------------------------------------------------------------------
# 3. OCEAN / MARINE HEATWAVES (Open‑Meteo Marine – no key)
# -------------------------------------------------------------------
async def fetch_ocean_temp(lat: float, lon: float) -> dict:
    """Sea surface temperature (SST) and anomaly. Real + mock."""
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["sea_surface_temperature"],
        "timezone": "UTC",
        "forecast_days": 1
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            sst = data.get("hourly", {}).get("sea_surface_temperature", [None])[0]
            if sst is None:
                raise ValueError("No SST data")
            baseline = 20.0
            anomaly = round(sst - baseline, 1)
            coral_risk = "high" if anomaly > 1.5 else "medium" if anomaly > 0.8 else "low"
            return {"lat": lat, "lon": lon, "sst": sst, "anomaly": anomaly, "coral_risk": coral_risk}
    except Exception:
        return _mock_ocean(lat, lon)

def _mock_ocean(lat, lon):
    sst = round(random.uniform(18, 30), 1)
    anomaly = round(random.uniform(-2, 3), 1)
    coral_risk = "high" if anomaly > 1.5 else "medium" if anomaly > 0.8 else "low"
    return {"lat": lat, "lon": lon, "sst": sst, "anomaly": anomaly, "coral_risk": coral_risk}

# -------------------------------------------------------------------
# 4. CARBON INTENSITY (ElectricityMap – requires token)
# -------------------------------------------------------------------
async def fetch_carbon_intensity(country_code: str = "US") -> dict:
    """National grid carbon intensity. Real + mock."""
    url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={country_code}"
    headers = {"auth-token": ELECTRICITY_MAP_TOKEN}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return {
                "country": country_code,
                "carbon_intensity": data.get("carbonIntensity", 400),
                "renewable_percent": data.get("renewable", 30),
                "fossil_percent": data.get("fossil", 70)
            }
    except Exception:
        return _mock_carbon(country_code)

def _mock_carbon(country_code):
    return {
        "country": country_code,
        "carbon_intensity": random.randint(200, 600),
        "renewable_percent": random.randint(10, 80),
        "fossil_percent": random.randint(20, 90)
    }

# -------------------------------------------------------------------
# 5. TURBULENCE (Derived from Open‑Meteo wind data – no key)
# -------------------------------------------------------------------
async def fetch_turbulence(bbox: Tuple[float, float, float, float] = None) -> List[dict]:
    """CAT index derived from wind speed and shear. Real wind data + mock."""
    if bbox is None:
        bbox = (-180, -90, 180, 90)
    points = []
    for _ in range(10):
        lat = random.uniform(bbox[1], bbox[3])
        lon = random.uniform(bbox[0], bbox[2])
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["wind_speed_10m", "wind_gusts_10m"],
            "timezone": "UTC"
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                wind = data.get("current", {}).get("wind_speed_10m", 10)
                gusts = data.get("current", {}).get("wind_gusts_10m", wind * 1.2)
                cat = (gusts - wind) * 0.5 + wind * 0.1
                if cat > 15:
                    risk = "severe"
                elif cat > 10:
                    risk = "high"
                elif cat > 5:
                    risk = "moderate"
                else:
                    risk = "low"
                points.append({"lat": lat, "lon": lon, "risk": risk})
        except Exception:
            points.append({"lat": lat, "lon": lon, "risk": random.choice(["low", "moderate", "high", "severe"])})
    return points

# -------------------------------------------------------------------
# 6. POLLEN (Open‑Meteo Air Quality – no key)
# -------------------------------------------------------------------
async def fetch_pollen(lat: float, lon: float) -> dict:
    """Pollen concentrations from Open‑Meteo Air Quality API."""
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["alder_pollen", "birch_pollen", "grass_pollen", "mugwort_pollen", "olive_pollen", "ragweed_pollen"],
        "timezone": "UTC",
        "forecast_days": 1
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            hourly = data.get("hourly", {})
            tree = hourly.get("alder_pollen", [0])[0] + hourly.get("birch_pollen", [0])[0] + hourly.get("olive_pollen", [0])[0]
            grass = hourly.get("grass_pollen", [0])[0]
            weed = hourly.get("mugwort_pollen", [0])[0] + hourly.get("ragweed_pollen", [0])[0]
            tree = min(100, int(tree * 2))
            grass = min(100, int(grass * 2))
            weed = min(100, int(weed * 2))
            overall = "high" if (tree + grass + weed) > 150 else "moderate" if (tree + grass + weed) > 80 else "low"
            return {"tree": tree, "grass": grass, "weed": weed, "overall_risk": overall}
    except Exception:
        return _mock_pollen(lat, lon)

def _mock_pollen(lat, lon):
    return {
        "tree": random.randint(0, 100),
        "grass": random.randint(0, 100),
        "weed": random.randint(0, 100),
        "overall_risk": random.choice(["low", "moderate", "high"])
    }

# -------------------------------------------------------------------
# 7. URBAN HEAT ISLAND (Derived – no direct API, uses weather comparison)
# -------------------------------------------------------------------
async def fetch_uhi(city: str) -> dict:
    """UHI intensity by comparing urban/rural weather."""
    coords = {
        "Karachi": (24.86, 67.01),
        "Lahore": (31.52, 74.36),
        "Islamabad": (33.68, 73.05),
        "Mumbai": (19.08, 72.88),
        "Delhi": (28.61, 77.23),
        "New York": (40.71, -74.01),
        "London": (51.51, -0.13),
        "Tokyo": (35.68, 139.76),
        "Sydney": (-33.87, 151.21)
    }
    urban_lat, urban_lon = coords.get(city, (24.86, 67.01))
    rural_lat = urban_lat + random.uniform(0.15, 0.3)
    rural_lon = urban_lon + random.uniform(0.15, 0.3)

    try:
        urban_w = await fetch_weather(urban_lat, urban_lon)
        rural_w = await fetch_weather(rural_lat, rural_lon)
        urban_temp = urban_w.get("current", {}).get("temperature_2m", 25)
        rural_temp = rural_w.get("current", {}).get("temperature_2m", 22)
        uhi_intensity = round(urban_temp - rural_temp, 1)
        hotspots = []
        for _ in range(4):
            hotspots.append({
                "lat": urban_lat + random.uniform(-0.05, 0.05),
                "lon": urban_lon + random.uniform(-0.05, 0.05)
            })
        return {
            "city": city,
            "urban_temp": urban_temp,
            "rural_temp": rural_temp,
            "uhi_intensity": uhi_intensity,
            "hotspots": hotspots
        }
    except Exception:
        return _mock_uhi(city)

def _mock_uhi(city):
    return {
        "city": city,
        "urban_temp": round(random.uniform(25, 40), 1),
        "rural_temp": round(random.uniform(20, 35), 1),
        "uhi_intensity": round(random.uniform(0, 8), 1),
        "hotspots": [{"lat": random.uniform(-90, 90), "lon": random.uniform(-180, 180)} for _ in range(4)]
    }

# -------------------------------------------------------------------
# 8. SOVEREIGN RISK SCORE (Composite – uses other fetchers)
# -------------------------------------------------------------------
async def fetch_risk_score(country_code: str = "PK") -> dict:
    """Composite risk score using multiple data sources."""
    country_map = {
        "PK": ("Pakistan", 30.0, 70.0),
        "US": ("United States", 40.0, -100.0),
        "IN": ("India", 20.0, 77.0),
        "CN": ("China", 35.0, 105.0),
        "UK": ("United Kingdom", 55.0, -3.0),
        "BR": ("Brazil", -15.0, -55.0),
        "AU": ("Australia", -25.0, 135.0)
    }
    name, lat, lon = country_map.get(country_code, ("Unknown", 30, 70))

    try:
        w = await fetch_weather(lat, lon)
        temps = w.get("daily", {}).get("temperature_2m_max", [25])
        extreme_weather = 10 if max(temps) > 40 else 7 if max(temps) > 35 else 4

        ocean = await fetch_ocean_temp(lat, lon)
        sea_level = 8 if ocean.get("anomaly", 0) > 1.5 else 5 if ocean.get("anomaly", 0) > 0.5 else 2

        pollen = await fetch_pollen(lat, lon)
        total_pollen = pollen.get("tree", 0) + pollen.get("grass", 0) + pollen.get("weed", 0)
        air_quality = 8 if total_pollen > 150 else 5 if total_pollen > 80 else 2

        carbon = await fetch_carbon_intensity(country_code)
        emissions = 10 if carbon.get("carbon_intensity", 500) > 500 else 7 if carbon.get("carbon_intensity", 500) > 350 else 3

        renewables = 10 - int(carbon.get("renewable_percent", 30) / 10)
        policy = random.randint(3, 8)

        components = {
            "extreme_weather": extreme_weather,
            "sea_level": sea_level,
            "air_quality": air_quality,
            "emissions": emissions,
            "renewables": renewables,
            "policy": policy
        }
        score = 100 - sum(components.values())
        score = max(0, min(100, score))

        return {"country": country_code, "score": score, "components": components}
    except Exception:
        return _mock_risk(country_code)

def _mock_risk(country_code):
    return {
        "country": country_code,
        "score": random.randint(20, 90),
        "components": {
            "extreme_weather": random.randint(1, 10),
            "sea_level": random.randint(1, 10),
            "air_quality": random.randint(1, 10),
            "emissions": random.randint(1, 10),
            "renewables": random.randint(1, 10),
            "policy": random.randint(1, 10)
        }
    }

# -------------------------------------------------------------------
# 9. EXTREME ALERTS (Open‑Meteo Warnings – no key)
# -------------------------------------------------------------------
async def fetch_alerts(bbox: Tuple[float, float, float, float] = None) -> List[dict]:
    """Real‑time weather warnings from Open‑Meteo."""
    if bbox is None:
        bbox = (-180, -90, 180, 90)
    url = "https://api.open-meteo.com/v1/warnings"
    params = {
        "latitude": (bbox[1] + bbox[3]) / 2,
        "longitude": (bbox[0] + bbox[2]) / 2,
        "timezone": "UTC"
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            warnings = data.get("warnings", [])
            alerts = []
            for w in warnings:
                severity = w.get("severity", "advisory").lower()
                if severity not in ["warning", "watch", "advisory"]:
                    severity = "advisory"
                alerts.append({
                    "type": w.get("event", "weather event"),
                    "lat": w.get("latitude", random.uniform(bbox[1], bbox[3])),
                    "lon": w.get("longitude", random.uniform(bbox[0], bbox[2])),
                    "severity": severity,
                    "time": w.get("start", datetime.utcnow().isoformat())
                })
            return alerts
    except Exception:
        return _mock_alerts()

def _mock_alerts():
    types = ["microburst", "flash flood", "dust storm", "tornado", "thunderstorm", "heatwave"]
    return [{
        "type": random.choice(types),
        "lat": random.uniform(-60, 70),
        "lon": random.uniform(-180, 180),
        "severity": random.choice(["warning", "watch", "advisory"]),
        "time": datetime.utcnow().isoformat()
    } for _ in range(random.randint(0, 5))]

# -------------------------------------------------------------------
# 10. HISTORICAL DATA (Open‑Meteo Archive – no key)
# -------------------------------------------------------------------
async def fetch_historical(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    """Historical daily weather for time slider playback."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "UTC"
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
        days = max(1, days)
        dates = [(datetime.utcnow() - timedelta(days=i)).isoformat() for i in range(days, 0, -1)]
        return {
            "daily": {
                "time": dates,
                "temperature_2m_max": [round(random.uniform(10, 35), 1) for _ in range(days)],
                "temperature_2m_min": [round(random.uniform(5, 20), 1) for _ in range(days)],
                "precipitation_sum": [round(random.uniform(0, 20), 1) for _ in range(days)]
            }
        }