
---

## 📄 `DEPLOYMENT.md` (Full)

```markdown
# EcoPulse Deployment Guide

Deploy the **EcoPulse** backend and frontend to free cloud platforms.

---

## 📦 Backend (Render)

1. Push your code to a GitHub repository.
2. Go to [Render](https://render.com) and create a new **Web Service**.
3. Connect your GitHub repo.
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Add environment variables (optional):
   - `NASA_FIRMS_TOKEN` – get from [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/download/)
   - `ELECTRICITY_MAP_TOKEN` – get from [ElectricityMap](https://www.electricitymap.org/api)
6. Deploy. Your API will be available at `https://your-app.onrender.com`.

> **Note:** `main.py` serves `dashboard.html` from the same folder. Ensure the HTML file is in the root or adjust the path accordingly.

---

## 🌐 Frontend (Vercel / Netlify)

### Option A: Serve from Backend (Simplest)
- The backend already serves `dashboard.html` at the root (`/`). Just deploy the backend as above.

### Option B: Static Hosting
1. Upload `dashboard.html` to Vercel or Netlify.
2. Update the API base URL in the JavaScript (if needed) to your backend URL.
3. Deploy.

---

## 💾 Database (Optional)

We use **in‑memory caching** by default. For production, add:
- **PostgreSQL** (via Supabase or PlanetScale) for persistent storage.
- **Redis** for caching (optional).

Update `data_fetchers.py` to store/retrieve data from a database.

---

## 🔐 Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `NASA_FIRMS_TOKEN` | Real fire data | ❌ (mock fallback) |
| `ELECTRICITY_MAP_TOKEN` | Real carbon data | ❌ (mock fallback) |
| `DATABASE_URL` | PostgreSQL connection | ❌ |
| `REDIS_URL` | Redis connection | ❌ |

Without API keys, the app uses **realistic mock data**.

---

## 🧪 Testing Deployment

After deployment, visit `/api/health` to confirm the backend is running.  
Then open the dashboard URL to start exploring.

---

## 📈 Scaling

For high traffic, consider:
- Using **Gunicorn** with Uvicorn workers.
- Adding a **CDN** for static assets.
- Enabling **Redis caching**.
- Setting up **rate limiting**.

---

## 🚀 Quick Deploy to Render

```bash
# 1. Push code to GitHub
# 2. On Render: New Web Service → Connect → Set commands (as above)
# 3. Deploy