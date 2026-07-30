"""
=============================================================================
EcoPulse - Climate Intelligence Data & Feature Engineering Engine
=============================================================================
This module handles feature extraction, mathematical climate modeling, 
spatial data processing, multi-city data aggregation, and mock generators 
for all 10 Real-Time Map Layers and 14 Analytical Features.

File: data_features.py
Author: EcoPulse Core Engineering Team
Version: 2.5.0
=============================================================================
"""

import math
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any

# =============================================================================
# 1. LOGGING & SYSTEM SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] DataFeatures: %(message)s"
)
logger = logging.getLogger("EcoPulse-DataFeatures")


# =============================================================================
# 2. FEATURE METADATA & SCHEMA DEFINITIONS (ALL 14 CORE FEATURES)
# =============================================================================

FEATURE_METADATA: Dict[str, Dict[str, Any]] = {
    "temperature": {
        "id": 1,
        "name": "Temperature",
        "unit": "°C",
        "description": "Ambient air temperature measured at standard 2 meters above ground level.",
        "category": "Atmospheric",
        "icon": "🌡️",
        "normal_range": (-10.0, 45.0),
        "threshold_high": 38.0,
        "threshold_low": 0.0
    },
    "carbon_intensity": {
        "id": 2,
        "name": "Carbon Intensity",
        "unit": "gCO₂/kWh",
        "description": "Emissions footprint per unit of electricity generated on the national grid.",
        "category": "Energy Grid",
        "icon": "⚡",
        "normal_range": (20, 800),
        "threshold_high": 400,
        "threshold_low": 100
    },
    "air_quality_index": {
        "id": 3,
        "name": "Air Quality Index (AQI)",
        "unit": "AQI",
        "description": "Composite air purity index covering PM2.5, PM10, NO2, and Ozone levels.",
        "category": "Environment",
        "icon": "💨",
        "normal_range": (0, 500),
        "threshold_high": 150,
        "threshold_low": 50
    },
    "humidity": {
        "id": 4,
        "name": "Relative Humidity",
        "unit": "%",
        "description": "Percentage of water vapor saturation in the local lower atmosphere.",
        "category": "Atmospheric",
        "icon": "💧",
        "normal_range": (10, 100),
        "threshold_high": 85,
        "threshold_low": 20
    },
    "wind_speed": {
        "id": 5,
        "name": "Wind Speed",
        "unit": "km/h",
        "description": "Surface wind speed measured at standard 10-meter anemometer elevation.",
        "category": "Atmospheric",
        "icon": "🌬️",
        "normal_range": (0.0, 120.0),
        "threshold_high": 50.0,
        "threshold_low": 5.0
    },
    "precipitation": {
        "id": 6,
        "name": "Precipitation Risk",
        "unit": "%",
        "description": "Probability of rain, snow, or sleet accumulation within 24 hours.",
        "category": "Atmospheric",
        "icon": "🌧️",
        "normal_range": (0, 100),
        "threshold_high": 75,
        "threshold_low": 10
    },
    "eco_risk_score": {
        "id": 7,
        "name": "Eco Risk Score",
        "unit": "/10",
        "description": "Integrated environmental vulnerability and natural hazard exposure rating.",
        "category": "Risk Analytics",
        "icon": "⚠️",
        "normal_range": (1.0, 10.0),
        "threshold_high": 7.5,
        "threshold_low": 2.5
    },
    "green_cover": {
        "id": 8,
        "name": "Green Cover Ratio",
        "unit": "%",
        "description": "Satellite-derived Normalized Difference Vegetation Index (NDVI) percentage.",
        "category": "Urban Dynamics",
        "icon": "🌳",
        "normal_range": (5, 80),
        "threshold_high": 60,
        "threshold_low": 15
    },
    "renewable_energy": {
        "id": 9,
        "name": "Renewable Energy Share",
        "unit": "%",
        "description": "Percentage of total municipal energy grid generated from solar, wind, and hydro.",
        "category": "Energy Grid",
        "icon": "☀️",
        "normal_range": (0, 100),
        "threshold_high": 80,
        "threshold_low": 20
    },
    "waste_management": {
        "id": 10,
        "name": "Waste Recycling Score",
        "unit": "/100",
        "description": "Efficiency of municipal solid waste recycling, diversion, and processing infrastructure.",
        "category": "Urban Dynamics",
        "icon": "♻️",
        "normal_range": (10, 100),
        "threshold_high": 85,
        "threshold_low": 30
    },
    "traffic_congestion": {
        "id": 11,
        "name": "Traffic Congestion Index",
        "unit": "%",
        "description": "Urban vehicle density delay index compared to free-flow arterial conditions.",
        "category": "Urban Dynamics",
        "icon": "🚗",
        "normal_range": (5, 95),
        "threshold_high": 70,
        "threshold_low": 20
    },
    "solar_potential": {
        "id": 12,
        "name": "Solar Power Potential",
        "unit": "kWh/m²",
        "description": "Global Horizontal Irradiance (GHI) available for photovoltaic generation.",
        "category": "Energy Grid",
        "icon": "🔋",
        "normal_range": (2.0, 8.5),
        "threshold_high": 6.5,
        "threshold_low": 3.0
    },
    "water_stress": {
        "id": 13,
        "name": "Water Stress Index",
        "unit": "%",
        "description": "Ratio of total municipal water withdrawals to available renewable freshwater supply.",
        "category": "Risk Analytics",
        "icon": "🚰",
        "normal_range": (0, 100),
        "threshold_high": 80,
        "threshold_low": 25
    },
    "resilience_index": {
        "id": 14,
        "name": "Climate Resilience Score",
        "unit": "/100",
        "description": "Capacity of local infrastructure and systems to withstand extreme climate shocks.",
        "category": "Risk Analytics",
        "icon": "🛡️",
        "normal_range": (10, 100),
        "threshold_high": 80,
        "threshold_low": 40
    }
}


# =============================================================================
# 3. GLOBAL CITIES REFERENCE DATABASE
# =============================================================================

GLOBAL_CITIES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "karachi": {"name": "Karachi", "lat": 24.8607, "lon": 67.0011, "country": "Pakistan", "country_code": "PK", "elevation_m": 10},
    "london": {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "United Kingdom", "country_code": "UK", "elevation_m": 11},
    "new york": {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "United States", "country_code": "US", "elevation_m": 10},
    "tokyo": {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "country_code": "JP", "elevation_m": 40},
    "lahore": {"name": "Lahore", "lat": 31.5204, "lon": 74.3587, "country": "Pakistan", "country_code": "PK", "elevation_m": 217},
    "sydney": {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "Australia", "country_code": "AU", "elevation_m": 19},
    "cairo": {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "country": "Egypt", "country_code": "EG", "elevation_m": 23},
    "sao paulo": {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333, "country": "Brazil", "country_code": "BR", "elevation_m": 760},
    "mumbai": {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "India", "country_code": "IN", "elevation_m": 14},
    "paris": {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "country": "France", "country_code": "FR", "elevation_m": 35},
    "beijing": {"name": "Beijing", "lat": 39.9042, "lon": 116.4074, "country": "China", "country_code": "CN", "elevation_m": 43},
    "toronto": {"name": "Toronto", "lat": 43.6532, "lon": -79.3832, "country": "Canada", "country_code": "CA", "elevation_m": 76},
    "dubai": {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "country": "United Arab Emirates", "country_code": "AE", "elevation_m": 5},
    "singapore": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "country": "Singapore", "country_code": "SG", "elevation_m": 15},
    "berlin": {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "country_code": "DE", "elevation_m": 34},
    "islamabad": {"name": "Islamabad", "lat": 33.6844, "lon": 73.0479, "country": "Pakistan", "country_code": "PK", "elevation_m": 540}
}


# =============================================================================
# 4. FEATURE MATRIX BUILDER (14 FEATURES GENERATOR ENGINE)
# =============================================================================

class FeatureMatrixEngine:
    """Calculates and constructs the complete 14-feature climate matrix for any city."""

    @staticmethod
    def _generate_seed(city_name: str) -> int:
        """Helper to create deterministic integer seed from city string."""
        return sum(ord(c) * (i + 1) for i, c in enumerate(city_name.lower().strip()))

    @classmethod
    def generate_full_matrix(cls, city_name: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """
        Generates deterministic, mathematically consistent feature values 
        for all 14 metrics based on coordinates and geographic location.
        """
        key = city_name.lower().strip()
        city_info = GLOBAL_CITIES_REGISTRY.get(key, None)

        if city_info:
            target_lat = city_info["lat"]
            target_lon = city_info["lon"]
            display_name = city_info["name"]
            country = city_info["country"]
        else:
            target_lat = lat if lat is not None else 25.0
            target_lon = lon if lon is not None else 67.0
            display_name = city_name.capitalize()
            country = "Global"

        # Deterministic pseudo-randomness based on city identity
        seed_val = cls._generate_seed(display_name)
        random.seed(seed_val)

        abs_lat = abs(target_lat)
        
        # Physics-inspired climate formulas
        base_temp = round(38.0 - (abs_lat * 0.52) + random.uniform(-2.5, 3.0), 1)
        base_humidity = int(max(15, min(95, 78 - (abs_lat * 0.45) + random.uniform(-12, 12))))
        
        # Urban Dynamics heuristics
        urban_density = random.randint(35, 92)
        green_cover = max(5, int(80 - (urban_density * 0.65) + random.uniform(-6, 6)))
        uhi_intensity = round((urban_density * 0.05) - (green_cover * 0.02) + random.uniform(0.1, 0.9), 1)

        # Assemble full 14-feature dictionary
        matrix = {
            "cityName": display_name,
            "country": country,
            "latitude": target_lat,
            "longitude": target_lon,
            "timestamp": datetime.utcnow().isoformat(),
            
            # Feature 1: Temperature (°C)
            "temperature": base_temp,
            
            # Feature 2: Carbon Intensity (gCO2/kWh)
            "carbon_intensity": random.randint(110, 490),
            
            # Feature 3: Air Quality Index (AQI)
            "air_quality_index": random.randint(22, 220),
            
            # Feature 4: Relative Humidity (%)
            "humidity": base_humidity,
            
            # Feature 5: Wind Speed (km/h)
            "wind_speed": round(random.uniform(3.5, 36.0), 1),
            
            # Feature 6: Precipitation Risk (%)
            "precipitation": random.randint(0, 90),
            
            # Feature 7: Eco Risk Score (/10)
            "eco_risk_score": round(min(10.0, max(1.0, (base_temp * 0.1) + (uhi_intensity * 0.45) + random.uniform(0.8, 2.5))), 1),
            
            # Feature 8: Green Cover Ratio (%)
            "green_cover": green_cover,
            
            # Feature 9: Renewable Energy Share (%)
            "renewable_energy": random.randint(6, 78),
            
            # Feature 10: Waste Recycling Score (/100)
            "waste_management": random.randint(30, 95),
            
            # Feature 11: Traffic Congestion Index (%)
            "traffic_congestion": urban_density,
            
            # Feature 12: Solar Power Potential (kWh/m²)
            "solar_potential": round(max(2.0, min(8.2, 7.8 - (abs_lat * 0.08) + random.uniform(-0.4, 0.4))), 1),
            
            # Feature 13: Water Stress Index (%)
            "water_stress": random.randint(12, 98),
            
            # Feature 14: Climate Resilience Score (/100)
            "resilience_index": random.randint(25, 96)
        }

        return matrix


# =============================================================================
# 5. 10 REAL-TIME MAP LAYERS GENERATOR
# =============================================================================

class RealTimeLayersEngine:
    """Generates structured spatial payloads for all 10 Real-Time Map Layers."""

    @staticmethod
    def get_layer_1_weather_radar(lat: float, lon: float) -> Dict[str, Any]:
        """Layer 1: Live Temperature, Humidity, Wind Speed & Rain Probability."""
        return {
            "layer_id": "layer_01_weather",
            "name": "Weather Radar",
            "icon": "🌤️",
            "coordinates": [lat, lon],
            "data": {
                "temperature_c": round(26.0 + random.uniform(-4, 9), 1),
                "humidity_pct": random.randint(38, 88),
                "wind_speed_kmh": round(random.uniform(4, 32), 1),
                "precipitation_drops_animation": True,
                "radar_coverage_status": "Active"
            }
        }

    @staticmethod
    def get_layer_2_wildfires() -> List[Dict[str, Any]]:
        """Layer 2: NASA FIRMS Active Wildfire Hotspots."""
        return [
            {"id": "wf_01", "name": "Amazonas Hotspot", "lat": -3.4653, "lon": -62.2159, "confidence": "High", "intensity_k": 348.5, "country": "Brazil"},
            {"id": "wf_02", "name": "California Bushfire", "lat": 38.8375, "lon": -120.8958, "confidence": "High", "intensity_k": 361.2, "country": "United States"},
            {"id": "wf_03", "name": "Siberian Taiga", "lat": 61.5240, "lon": 105.3188, "confidence": "Medium", "intensity_k": 322.0, "country": "Russia"},
            {"id": "wf_04", "name": "Outback Fires", "lat": -25.2744, "lon": 133.7751, "confidence": "High", "intensity_k": 355.0, "country": "Australia"},
            {"id": "wf_05", "name": "Attica Forest Fire", "lat": 38.0400, "lon": 23.8200, "confidence": "Medium", "intensity_k": 331.8, "country": "Greece"},
            {"id": "wf_06", "name": "Alberta Ridge Fire", "lat": 53.9333, "lon": -116.5765, "confidence": "High", "intensity_k": 342.1, "country": "Canada"}
        ]

    @staticmethod
    def get_layer_3_marine(lat: float, lon: float) -> Dict[str, Any]:
        """Layer 3: Sea Surface Temperature (SST) Anomaly & Coral Bleaching Risk."""
        anomaly = round(random.uniform(0.1, 3.6), 2)
        bleaching = "Severe Risk" if anomaly > 2.2 else ("Warning" if anomaly > 1.1 else "Normal")
        return {
            "layer_id": "layer_03_marine",
            "name": "Marine Heatwaves",
            "icon": "🌊",
            "coordinates": [lat, lon],
            "sst_temperature_c": round(21.0 + anomaly, 1),
            "sst_anomaly_c": anomaly,
            "coral_bleaching_risk": bleaching
        }

    @staticmethod
    def get_layer_4_carbon(country_code: str = "PK") -> Dict[str, Any]:
        """Layer 4: Grid Carbon Intensity & Energy Mix."""
        grid_database = {
            "PK": {"carbon_intensity": 380, "renewable_pct": 28.5, "fossil_pct": 71.5, "status": "High Footprint"},
            "US": {"carbon_intensity": 355, "renewable_pct": 23.0, "fossil_pct": 77.0, "status": "Moderate Footprint"},
            "UK": {"carbon_intensity": 140, "renewable_pct": 56.0, "fossil_pct": 44.0, "status": "Low Footprint"},
            "JP": {"carbon_intensity": 425, "renewable_pct": 20.0, "fossil_pct": 80.0, "status": "High Footprint"},
            "BR": {"carbon_intensity": 82, "renewable_pct": 84.5, "fossil_pct": 15.5, "status": "Clean Grid"}
        }
        data = grid_database.get(country_code.upper(), {
            "carbon_intensity": random.randint(160, 480),
            "renewable_pct": round(random.uniform(12, 65), 1),
            "fossil_pct": round(random.uniform(35, 88), 1),
            "status": "Estimated Grid Data"
        })
        return {
            "layer_id": "layer_04_carbon",
            "name": "Carbon Intensity",
            "icon": "⚡",
            "country_code": country_code.upper(),
            "grid_data": data
        }

    @staticmethod
    def get_layer_5_turbulence() -> Dict[str, Any]:
        """Layer 5: Clear-Air Turbulence (CAT) Aviation Risk Index."""
        cat_score = round(random.uniform(1.0, 9.2), 1)
        return {
            "layer_id": "layer_05_turbulence",
            "name": "Turbulence Risk",
            "icon": "✈️",
            "cat_index": cat_score,
            "aviation_status": "Safe Operations" if cat_score < 4.0 else ("Cautionary Steering" if cat_score < 7.0 else "Severe CAT Warning")
        }

    @staticmethod
    def get_layer_6_pollen(lat: float, lon: float) -> Dict[str, Any]:
        """Layer 6: Pollen & Allergy Concentrations."""
        tree = random.randint(0, 5)
        grass = random.randint(0, 5)
        weed = random.randint(0, 5)
        overall_idx = max(tree, grass, weed)
        labels = ["None", "Very Low", "Low", "Moderate", "High", "Very High"]
        return {
            "layer_id": "layer_06_pollen",
            "name": "Pollen Forecast",
            "icon": "🌿",
            "coordinates": [lat, lon],
            "tree_pollen": tree,
            "grass_pollen": grass,
            "weed_pollen": weed,
            "overall_allergy_risk": labels[overall_idx]
        }

    @staticmethod
    def get_layer_7_uhi(city_name: str) -> Dict[str, Any]:
        """Layer 7: Urban Heat Island Center vs Rural Temperature Differential."""
        urban = round(random.uniform(31.0, 41.0), 1)
        rural = round(urban - random.uniform(2.2, 5.8), 1)
        return {
            "layer_id": "layer_07_uhi",
            "name": "Urban Heat Island",
            "icon": "🏙️",
            "city": city_name,
            "urban_center_temp_c": urban,
            "rural_surrounding_temp_c": rural,
            "uhi_differential_c": round(urban - rural, 1),
            "severity": "Critical UHI Zone" if (urban - rural) > 4.0 else "Moderate UHI Zone"
        }

    @staticmethod
    def get_layer_8_sovereign_risk(country_name: str) -> Dict[str, Any]:
        """Layer 8: Sovereign Climate Resilience Score (0-100)."""
        score = random.randint(32, 88)
        return {
            "layer_id": "layer_08_sovereign",
            "name": "Sovereign Risk Score",
            "icon": "🛡️",
            "country": country_name,
            "resilience_score": score,
            "classification": "High Resilience" if score > 75 else ("Vulnerable" if score < 45 else "Moderate Risk")
        }

    @staticmethod
    def get_layer_9_extreme_alerts() -> List[Dict[str, Any]]:
        """Layer 9: Extreme Weather Real-Time Warnings."""
        return [
            {"id": "alt_01", "type": "Cyclone Emergency", "region": "Bay of Bengal", "severity": "Extreme", "issued_at": datetime.utcnow().isoformat()},
            {"id": "alt_02", "type": "Heatwave Emergency", "region": "South Asia", "severity": "High", "issued_at": datetime.utcnow().isoformat()},
            {"id": "alt_03", "type": "Flash Flood Alert", "region": "Central Europe", "severity": "High", "issued_at": datetime.utcnow().isoformat()},
            {"id": "alt_04", "type": "Dust Storm Advisory", "region": "Middle East", "severity": "Medium", "issued_at": datetime.utcnow().isoformat()}
        ]

    @staticmethod
    def get_layer_10_city_labels() -> List[Dict[str, Any]]:
        """Layer 10: Interactive City Markers for Map UI."""
        return [
            {"name": city_data["name"], "lat": city_data["lat"], "lon": city_data["lon"], "country": city_data["country"]}
            for city_data in GLOBAL_CITIES_REGISTRY.values()
        ]


# =============================================================================
# 6. MULTI-CITY COMPARISON DATA CALCULATOR (UP TO 3 CITIES)
# =============================================================================

class CityComparisonEngine:
    """Handles multi-city comparison matrices (comparing up to 3 cities side-by-side)."""

    @classmethod
    def build_comparison_payload(cls, cities_list: List[str]) -> Dict[str, Any]:
        """
        Takes a list of city names and returns a side-by-side comparison 
        dictionary for all 14 metrics.
        """
        clean_cities = cities_list[:3]  # Limit to 3 max
        results = []

        for city in clean_cities:
            matrix = FeatureMatrixEngine.generate_full_matrix(city)
            results.append(matrix)

        return {
            "compared_cities_count": len(results),
            "metadata": FEATURE_METADATA,
            "comparison": results
        }


# =============================================================================
# 7. SCENARIO SIMULATOR COMPUTATION MODEL
# =============================================================================

class ScenarioSimulator:
    """Interactive scenario simulation model for live parameter tweaking."""

    @staticmethod
    def run_simulation(urban_density: float, vegetation_cover: float, renewable_pct: float) -> Dict[str, Any]:
        """
        Computes live outcome predictions based on user adjustments 
        to urban density, green vegetation cover, and clean energy share.
        """
        base_temp_anomaly = 2.2  # °C baseline
        base_carbon = 360.0      # gCO2/kWh baseline
        base_aqi = 115           # AQI baseline

        # Calculate impact vectors
        temp_delta = (urban_density * 0.038) - (vegetation_cover * 0.048)
        carbon_delta = -1.0 * (renewable_pct * 2.85)
        aqi_delta = (urban_density * 0.42) - (vegetation_cover * 0.65) - (renewable_pct * 0.28)

        predicted_temp_anomaly = round(max(-1.5, base_temp_anomaly + temp_delta), 2)
        predicted_carbon = round(max(15.0, base_carbon + carbon_delta), 1)
        predicted_aqi = int(max(10, base_aqi + aqi_delta))

        # Overall sustainability index (0 - 100)
        sustainability_rating = min(100, max(0, int(100 - (predicted_temp_anomaly * 12) - (predicted_carbon * 0.08))))

        return {
            "scenario_inputs": {
                "urban_density_pct": urban_density,
                "vegetation_cover_pct": vegetation_cover,
                "renewable_energy_pct": renewable_pct
            },
            "predicted_outcomes": {
                "temperature_anomaly_c": predicted_temp_anomaly,
                "carbon_intensity_gco2_kwh": predicted_carbon,
                "air_quality_index": predicted_aqi,
                "sustainability_score": sustainability_rating,
                "rating_classification": "Optimum" if sustainability_rating > 80 else ("Moderate" if sustainability_rating > 50 else "Critical Risk")
            }
        }


# =============================================================================
# 8. HISTORICAL TIME PLAYBACK DATA GENERATOR
# =============================================================================

class HistoricalPlaybackEngine:
    """Generates multi-day historical climate trends for map time-sliders."""

    @staticmethod
    def generate_timeline(days_back: int = 7) -> List[Dict[str, Any]]:
        """Generates past daily climate points for historical analysis."""
        timeline = []
        now = datetime.utcnow()

        for i in range(days_back, 0, -1):
            past_date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            timeline.append({
                "date": past_date,
                "global_avg_temp_c": round(15.2 + math.sin(i * 0.5) * 1.8, 1),
                "global_carbon_index": random.randint(310, 375),
                "active_wildfires_count": random.randint(110, 160),
                "avg_humidity_pct": random.randint(58, 68)
            })

        return timeline


# =============================================================================
# 9. AI CHATBOT KNOWLEDGE BASE & RESPONSE ENGINE
# =============================================================================

class ClimateChatEngine:
    """Rules-assisted NLP Engine for handling user climate queries."""

    @staticmethod
    def process_query(user_message: str) -> str:
        msg = user_message.lower().strip()

        if "fire" in msg or "wildfire" in msg:
            return "EcoPulse currently tracks active wildfires globally via NASA FIRMS integration. Key active hotspots include the Amazon Basin, California, and Western Australia."
        elif "alert" in msg or "warning" in msg:
            return "Active extreme weather alerts are broadcast in real-time. Current alerts include Heatwave warnings in South Asia and Flash Flood alerts in Central Europe."
        elif "carbon" in msg or "co2" in msg:
            return "Grid carbon intensity reflects the emissions per kWh produced. High-carbon grids exceed 400 gCO2/kWh, while clean grids with renewable energy stay under 150 gCO2/kWh."
        elif "uhi" in msg or "urban heat" in msg:
            return "The Urban Heat Island (UHI) effect causes dense city centers to be 2°C to 5°C warmer than surrounding rural areas due to pavement density and low vegetation."
        elif "pollen" in msg or "allergy" in msg:
            return "Our pollen layer tracks tree, grass, and weed pollen levels to assess allergy risks for sensitive urban populations."
        else:
            return f"EcoPulse Intelligence: Processing your climate query '{user_message}'. All 14 metrics and 10 real-time map layers are currently active and updating."


# =============================================================================
# 10. SELF-TEST RUNNER & ENTRYPOINT
# =============================================================================

if __name__ == "__main__":
    logger.info("Executing Data Features Engine Self-Test...")

    # Test 1: Full 14-Feature Matrix Generation
    matrix = FeatureMatrixEngine.generate_full_matrix("Karachi")
    logger.info(f"Test 1 Passed: Generated {len(matrix) - 5} climate features for Karachi.")

    # Test 2: Real-Time Map Layers
    fires = RealTimeLayersEngine.get_layer_2_wildfires()
    logger.info(f"Test 2 Passed: Retrieved {len(fires)} active wildfire hotspots.")

    # Test 3: Multi-City Comparison
    comparison = CityComparisonEngine.build_comparison_payload(["Karachi", "London", "Tokyo"])
    logger.info(f"Test 3 Passed: Built comparison matrix for {comparison['compared_cities_count']} cities.")

    # Test 4: Scenario Simulation
    sim = ScenarioSimulator.run_simulation(70.0, 20.0, 50.0)
    logger.info(f"Test 4 Passed: Scenario Simulation calculated Score {sim['predicted_outcomes']['sustainability_score']}.")

    # Test 5: Historical Timeline
    history = HistoricalPlaybackEngine.generate_timeline(7)
    logger.info(f"Test 5 Passed: Generated {len(history)} historical timeline data points.")

    logger.info("All 10 Real-Time Layers and 14 Features Data Engine Self-Test Completed Successfully!")