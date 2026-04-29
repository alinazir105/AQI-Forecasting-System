import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

OPENWEATHER_AIR_URL = "https://api.openweathermap.org/data/2.5/air_pollution"

KARACHI_LAT = 24.8607
KARACHI_LON = 67.0011


def fetch_current_air_quality() -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY not found in environment variables.")

    params = {
        "lat": KARACHI_LAT,
        "lon": KARACHI_LON,
        "appid": api_key,
    }

    res = requests.get(OPENWEATHER_AIR_URL, params=params, timeout=10)
    res.raise_for_status()

    payload = res.json()

    if "list" not in payload or len(payload["list"]) == 0:
        raise ValueError("OpenWeather returned no air pollution records.")

    item = payload["list"][0]

    dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
    components = item.get("components", {})
    main = item.get("main", {})

    pm25 = components.get("pm2_5")

    if pm25 is None:
        raise ValueError("PM2.5 value not available in OpenWeather response.")

    record = {
        "datetime": dt.isoformat(),
        "date": dt.date().isoformat(),
        "aqi": main.get("aqi"),
        "pm25": pm25,
        "pm10": components.get("pm10"),
        "co": components.get("co"),
        "no": components.get("no"),
        "no2": components.get("no2"),
        "o3": components.get("o3"),
        "so2": components.get("so2"),
        "nh3": components.get("nh3"),
        "source": "OpenWeather",
        "lat": KARACHI_LAT,
        "lon": KARACHI_LON,
    }

    return record


if __name__ == "__main__":
    print(fetch_current_air_quality())