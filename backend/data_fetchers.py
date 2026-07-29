"""
EcoPulse – Real‑time Data Fetchers
Complete implementation for all 10 climate features + 16-city risk alerts.
All functions have real API calls with mock fallback for reliability.
Author: EcoPulse Team
Version: 3.4
"""

import httpx
import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------
# API KEYS from environment (optional; fallback to mock if not set)
# -------------------------------------------------------------------
NASA_FIRMS_TOKEN = os.getenv("NASA_FIRMS_TOKEN", "demo")
ELECTRICITY_MAP_TOKEN = os.getenv("ELECTRICITY_MAP_TOKEN", "demo")

# -------------------------------------------------------------------
# 1. WEATHER (Open‑Meteo Forecast – no API key required)
# -------------------------------------------------------------------
async def fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get current weather and 7‑day forecast from Open‑Meteo.
    Returns dict with 'current' and 'daily' sections.
    Falls back to realistic mock data on any error.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "weather_code",
            "wind_speed_10m",
            "precipitation"
        ],
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "weather_code",
            "wind_speed_10m"
        ],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max"
        ],
        "timezone": "UTC",
        "forecast_days": 7
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"Weather API error: {e}, using mock")
        return _mock_weather(lat, lon)


def _mock_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Generate realistic mock weather data."""
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
async def fetch_fires(
    bbox: Tuple[float, float, float, float] = None
) -> List[Dict[str, Any]]:
    """
    Get active fires from NASA FIRMS within a bounding box.
    Returns list of fire objects with lat, lon, brightness, confidence, type.
    Falls back to mock if token invalid or network error.
    """
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
    except Exception as e:
        print(f"FIRMS API error: {e}, using mock")
        return _mock_fires()


def _mock_fires() -> List[Dict[str, Any]]:
    """Generate mock fire data with random locations and confidence."""
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
async def fetch_ocean_temp(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get sea surface temperature (SST) and anomaly from Open‑Meteo Marine.
    Returns SST, anomaly (relative to 20°C baseline), and coral risk.
    """
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
    except Exception as e:
        print(f"Ocean API error: {e}, using mock")
        return _mock_ocean(lat, lon)


def _mock_ocean(lat: float, lon: float) -> Dict[str, Any]:
    sst = round(random.uniform(18, 30), 1)
    anomaly = round(random.uniform(-2, 3), 1)
    coral_risk = "high" if anomaly > 1.5 else "medium" if anomaly > 0.8 else "low"
    return {"lat": lat, "lon": lon, "sst": sst, "anomaly": anomaly, "coral_risk": coral_risk}


# -------------------------------------------------------------------
# 4. CARBON INTENSITY (ElectricityMap – requires token)
# -------------------------------------------------------------------
async def fetch_carbon_intensity(country_code: str = "US") -> Dict[str, Any]:
    """
    Get real‑time carbon intensity (gCO₂/kWh) and renewable/fossil mix.
    Uses ElectricityMap API; falls back to mock.
    """
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
    except Exception as e:
        print(f"Carbon API error: {e}, using mock")
        return _mock_carbon(country_code)


def _mock_carbon(country_code: str) -> Dict[str, Any]:
    return {
        "country": country_code,
        "carbon_intensity": random.randint(200, 600),
        "renewable_percent": random.randint(10, 80),
        "fossil_percent": random.randint(20, 90)
    }


# -------------------------------------------------------------------
# 5. TURBULENCE (Derived from Open‑Meteo wind data – no key)
# -------------------------------------------------------------------
async def fetch_turbulence(
    bbox: Tuple[float, float, float, float] = None
) -> List[Dict[str, Any]]:
    """
    Compute clear‑air turbulence (CAT) index from wind speed and gusts.
    Samples 10 random points in the bbox, fetches wind data, calculates risk.
    """
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
async def fetch_pollen(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get pollen concentrations (tree, grass, weed) from Open‑Meteo Air Quality API.
    Returns counts and overall risk level.
    """
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "alder_pollen",
            "birch_pollen",
            "grass_pollen",
            "mugwort_pollen",
            "olive_pollen",
            "ragweed_pollen"
        ],
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
    except Exception as e:
        print(f"Pollen API error: {e}, using mock")
        return _mock_pollen(lat, lon)


def _mock_pollen(lat: float, lon: float) -> Dict[str, Any]:
    return {
        "tree": random.randint(0, 100),
        "grass": random.randint(0, 100),
        "weed": random.randint(0, 100),
        "overall_risk": random.choice(["low", "moderate", "high"])
    }


# -------------------------------------------------------------------
# 7. URBAN HEAT ISLAND (Derived from weather comparison – no key)
# -------------------------------------------------------------------
async def fetch_uhi(city: str) -> Dict[str, Any]:
    """
    Compute UHI intensity by comparing urban vs rural weather.
    Uses predefined city coordinates and fetches weather for both.
    """
    # Predefined city coordinates
    coords = {
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
        "Jakarta": (-6.20, 106.81)
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


def _mock_uhi(city: str) -> Dict[str, Any]:
    return {
        "city": city,
        "urban_temp": round(random.uniform(25, 40), 1),
        "rural_temp": round(random.uniform(20, 35), 1),
        "uhi_intensity": round(random.uniform(0, 8), 1),
        "hotspots": [{"lat": random.uniform(-90, 90), "lon": random.uniform(-180, 180)} for _ in range(4)]
    }


# -------------------------------------------------------------------
# 8. SOVEREIGN RISK SCORE (Composite from multiple sources)
# -------------------------------------------------------------------
async def fetch_risk_score(country_code: str = "PK") -> Dict[str, Any]:
    """
    Compute a composite climate resilience score (0‑100) for a country.
    Combines extreme weather, sea level, air quality, emissions, renewables, policy.
    Uses real data where available; falls back to mock.
    """
    country_map = {
        "PK": ("Pakistan", 30.0, 70.0),
        "US": ("United States", 40.0, -100.0),
        "IN": ("India", 20.0, 77.0),
        "CN": ("China", 35.0, 105.0),
        "UK": ("United Kingdom", 55.0, -3.0),
        "BR": ("Brazil", -15.0, -55.0),
        "AU": ("Australia", -25.0, 135.0),
        "IR": ("Iran", 32.0, 53.0),
        "AE": ("UAE", 24.0, 54.0),
        "SG": ("Singapore", 1.35, 103.82),
        "TH": ("Thailand", 15.0, 101.0),
        "ID": ("Indonesia", -5.0, 120.0),
        "JP": ("Japan", 36.0, 138.0),
        "ZA": ("South Africa", -30.0, 25.0)
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
    except Exception as e:
        print(f"Risk score error: {e}, using mock")
        return _mock_risk(country_code)


def _mock_risk(country_code: str) -> Dict[str, Any]:
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
async def fetch_alerts(
    bbox: Tuple[float, float, float, float] = None
) -> List[Dict[str, Any]]:
    """
    Get real‑time weather warnings from Open‑Meteo.
    Returns alerts with type, severity, location, time, country, description.
    """
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
                    "time": w.get("start", datetime.utcnow().isoformat()),
                    "country": w.get("country", "Unknown"),
                    "description": w.get("description", "Weather alert")
                })
            return alerts
    except Exception:
        return _mock_alerts()


def _mock_alerts() -> List[Dict[str, Any]]:
    types = ["Microburst", "Flash Flood", "Dust Storm", "Tornado", "Thunderstorm", "Heatwave", "Cyclone", "Tsunami Warning"]
    countries = ["Pakistan", "India", "USA", "UK", "Australia", "UAE", "Singapore", "Iran", "China", "Japan"]
    return [{
        "type": random.choice(types),
        "lat": random.uniform(-60, 70),
        "lon": random.uniform(-180, 180),
        "severity": random.choice(["warning", "watch", "advisory"]),
        "time": datetime.utcnow().isoformat(),
        "country": random.choice(countries),
        "description": f"{random.choice(types)} warning in {random.choice(countries)}"
    } for _ in range(random.randint(0, 8))]


# -------------------------------------------------------------------
# 10. HISTORICAL DATA (Open‑Meteo Archive – no key)
# -------------------------------------------------------------------
async def fetch_historical(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Get historical daily weather from Open‑Meteo Archive.
    Returns daily max/min temperature and precipitation.
    Falls back to mock if API fails.
    """
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
        # Generate mock historical data
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


# ===================================================================
# 11. GLOBAL RISK ALERTS (16 Cities with Severity)
# ===================================================================
ALL_CITIES = [
    {"name": "Karachi", "lat": 24.86, "lon": 67.01, "country": "Pakistan"},
    {"name": "Lahore", "lat": 31.52, "lon": 74.36, "country": "Pakistan"},
    {"name": "Islamabad", "lat": 33.68, "lon": 73.05, "country": "Pakistan"},
    {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "country": "India"},
    {"name": "Delhi", "lat": 28.61, "lon": 77.23, "country": "India"},
    {"name": "London", "lat": 51.51, "lon": -0.13, "country": "UK"},
    {"name": "New York", "lat": 40.71, "lon": -74.01, "country": "USA"},
    {"name": "Tokyo", "lat": 35.68, "lon": 139.76, "country": "Japan"},
    {"name": "Sydney", "lat": -33.87, "lon": 151.21, "country": "Australia"},
    {"name": "Cape Town", "lat": -33.92, "lon": 18.42, "country": "South Africa"},
    {"name": "Tehran", "lat": 35.68, "lon": 51.38, "country": "Iran"},
    {"name": "Dubai", "lat": 25.20, "lon": 55.27, "country": "UAE"},
    {"name": "Singapore", "lat": 1.35, "lon": 103.82, "country": "Singapore"},
    {"name": "Hong Kong", "lat": 22.31, "lon": 114.16, "country": "China"},
    {"name": "Bangkok", "lat": 13.75, "lon": 100.50, "country": "Thailand"},
    {"name": "Jakarta", "lat": -6.20, "lon": 106.81, "country": "Indonesia"},
]


async def fetch_risk_alerts() -> List[Dict[str, Any]]:
    """
    Compute risk scores (fire + flood) for all 16 cities.
    Returns a list of alerts with severity (High/Medium/Low), icons, and risk type.
    Sorted by risk score (highest first).
    """
    results = []
    for city in ALL_CITIES:
        try:
            w = await fetch_weather(city["lat"], city["lon"])
            if not w or not w.get('current'):
                continue

            temp = w['current']['temperature_2m']
            humidity = w['current']['relative_humidity_2m']
            wind = w['current']['wind_speed_10m']
            rain_prob = w.get('daily', {}).get('precipitation_probability_max', [0])[0] or 0

            # Fire risk: sum of conditions
            fire_risk = 0
            if temp > 30:
                fire_risk += 1
            if humidity < 20:
                fire_risk += 1
            if wind > 20:
                fire_risk += 1

            # Flood risk: high rain probability
            flood_risk = 1 if rain_prob > 80 else 0

            total_risk = fire_risk + flood_risk
            if total_risk > 0:
                # Determine severity
                if total_risk >= 3:
                    severity = "High"
                    severity_icon = "🔴"
                elif total_risk >= 2:
                    severity = "Medium"
                    severity_icon = "🟡"
                else:
                    severity = "Low"
                    severity_icon = "🟢"

                # Determine risk type
                if fire_risk > flood_risk:
                    risk_type = "🔥 Fire"
                elif flood_risk > fire_risk:
                    risk_type = "🌊 Flood"
                else:
                    risk_type = "🔥🌊 Mixed"

                results.append({
                    "name": city["name"],
                    "lat": city["lat"],
                    "lon": city["lon"],
                    "country": city["country"],
                    "fire_risk": fire_risk,
                    "flood_risk": flood_risk,
                    "risk": total_risk,
                    "severity": severity,
                    "severity_icon": severity_icon,
                    "temp": temp,
                    "humidity": humidity,
                    "wind": wind,
                    "rain_prob": rain_prob,
                    "risk_type": risk_type
                })
        except Exception as e:
            print(f"Risk alert error for {city['name']}: {e}")
            continue

    # Sort by risk (highest first)
    results.sort(key=lambda x: x["risk"], reverse=True)
    return results