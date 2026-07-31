# 🌐 EcoPulse - Enterprise Global Climate Intelligence Platform (v4.2.0)

**EcoPulse** is an enterprise-grade climate monitoring and predictive intelligence suite designed to bridge real-time environmental telemetry, satellite thermal hotspot data, and machine learning models into a unified interactive interface.

---

## ✨ Features & Layers

- **🏙️ Urban Heat Island (UHI) Diagnostics:** Real-time surface thermal anomaly tracking across dense concrete urban sectors versus baseline regions using NASA FIRMS hotspot correlation.
- **🌊 Ocean Heat & Marine Anomalies:** Tracks coastal sea surface temperature build-ups and marine heatwave risk zones.
- **⚡ Carbon Grid Intensity:** Real-time tracking of regional electrical grid emission rates (`gCO2eq/kWh`) integrated with the Electricity Maps API.
- **💨 Atmospheric Turbulence & Wind Shear:** Real-time boundary-layer wind speed and gust differential evaluation for aviation safety and low-altitude structural hazard assessment.
- **🌿 Botanical Pollen Tracking:** Active monitoring of airborne botanical allergen risk levels (Tree, Grass, Weed concentrations).
- **🔥 NASA FIRMS Wildfire Monitoring:** Global satellite thermal hotspot detection featuring active Fire Radiative Power (FRP) metrics.
- **🤖 Intelligent Climate AI Assistant:** Built-in AI bot trained to serve context-aware climate metrics, UHI rates, and atmospheric risk insights.
- **🚨 Automated Risk Telemetry Alerts:** Background worker integration with SMTP (Port 465 SSL / 587 TLS) for real-time risk alert subscriptions.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.10+, Uvicorn, Async HTTP (httpx/requests)
- **Frontend UI:** Embedded HTML5, Leaflet.js (CartoDB Dark Tiles), Chart.js, CSS3
- **External Data Providers:** Open-Meteo API, NASA FIRMS VIIRS Active Fire Data, Electricity Maps API
- **Alert System:** Python `smtplib` (SSL/TLS), BackgroundTasks

---

## 🚀 Quick Start (Local Run)

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/your-username/ecopulse.git](https://github.com/your-username/ecopulse.git)
   cd ecopulse
2. **Install Dependecies:**
   ```bash
   install -r requirements.txt
3. **Set Environment Variables (Optional):**
   ```bash
  export SENDER_EMAIL="your-email@gmail.com"
  export SENDER_PASSWORD="your-16-digit-app-password"
  export SMTP_PORT=465
  export ELECTRICITY_MAPS_TOKEN="your_token"
  export NASA_FIRMS_TOKEN="your_token"
4. **Launch Application:**
   ```bash
   python main.py
   Access the dashboard at http://localhost:8000/
   