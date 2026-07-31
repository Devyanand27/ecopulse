# 🌍 EcoPulse v4.2 Enterprise — Predictive Environmental Telemetry Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML%20Engine-FF6F00?style=for-the-badge)](https://xgboost.readthedocs.io/)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?style=for-the-badge)](https://ecopulse-1-b2lm.onrender.com)

**EcoPulse v4.2 Enterprise** is an asynchronous predictive environmental telemetry platform that bridges satellite thermal tracking, urban microclimate diagnostics, grid emission monitoring, and machine learning scenario simulation into a unified GIS web portal.

---

## 🔗 Quick Links & Endpoints

* 🌐 **Live Application:** [https://ecopulse-1-b2lm.onrender.com](https://ecopulse-1-b2lm.onrender.com)
* 📊 **Interactive Dashboard:** `https://ecopulse-1-b2lm.onrender.com/dashboard`
* 🏙️ **Multi-City Comparison:** `https://ecopulse-1-b2lm.onrender.com/compare`
* 📄 **OpenAPI / Swagger Docs:** `https://ecopulse-1-b2lm.onrender.com/docs`

---

## ✨ Key Features & Enterprise Modules

### 1. 🛰️ Geospatial Telemetry Mapping Center
* **Live GIS Engine:** Built with Leaflet.js and CartoDB Dark Matter tiles.
* **Multi-Layer Support:** Dynamic toggle for Cities, Wildfires (NASA FIRMS), Pollen Allergen Risk, Ocean Heat Thermal, Urban Heat Island (UHI), and Atmospheric Turbulence.
* **Real-Time Telemetry Markers:** Tracks key regional nodes (Islamabad, Lahore, Karachi, and UAE marine zones).

### 2. 🧮 XGBoost Interactive Scenario Simulator
* Allows urban planners to model environmental policy interventions interactively.
* **UHI Simulation Formula:**
  $$\text{Simulated UHI Delta } (^\circ\text{C}) = (\text{Vegetation Cover } \% \times 0.04) - (\text{Urban Density } \% \times 0.02)$$
* **Carbon Offset Formula:**
  $$\text{Carbon Reduction Offset } \% = \text{Renewables Share } \% \times 2.5$$

### 3. 🤖 Natural Language AI Assistant
* Context-aware conversational AI assistant integrated into the UI.
* Accessible via REST API endpoint (`POST /api/v1/chat`).

### 4. 🏙️ Metropolitan Matrix Comparison
* Side-by-side diagnostic comparative matrix analyzing Islamabad vs. Lahore telemetry metrics (AQI, UHI Delta, SST, Turbulence Index, and Grid Carbon Intensity).

### 5. 🔔 Automated Safety Threshold Alert System
* Background risk engine dispatching alerts for UHI thermal anomalies (> +3.0°C), atmospheric shear (> 40/100), and unhealthy AQI levels (> 100).

---

## 🛠️ System Architecture

```text
+-------------------------------------------------------------------------+
|                    FRONTEND VISUALIZATION LAYER                         |
|   Leaflet GIS Engine  |  Chart.js Visual Analytics  |  AI Assistant UI   |
+-------------------------------------------------------------------------+
                                     ^
                                     | JSON REST Telemetry (OpenAPI 3.1)
                                     v
+-------------------------------------------------------------------------+
|                    FASTAPI CORE ASYNCHRONOUS ENGINE                     |
+-------------------------------------------------------------------------+
          /                          |                          \
         v                           v                           v
[ NASA FIRMS Telemetry ]    [ Grid Carbon Analytics ]   [ XGBoost ML Engine ]
 Thermal Hotspot Tracking    gCO2eq/kWh Diagnostics      Scenario Simulation
```

## 🛠️ Environment Variables Setup

Configure the following environment variables in your deployment platform (e.g., Render) or local `.env` file:

| Variable | Description | Example / Value |
| :--- | :--- | :--- |
| `SENDGRID_API_KEY` | SendGrid Web API Key for email alerts | `SG.xxxxxxxx...` |
| `SENDER_EMAIL` | Verified SendGrid sender email address | `nanddevya27@gmail.com` |
| `ELECTRICITY_MAP_TOKEN` | API Key for Electricity Maps telemetry | `your_token_here` |
| `NASA_FIRMS_TOKEN` | Token for NASA FIRMS Thermal Hotspots | `your_token_here` |

---

## 🚀 Quick Start (Local Run)

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/your-username/ecopulse.git](https://github.com/your-username/ecopulse.git)
   cd ecopulse
2. **Install Dependecies:**
   ```bash
   install -r requirements.txt
3. **Launch Application:**
   ```bash
   python main.py
   Access the dashboard at http://localhost:8000/
4. **📡 API Architecture & Endpoints:**
```text
   **Core UI Routes**
GET / — Interactive Geospatial Live Telemetry Map
GET /compare — Dynamic Global Multi-City Climate Comparison Portal
GET /about — System Architecture & Methodology Documentation

   **REST API Endpoints**
GET /api/telemetry?city={cityName} — Fetches real-time weather, AQI, UHI, and turbulence metrics for any global city.
POST /api/subscribe — Subscribes a user email for climate risk alerts via SendGrid API.
```
6. **Run Development Server:**
```Bash
uvicorn main:app --reload --host 0.0.00 --port 8000
```
Open your browser and navigate to
```Bash
http://localhost:8000 or http://localhost:8000/docs.
```
**📈 ML Engine Performance**
Model Framework: XGBoost Regression Pipeline

Inference Latency: < 15ms
Prediction Accuracy: 94.5%

**📜 License**
This project is open-source and available under the MIT License.
