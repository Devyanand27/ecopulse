# 🌿 EcoPulse – Global Climate Intelligence Platform

**Version 3.3** · Built for **NEXTGEN INNOVATION 2026**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?logo=leaflet)](https://leafletjs.com)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4.1-ff6384?logo=chart.js)](https://chartjs.org)

> **Real‑time, hyper‑local climate risk intelligence for any location – with predictive alerts, scenario planning, and multi‑city comparison.**

---

## 🎯 Overview

EcoPulse is an **advanced global climate intelligence platform** that combines:

- **AI/ML** (XGBoost + SHAP) for microclimate prediction  
- **Real‑time data** from Open‑Meteo, NASA FIRMS, ElectricityMap (with mock fallbacks)  
- **Interactive map** with 10+ layers (weather, fires, ocean, carbon, turbulence, pollen, UHI, risk, alerts)  
- **Unique icons** for each layer for easy visual differentiation  
- **Predictive risk alerts** for fire and flood based on forecast data  
- **Scenario simulator** to see the impact of urban density, vegetation, and renewable energy  
- **Multi‑city comparison** to benchmark climate resilience across cities  
- **Climate Learning Center** explaining key concepts in simple terms  
- **Progressive Web App (PWA)** – installable on mobile  
- **Multi‑language support** (English, Urdu, Hindi)  
- **WebSocket** real‑time updates  

It empowers **city officials, emergency responders, researchers, and citizens** to make data‑driven decisions for climate resilience.

---

## ✨ Key Features

| # | Feature | Icon | Description |
|---|---------|------|-------------|
| 1 | **Weather Radar** | ☁️ | Live temperature, humidity, wind, rain probability with animated drops |
| 2 | **Wildfire Tracker** | 🔥 | NASA FIRMS data – confidence, brightness, type |
| 3 | **Marine Heatwaves** | 🌊 | SST anomaly, coral bleaching risk |
| 4 | **Carbon Intensity** | ⚡ | Grid carbon footprint (gCO₂/kWh), renewable/fossil mix |
| 5 | **Turbulence Risk** | ✈️ | Clear‑air turbulence for aviation |
| 6 | **Pollen Forecast** | 🌿 | Tree/grass/weed pollen, allergy risk |
| 7 | **Urban Heat Island** | 🏙️ | City vs rural temperature, intensity |
| 8 | **Sovereign Risk Score** | 🛡️ | Country‑level climate resilience (0‑100) |
| 9 | **Extreme Alerts** | 🔔 | Real‑time flash flood, tornado, dust storm warnings |
| 10 | **Microclimate Prediction** | 📊 | ML‑based temperature anomaly (100m resolution) |
| 11 | **Predictive Risk Alerts** | 🚨 | Fire/flood risk scores for cities (48‑hour forecast) |
| 12 | **Scenario Simulator** | 🎛️ | Adjust urban density, vegetation, renewables – see impact |
| 13 | **Multi‑City Comparison** | 📈 | Compare metrics across 10+ global cities |
| 14 | **Climate Learning Center** | 📚 | Simple explanations of climate terms |

---

## 🖥️ Tech Stack

### Backend
- **FastAPI** – high‑performance REST API + WebSocket  
- **XGBoost** – ML model for temperature anomaly  
- **SHAP** – explainability  
- **Pandas / NumPy** – data processing  
- **Joblib** – model serialization  
- **Uvicorn** – ASGI server  

### Frontend
- **Leaflet** – interactive map  
- **Chart.js** – 7‑day forecast & comparison charts  
- **Font Awesome** – icons  
- **Custom CSS** – dark glassmorphism, fully responsive  

### Data Sources (with mock fallback)
- Open‑Meteo (weather, marine, air quality, warnings, archive)  
- NASA FIRMS (active fires)  
- ElectricityMap (carbon intensity)  
- Derived calculations (turbulence, UHI, risk score)  

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (recommended)  
- `pip` and `venv`  

### Installation
```bash
# Clone or download the project
cd EcoPulse/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # Linux/Mac
# or venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Train the ML model
python train_model.py

# Run the server
uvicorn main:app --reload

Open http://localhost:8000 in your browser