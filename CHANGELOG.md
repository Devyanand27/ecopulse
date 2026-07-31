# 📜 EcoPulse Release Changelog

## [4.2.0] - 2026-07-31

### 🚀 Added
- **Urban Heat Island (UHI) Engine:** Calculates real-time microclimate thermal traps (+°C) based on temperature and satellite hotspot density.
- **Atmospheric Turbulence Scoring:** Evaluates boundary-layer wind speeds and gust deltas to output turbulence risk levels.
- **Ocean Heat Index Layer:** Tracks sea surface temperatures and marine heatwave anomalies.
- **Carbon Grid Intensity:** Integrated Electricity Maps telemetry to monitor real-time electrical grid emission factors (`gCO2eq/kWh`).
- **Flexible SMTP SSL Support:** Upgraded email notification dispatcher with `SMTP_SSL` on Port 465 with fallback handling to prevent cloud platform (Render) timeouts.
- **Route Aliases:** Added `/dashboard.html` and `/compare.html` endpoint aliases to resolve UI page navigation errors.

### ⚙️ Changed
- Converted `/compare` from external static `FileResponse` dependency to inline dynamic `HTMLResponse` served directly from `main.py`.
- Expanded the AI chatbot knowledge base to handle queries regarding UHI, turbulence, carbon grid, ocean heat, pollen, and wildfires.

### 🐛 Fixed
- Fixed 404 `{"detail": "Not Found"}` error when navigating between `compare.html` and `dashboard.html`.
- Fixed background email delivery issues under cloud container restrictions by introducing 15-second socket connection timeouts.

---

## [4.0.0] - 2026-06-15
- Initial enterprise deployment featuring Leaflet dark maps, Open-Meteo telemetry, and basic wildfire hotspot layer.