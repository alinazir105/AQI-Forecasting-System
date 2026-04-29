from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from app.services.history_store import load_history
from app.services.forecast_service import forecast_next_days

app = FastAPI(
    title="Karachi AQI Forecasting API",
    description="3-day PM2.5 forecast for Karachi using OpenWeather data",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-deployed-frontend.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_aqi_category(pm25: float) -> dict:
    """
    OpenWeather AQI scale based on PM2.5 (µg/m³):
      1 - Good:      [0, 10)
      2 - Fair:      [10, 25)
      3 - Moderate:  [25, 50)
      4 - Poor:      [50, 75)
      5 - Very Poor: [75+]
    """
    if pm25 < 0:
        return {"aqi_index": None, "category": "Unknown"}
    elif pm25 < 10:
        return {"aqi_index": 1, "category": "Good"}
    elif pm25 < 25:
        return {"aqi_index": 2, "category": "Fair"}
    elif pm25 < 50:
        return {"aqi_index": 3, "category": "Moderate"}
    elif pm25 < 75:
        return {"aqi_index": 4, "category": "Poor"}
    else:
        return {"aqi_index": 5, "category": "Very Poor"}


@app.get("/")
def root():
    return {
        "service": "Karachi AQI Forecasting API",
        "endpoints": {
            "forecast": "/forecast",
            "current": "/current",
            "health": "/health"
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/current")
def get_current():
    history = load_history()

    if history.empty:
        return {"error": "No data available"}

    latest = history.iloc[-1]

    def safe(col):
        val = latest.get(col)
        return None if val is None or pd.isna(val) else round(float(val), 2)

    pm25 = safe("pm25")
    category = get_aqi_category(pm25) if pm25 is not None else {"aqi_index": None, "category": "Unknown"}

    return {
        "datetime": str(latest["datetime"]),
        "date": str(latest["date"]),
        "pm25": pm25,
        "pm10": safe("pm10"),
        "co":   safe("co"),
        "no2":  safe("no2"),
        "o3":   safe("o3"),
        "so2":  safe("so2"),
        "nh3":  safe("nh3"),
        "aqi_index": category["aqi_index"],
        "category":  category["category"],
        "source": str(latest.get("source", "OpenWeather")),
    }

@app.get("/forecast")
def get_forecast():
    history = load_history()

    if len(history) < 20:
        return {"error": "Not enough historical data to generate a forecast"}

    forecast = forecast_next_days(history, days=3)

    enriched = []
    for entry in forecast:
        category = get_aqi_category(entry["predicted_pm25"])
        enriched.append({
            "date": entry["date"],
            "predicted_pm25": entry["predicted_pm25"],
            "aqi_index": category["aqi_index"],
            "category": category["category"],
        })

    return {
        "city": "Karachi",
        "forecast": enriched
    }