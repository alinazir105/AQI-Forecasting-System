import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from pathlib import Path

load_dotenv()

OPENWEATHER_HISTORY_URL = "https://api.openweathermap.org/data/2.5/air_pollution/history"

KARACHI_LAT = 24.8607
KARACHI_LON = 67.0011

OUTPUT_PATH = Path("data/openweather_historical_air_pollution.csv")


def fetch_historical_air_quality(start_date: str, end_date: str) -> pd.DataFrame:
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY not found in environment variables.")

    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

    all_records = []

    current_start = start_dt

    while current_start < end_dt:
        current_end = min(current_start + timedelta(days=30), end_dt)

        params = {
            "lat": KARACHI_LAT,
            "lon": KARACHI_LON,
            "start": int(current_start.timestamp()),
            "end": int(current_end.timestamp()),
            "appid": api_key,
        }

        response = requests.get(OPENWEATHER_HISTORY_URL, params=params, timeout=20)
        response.raise_for_status()

        payload = response.json()

        for item in payload.get("list", []):
            dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            components = item.get("components", {})
            main = item.get("main", {})

            all_records.append({
                "datetime": dt.isoformat(),
                "date": dt.date().isoformat(),
                "aqi": main.get("aqi"),
                "pm25": components.get("pm2_5"),
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
            })

        print(f"Fetched: {current_start.date()} to {current_end.date()}")

        current_start = current_end
        time.sleep(1)

    df = pd.DataFrame(all_records)
    df = df.drop_duplicates(subset=["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    return df


if __name__ == "__main__":
    df = fetch_historical_air_quality(
        start_date="2021-01-01",
        end_date="2026-04-26"
    )

    print(df.head())
    print(df.tail())
    print(f"Total rows: {len(df)}")