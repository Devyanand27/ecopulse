
# Changelog

All notable changes to EcoPulse are documented here.

---

## [3.3] – 2026-07-27

### Added
- **Predictive Risk Alerts** – fire/flood risk scores for major cities (computed from Open‑Meteo forecast).
- **Scenario Simulator** – sliders for urban density, vegetation, renewable energy – see impact on anomaly and carbon intensity.
- **Multi‑City Comparison** – select up to 5 cities, compare metrics (temp, fires, carbon, UHI, risk) with bar charts.
- **Climate Learning Center** – modal explaining temperature, humidity, pollen, carbon intensity, UHI, risk score, etc.
- **Chatbot** – AI assistant that answers climate‑related questions (weather, fires, alerts, rain, carbon, pollen).
- **Analytics dashboard** – global stats (total fires, alerts, average temperature) with bar chart.
- **Historical data playback** – time slider to fetch past weather (1‑30 days) and overlay heatmap.

### Changed
- Removed city labels from map (user request) – cleaner visual.
- Enhanced error handling in all endpoints – always return fallback data.
- Updated frontend with new panels for Risk Alerts, Scenario, Compare, and Learning Center.

### Fixed
- Chatbot returning `undefined` – fixed by ensuring proper response parsing.
- Analytics modal showing placeholders – improved error handling and fallback data.
- Internal server error on root – resolved file path issues.

---

## [3.2] – 2026-07-25

### Added
- Unique icons for each feature on the map (fire, cloud, water, plane, etc.) – replaces all circles.
- Rain status badge next to location label – shows "Raining" or "Not raining".
- Clickable alert items in the feed – clicking zooms map to that alert's location.
- Legend panel with icons and color meanings.

### Changed
- Popup now includes a clear "Raining / Not raining" line.
- Legend now displays the corresponding icon for each layer.

---

## [3.1] – 2026-07-24

### Added
- Rain probability and status in popups.
- Location label with rain badge.
- More detailed alert explanations in the UI.

---

## [3.0] – 2026-07-23

### Added
- All 10 features with full backend endpoints.
- WebSocket for real‑time updates.
- Fully responsive dark glassmorphism UI.
- City search (Nominatim integration).

---

## [2.0] – 2026-07-20

### Added
- 10 feature layers with toggles.
- Basic map interaction (click → popup with weather).

---

## [1.0] – 2026-07-15

### Added
- Initial proof-of-concept with FastAPI and Leaflet.