# ☁️ EcoPulse Render Deployment Guide

Follow this step-by-step guide to deploy **EcoPulse** on Render.

---

## 1. Render Web Service Setup

1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository containing `main.py`.
4. Configure the runtime parameters:
   - **Name:** `ecopulse` (or your preferred service name)
   - **Environment:** `Python 3`
   - **Build Command:**
     ```bash
     pip install fastapi uvicorn httpx requests pydantic
     ```
   - **Start Command:**
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

---

## 2. Environment Variables Configuration

In your Render Service settings, navigate to **Environment** and add the following keys:

| Key | Example Value | Description |
| :--- | :--- | :--- |
| `SENDER_EMAIL` | `your.email@gmail.com` | Gmail address used for sending alerts |
| `SENDER_PASSWORD` | `xxxx xxxx xxxx xxxx` | **16-digit Google App Password** |
| `SMTP_SERVER` | `smtp.gmail.com` | SMTP Server Host |
| `SMTP_PORT` | `465` | **465** (Recommended for SSL on Render) |
| `ELECTRICITY_MAPS_TOKEN` | *(Optional)* | API token for real-time grid carbon data |
| `NASA_FIRMS_TOKEN` | *(Optional)* | API token for live satellite thermal data |

> ⚠️ **Important Google App Password Note:**
> Do NOT use your primary Gmail account password. Go to **Google Account Settings -> Security -> 2-Step Verification -> App Passwords**, generate a key for "EcoPulse", and paste it into `SENDER_PASSWORD`.

---

## 3. Verifying Deployment

Once deployed, test your live instance:
- **Main Dashboard:** `https://<your-render-app>.onrender.com/`
- **Compare Page:** `https://<your-render-app>.onrender.com/compare`
- **Swagger Docs:** `https://<your-render-app>.onrender.com/docs`