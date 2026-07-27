# EcoPulse API Reference

**Base URL:** `http://localhost:8000/api`  
**Version:** 3.3  
**Format:** JSON (all requests/responses)

All endpoints include **error handling** and **mock fallbacks** – the dashboard works even without internet.

---

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/weather?lat=&lon=` | GET | Current weather + 7‑day forecast |
| `/fires?min_lon=&min_lat=&max_lon=&max_lat=` | GET | Active fires within bbox |
| `/ocean?lat=&lon=` | GET | Sea surface temperature anomaly |
| `/carbon?country=` | GET | Carbon intensity (gCO₂/kWh) |
| `/turbulence?bbox` | GET | Turbulence risk zones |
| `/pollen?lat=&lon=` | GET | Pollen concentration |
| `/uhi?city=` | GET | Urban Heat Island index |
| `/risk-score?country=` | GET | Sovereign Green Risk Score (0‑100) |
| `/alerts?bbox` | GET | Extreme weather alerts |
| `/predict` | POST | Microclimate temperature anomaly prediction (JSON body) |
| `/analytics` | GET | Global statistics (fires, alerts, avg temp) |
| `/historical?lat=&lon=&days=` | GET | Historical daily weather (last 1‑30 days) |
| `/risk-alerts` | GET | Fire/flood risk scores for monitored cities |
| `/scenario` | POST | Scenario simulation (urban density, vegetation, renewables) |
| `/compare?cities=...` | POST | Multi‑city comparison (up to 5 cities) |
| `/chat?message=` | GET | Chatbot assistant – answers climate questions |
| `/ws` | WebSocket | Real‑time updates stream |

---

## Detailed Parameter & Response Examples

### 1. Weather
**GET** `/api/weather?lat=30&lon=70`

**Response:**
```json
{
  "latitude": 30.0,
  "longitude": 70.0,
  "current": {
    "temperature_2m": 25.3,
    "relative_humidity_2m": 65,
    "weather_code": 0,
    "wind_speed_10m": 12.4,
    "precipitation": 0.0
  },
  "daily": {
    "time": ["2026-07-27", ...],
    "temperature_2m_max": [30, 31, ...],
    "temperature_2m_min": [18, 19, ...],
    "precipitation_probability_max": [20, 40, ...]
  }
}
2. Fires
GET /api/fires?min_lon=-180&min_lat=-90&max_lon=180&max_lat=90

Response: Array of fire objects:
[
  {
    "lat": 35.12,
    "lon": -101.23,
    "brightness": 345.6,
    "confidence": "high",
    "type": "fire"
  }
]

3. Ocean
GET /api/ocean?lat=30&lon=70

Response:
{
  "lat": 30.0,
  "lon": 70.0,
  "sst": 26.5,
  "anomaly": 1.2,
  "coral_risk": "medium"
}
4. Carbon Intensity
GET /api/carbon?country=PK

Response:
{
  "country": "PK",
  "carbon_intensity": 320,
  "renewable_percent": 35,
  "fossil_percent": 65
}
5. Turbulence
GET /api/turbulence?min_lon=-180&min_lat=-90&max_lon=180&max_lat=90

Response: Array of zones:
[
  { "lat": 40.0, "lon": -80.0, "risk": "moderate" }
]
6. Pollen
GET /api/pollen?lat=30&lon=70

Response:
{
  "tree": 45,
  "grass": 20,
  "weed": 10,
  "overall_risk": "moderate"
}
7. Urban Heat Island (UHI)
GET /api/uhi?city=Karachi

Response:
{
  "city": "Karachi",
  "urban_temp": 38.2,
  "rural_temp": 32.5,
  "uhi_intensity": 5.7,
  "hotspots": [{"lat": 24.86, "lon": 67.01}]
}
8. Sovereign Risk Score
GET /api/risk-score?country=PK

Response:
{
  "country": "PK",
  "score": 68,
  "components": {
    "extreme_weather": 6,
    "sea_level": 4,
    "air_quality": 7,
    "emissions": 5,
    "renewables": 3,
    "policy": 5
  }
}
9. Extreme Alerts
GET /api/alerts?min_lon=-180&min_lat=-90&max_lon=180&max_lat=90

Response:
[
  {
    "type": "flash flood",
    "lat": 24.0,
    "lon": 67.0,
    "severity": "warning",
    "time": "2026-07-27T14:30:00Z"
  }
]
10. Microclimate Prediction
POST /api/predict

Request Body:
{
  "elevation": 50,
  "urban_density": 30,
  "veg_index": 0.4,
  "water_dist": 2,
  "hour": 14
}
Response:
{
  "anomaly": 2.35,
  "shap_values": [0.12, -0.05, 0.30, -0.10, 0.08]
}
11. Analytics
GET /api/analytics

Response:
{
  "total_fires": 12,
  "total_alerts": 0,
  "avg_temperature": 26.4,
  "timestamp": "2026-07-27T12:34:56.789Z"
}
12. Historical Data
GET /api/historical?lat=30&lon=70&days=7

Response: Same format as weather but only daily object.

13. Predictive Risk Alerts
GET /api/risk-alerts

Response:
{
  "alerts": [
    {
      "name": "Karachi",
      "lat": 24.86,
      "lon": 67.01,
      "fire_risk": 2,
      "flood_risk": 0,
      "temp": 35.2,
      "humidity": 18,
      "wind": 22,
      "rain_prob": 10
    }
  ],
  "timestamp": "2026-07-27T12:34:56.789Z"
}
14. Scenario Simulator
POST /api/scenario

Request Body:
{
  "urban_density": 50,
  "veg_index": 0.5,
  "renewable_percent": 30
}
Response:
{
  "anomaly": 1.2,
  "carbon_intensity": 310,
  "renewable_percent": 30
}
15. Multi‑City Comparison
POST /api/compare?cities=Karachi,Lahore,Delhi

Response:
{
  "comparison": [
    {
      "city": "Karachi",
      "temperature": 35.2,
      "fires_nearby": 2,
      "carbon_intensity": 320,
      "uhi_intensity": 5.7,
      "risk_score": 68
    },
    ...
  ],
  "timestamp": "2026-07-27T12:34:56.789Z"
}
16. Chatbot
GET /api/chat?message=weather

Response:
{
  "reply": "🌤️ Click on the map to see current weather and 7‑day forecast."
}
17. WebSocket
ws://host/ws

Messages received:
{
  "type": "update",
  "timestamp": "...",
  "fires": 20,
  "alerts": 1
}
Error Handling
200 – success

400 – bad request (missing parameters)

500 – internal server error (with fallback to mock data)

Rate limiting: 60 requests per minute (soft).

Authentication: None required for demo. For production, add API keys or OAuth