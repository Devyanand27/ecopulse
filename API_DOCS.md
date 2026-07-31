# ⚡ EcoPulse API Documentation (v4.2.0)

Interactive OpenAPI / Swagger documentation is also served natively at `/docs` or `/redoc`.

---

## 📡 Endpoints Overview

### 1. Telemetry Engine
- **`GET /api/telemetry`**
  - **Query Params:** `city` (string, e.g., `Lahore`, `Karachi`)
  - **Description:** Returns real-time weather, AQI, UHI index, carbon grid intensity, turbulence scores, and ocean heat telemetry.
  - **Sample Response:**
    ```json
    {
      "city": "Lahore",
      "country": "Pakistan",
      "coordinates": {"lat": 31.5204, "lon": 74.3587},
      "temperature": "35.2 °C",
      "humidity": "45 %",
      "wind_speed": "12.5 km/h",
      "uhi_index": "+3.6 °C (NASA Hotspots: 4)",
      "turbulence_risk": {
        "score": 28,
        "level": "Low Risk"
      },
      "grid_carbon_intensity": "410 gCO2eq/kWh",
      "ocean_surface_heat": "27.5 °C",
      "aqi": 185
    }
    ```

---

### 2. UI Portal Routes
- **`GET /`** or **`GET /dashboard`** or **`GET /dashboard.html`**: Interactive Live Map Dashboard.
- **`GET /compare`** or **`GET /compare.html`**: Global City Comparison Matrix Page.
- **`GET /about`**: EcoPulse Platform Story & Technical Documentation Page.

---

### 3. Active Environmental Layers
- **`GET /api/v1/wildfires`**
  - **Description:** Fetch global thermal hotspots detected by satellite VIIRS/MODIS sensors.
  - **Sample Response:**
    ```json
    {
      "total_detected": 10,
      "hotspots": [
        {
          "id": "fire_pk_01",
          "location": "Margalla Hills, Islamabad",
          "lat": 33.7438,
          "lon": 73.0228,
          "frp": "42.5 MW"
        }
      ]
    }
    ```

---

### 4. Interactive Tools & Scenario Simulation
- **`POST /api/v1/scenario/simulate`**
  - **Request Body:**
    ```json
    {
      "urban_density": 65.0,
      "vegetation_cover": 25.0,
      "renewable_energy_pct": 45.0
    }
    ```
  - **Sample Response:**
    ```json
    {
      "temperature_anomaly_c": 2.05,
      "carbon_intensity_reduction_pct": 112.5,
      "uhi_mitigation_c": 1.0,
      "sustainability_score": 63
    }
    ```

---

### 5. Intelligent AI Assistant
- **`POST /api/v1/chat`**
  - **Request Body:** `{"message": "What is the UHI index of Lahore?"}`
  - **Sample Response:**
    ```json
    {
      "reply": "🏙️ **Urban Heat Island (UHI) Status for Lahore**:\n• Surface Heat Delta: +3.6°C above rural baselines.\n• Driver: High asphalt density & concrete heat trap."
    }
    ```

---

### 6. Risk Alert Subscriptions
- **`POST /api/subscribe`**
  - **Form Data:** `email=user@example.com`
  - **Description:** Enqueues background tasks to dispatch a welcome HTML telemetry alert via SMTP.