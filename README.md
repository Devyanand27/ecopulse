# 🌍 EcoPulse Enterprise - Global Climate & Telemetry Intelligence Platform

EcoPulse is an enterprise-grade environmental telemetry and predictive climate modeling dashboard built with **FastAPI** and **Chart.js**. It provides real-time tracking, geospatial visualization, multi-metric city comparison, and automated risk alert subscriptions.

---

## ⚡ Key Features

* **Global Dynamic City Comparison:** Real-time comparison across any city worldwide using Open-Meteo Geocoding API (Zero hardcoding).
* **Automated Risk Subscriptions:** Instant email notifications powered by SendGrid HTTP Web API for UHI anomalies, high AQI, and turbulence alerts.
* **Geospatial Hotspot Tracking:** Satellite thermal anomaly detection utilizing NASA FIRMS API.
* **Grid Carbon Intensity:** Live power grid telemetry via Electricity Maps API.
* **Aviation & Turbulence Risk Index:** Real-time atmospheric turbulence risk score evaluation.

---

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
   **Core UI Routes**
GET / — Interactive Geospatial Live Telemetry Map
GET /compare — Dynamic Global Multi-City Climate Comparison Portal
GET /about — System Architecture & Methodology Documentation

   **REST API Endpoints**
GET /api/telemetry?city={cityName} — Fetches real-time weather, AQI, UHI, and turbulence metrics for any global city.
POST /api/subscribe — Subscribes a user email for climate risk alerts via SendGrid API.

