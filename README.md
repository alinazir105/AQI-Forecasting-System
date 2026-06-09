# Karachi AQI Forecasting System

An end-to-end air quality forecasting system that predicts daily average PM2.5 concentrations for Karachi 3 days ahead, classifies results into AQI health categories, and serves predictions through a REST API with a React dashboard frontend.

**Live coordinates:** 24.8607°N, 67.0011°E  
**Data source:** OpenWeather Air Pollution API  
**Model:** Ridge Regression (recursive multi-step forecasting)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [ML Pipeline](#ml-pipeline)
  - [Feature Engineering](#feature-engineering)
  - [Model Selection & Results](#model-selection--results)
  - [Forecasting Strategy](#forecasting-strategy)
- [API Reference](#api-reference)
- [AQI Scale](#aqi-scale)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Data Pipeline](#data-pipeline)
- [Frontend](#frontend)
- [Hopsworks Integration](#hopsworks-integration)
- [Retraining](#retraining)

---

## Overview

Air quality in Karachi is a significant public health concern. This system collects real-time and historical hourly pollutant data, engineers time-series features, and uses a Ridge Regression model to forecast the next 3 days of PM2.5 — the pollutant most strongly linked to respiratory harm.

Key capabilities:

- Hourly data collection via a background scheduler or cron-triggered `/collect` endpoint
- 4+ years of historical backfill (2021–2026) for robust model training
- Recursive 3-day PM2.5 forecast with AQI category labels
- Live hazard alerts when current or forecasted air quality is Poor or worse
- Optional feature store and model registry integration via Hopsworks
- `/retrain` endpoint to refresh the model in production without redeployment

---

## Architecture

```
OpenWeather API
      │
      ▼
api_fetcher.py ──► history_store.py (data/api_history.csv)
                          │
                          ▼
                  feature_pipeline.py
                  (lag features, rolling stats, calendar)
                          │
                          ▼
                  Ridge Regression Model
                  (models/Ridge-Regression-Pipeline.pkl)
                          │
                          ▼
                  forecast_service.py
                  (recursive 3-day prediction)
                          │
                          ▼
                    FastAPI (main.py)
                    /current  /forecast
                          │
                          ▼
                  React Dashboard (AQIDashboard.jsx)
```

---

## Project Structure

```
├── app/
│   └── services/
│       ├── api_fetcher.py          # Fetches live AQI data from OpenWeather
│       ├── history_store.py        # Loads/saves/appends to CSV history
│       ├── feature_pipeline.py     # Time-series feature engineering
│       ├── forecast_service.py     # Recursive 3-day PM2.5 forecasting
│       └── hopswork_store.py       # Hopsworks feature store & model registry
├── data/
│   ├── api_history.csv             # Live + backfilled hourly records
│   └── openweather_historical_air_pollution.csv  # Backfill source
├── models/
│   ├── Ridge-Regression-Pipeline.pkl   # Trained sklearn Pipeline
│   └── features.pkl                    # Ordered feature names list
├── main.py                         # FastAPI app
├── scheduler.py                    # Standalone hourly data collector
├── backfill_history.py             # One-time historical data loader
├── historical_fetcher.py           # Fetches multi-year history from OpenWeather
├── model_loader.py                 # Debug utility: inspect features
├── notebook.ipynb                  # Full EDA, modelling, and backtesting
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── AQIDashboard.jsx        # Main dashboard component
│   └── .env                        # VITE_API_URL
└── requirements.txt
```

---

## ML Pipeline

### Feature Engineering

Raw hourly records are aggregated to daily means before features are computed. All features are constructed strictly from past observations to prevent data leakage.

| Feature | Description |
|---|---|
| `lag_1` | PM2.5 from 1 day ago |
| `lag_2` | PM2.5 from 2 days ago |
| `lag_3` | PM2.5 from 3 days ago |
| `lag_7` | PM2.5 from 7 days ago |
| `pm25_rolling_7` | 7-day rolling mean of PM2.5 |
| `pm25_rolling_14` | 14-day rolling mean of PM2.5 |
| `month` | Calendar month (captures seasonality) |
| `pm10_lag_1` | PM10 from 1 day ago |
| `co_lag_1` | CO from 1 day ago |
| `no2_lag_1` | NO₂ from 1 day ago |
| `so2_lag_1` | SO₂ from 1 day ago |
| `nh3_lag_1` | NH₃ from 1 day ago |

Features are defined in `feature_pipeline.py` and the ordered list is persisted at `models/features.pkl` to guarantee consistent column ordering between training and inference.

### Model Selection & Results

Five model families were evaluated using 5-fold `TimeSeriesSplit` cross-validation on 4+ years of daily data. Random train/test splitting was explicitly avoided to prevent temporal leakage.

| Model | Avg MAE (µg/m³) | Avg RMSE (µg/m³) | Avg R² |
|---|---|---|---|
| Linear Regression | 27.80 | 46.35 | 0.612 |
| **Ridge Regression** | **27.71** | **46.32** | **0.613** |
| Random Forest | 28.10 | 47.20 | 0.617 |
| XGBoost | 29.40 | 49.17 | 0.579 |
| LSTM | 15.38 | 25.09 | — |

Ridge Regression was selected for production. While the LSTM achieved lower error, Ridge was preferred for its stability, interpretability, lower inference latency, and suitability for recursive multi-step forecasting. The LSTM's advantage partially reflects optimistic evaluation under sequential prediction conditions.

The production model is a scikit-learn `Pipeline` combining `StandardScaler` and `Ridge(alpha=1.0)`.

**Reported forecast error: ~27.7 µg/m³ MAE** (disclosed in the frontend footer).

### Forecasting Strategy

The system uses **recursive (iterative) forecasting**: the model predicts one day at a time, and each prediction is fed back as a lag feature for the next step.

For each forecast step:
1. Extract the final feature row from history.
2. Run `model.predict()` to get `predicted_pm25`.
3. Construct the next feature row by shifting lags forward, updating rolling averages with an online formula, and carrying forward the last known pollutant values.
4. Append the synthetic row and repeat for the next day.

This is implemented in `forecast_service.py::forecast_next_days()`.

---

## API Reference

Base URL: configured via `VITE_API_URL` (frontend) or direct FastAPI host.

### `GET /`
Returns service info and available endpoints.

### `GET /health`
Health check. Returns `{"status": "ok"}`.

### `GET /current`
Returns the latest recorded air quality reading.

```json
{
  "datetime": "2026-06-08T18:00:00+00:00",
  "date": "2026-06-08",
  "pm25": 42.5,
  "pm10": 78.3,
  "co": 310.2,
  "no2": 12.1,
  "o3": 55.0,
  "so2": 3.4,
  "nh3": 1.2,
  "aqi_index": 3,
  "category": "Moderate",
  "source": "OpenWeather"
}
```

### `GET /forecast`
Returns 3-day PM2.5 forecast with AQI labels. Requires at least 20 records in history.

```json
{
  "city": "Karachi",
  "forecast": [
    { "date": "2026-06-09", "predicted_pm25": 38.12, "aqi_index": 3, "category": "Moderate" },
    { "date": "2026-06-10", "predicted_pm25": 41.05, "aqi_index": 3, "category": "Moderate" },
    { "date": "2026-06-11", "predicted_pm25": 44.60, "aqi_index": 3, "category": "Moderate" }
  ]
}
```

### `POST /collect?api_key=<secret>`
Fetches current air quality from OpenWeather and appends it to history. Protected by `COLLECT_SECRET`.

### `POST /retrain?api_key=<secret>`
Retrains the Ridge model on the current full history (requires ≥100 rows). Overwrites `models/Ridge-Regression-Pipeline.pkl` in place.

### `GET /download-history?api_key=<secret>`
Downloads `data/api_history.csv` as a file attachment.

### `GET /debug-forecast` / `GET /debug-forecast2`
Development endpoints that expose the last feature row and step-by-step forecast values for debugging recursive prediction.

---

## AQI Scale

The system uses the OpenWeather PM2.5 thresholds (µg/m³):

| Index | Category | PM2.5 Range |
|---|---|---|
| 1 | Good | < 10 |
| 2 | Fair | 10 – 24.9 |
| 3 | Moderate | 25 – 49.9 |
| 4 | Poor | 50 – 74.9 |
| 5 | Very Poor | ≥ 75 |

A hazard alert is shown in the dashboard whenever the current reading or any forecasted day reaches index 4 (Poor) or higher.

---

## Setup & Installation

### Backend

```bash
# 1. Clone and create environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install fastapi uvicorn pandas scikit-learn joblib python-dotenv requests hopsworks

# 3. Set environment variables (see below)
cp .env.example .env

# 4. Backfill historical data (first run only)
python historical_fetcher.py   # fetches 2021–present from OpenWeather
python backfill_history.py     # loads it into data/api_history.csv

# 5. Ensure trained model files exist
#    models/Ridge-Regression-Pipeline.pkl
#    models/features.pkl
#    (train via notebook.ipynb if not present)

# 6. Start the API
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# Set VITE_API_URL in .env
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

### Continuous Data Collection

Either run the standalone scheduler:
```bash
python scheduler.py
```

Or trigger collection via cron/GitHub Actions hitting:
```
POST /collect?api_key=<COLLECT_SECRET>
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENWEATHER_API_KEY` | Yes | OpenWeather API key (free tier sufficient) |
| `COLLECT_SECRET` | Yes | Protects `/collect`, `/retrain`, `/download-history` |
| `HOPSWORKS_API_KEY` | Optional | For feature store / model registry integration |
| `HOPSWORKS_PROJECT` | Optional | Hopsworks project name |
| `VITE_API_URL` | Frontend | Backend base URL (e.g. `https://your-api.com`) |

---

## Data Pipeline

### First Run (Historical Backfill)

1. `historical_fetcher.py` calls the OpenWeather historical air pollution endpoint in 30-day chunks and writes `data/openweather_historical_air_pollution.csv`.
2. `backfill_history.py` reads that file and merges it into `data/api_history.csv`, deduplicating on `datetime`.

### Ongoing Collection

`scheduler.py` or the `/collect` endpoint appends one record per hour to `api_history.csv`. Deduplication is enforced on write in `history_store.py::save_history()`.

### History Format

```
datetime, date, aqi, pm25, pm10, co, no, no2, o3, so2, nh3, source, lat, lon
```

---

## Frontend

The React frontend (`AQIDashboard.jsx`) fetches from `/current` and `/forecast` on load and renders:

- **Current card** — PM2.5 reading with AQI badge, colour-coded by severity
- **Hazard alert** — shown when AQI index ≥ 4 for current or any forecast day
- **3-day forecast cards** — one card per day with predicted PM2.5 and AQI badge
- **PM2.5 trend chart** — Recharts line chart with AQI-coloured dots
- **Pollutant grid** — current levels for PM2.5, PM10, CO, NO₂, SO₂, O₃
- **AQI legend** — colour key for all five categories

The frontend is designed to deploy to Vercel. Set `VITE_API_URL` in the Vercel environment variables to point at your production API.

**Allowed CORS origins** (configured in `main.py`):
- `http://localhost:5173`
- `https://aqi-forecasting-system.vercel.app`

Update `allow_origins` if deploying to a different domain.

---

## Hopsworks Integration

`hopswork_store.py` provides optional integration with [Hopsworks](https://www.hopsworks.ai) for:

- **Feature storage** — `push_features(df)` uploads engineered feature rows to the `karachi_aqi_features` feature group
- **Model registry** — `push_model(path, metrics)` registers the trained model with evaluation metrics
- **Pull for inference** — `pull_features()` and `pull_model()` retrieve stored assets

This is optional; the production system uses local CSV and `joblib` files by default.

---

## Retraining

The `/retrain` endpoint re-fits the Ridge model on the full current history without redeploying:

```bash
curl -X POST "https://your-api.com/retrain?api_key=YOUR_SECRET"
```

Requirements:
- At least 100 rows in `api_history.csv`
- `models/features.pkl` must exist (column order is reused)

The retrained pipeline is saved back to `models/Ridge-Regression-Pipeline.pkl` and picked up by `forecast_service.py` on the next request (model is loaded at module import time; a process restart may be needed depending on your deployment setup).

To retrain from scratch with the notebook, run all cells in `notebook.ipynb` through the model persistence section and copy the output `.pkl` files to `models/`.
