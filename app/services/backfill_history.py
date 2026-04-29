from pathlib import Path
import pandas as pd
from app.services.history_store import save_history, load_history

HISTORICAL_DATA_PATH = Path("data/openweather_historical_air_pollution.csv")

EXPECTED_COLUMNS = [
    "datetime", "date", "aqi", "pm25", "pm10",
    "co", "no", "no2", "o3", "so2", "nh3",
    "source", "lat", "lon",
]

def backfill_history() -> pd.DataFrame:
    historical_df = pd.read_csv(HISTORICAL_DATA_PATH)
    historical_df.columns = historical_df.columns.str.strip().str.lower()

    for col in ["date", "pm25"]:
        if col not in historical_df.columns:
            raise ValueError(f"Historical dataset must contain a '{col}' column.")

    historical_df["datetime"] = pd.to_datetime(historical_df["datetime"], utc=True)
    historical_df["date"] = pd.to_datetime(historical_df["date"]).dt.date

    backfill_df = historical_df[EXPECTED_COLUMNS].copy()

    existing_history = load_history()
    combined_history = pd.concat([existing_history, backfill_df], ignore_index=True)
    save_history(combined_history)

    return load_history()


if __name__ == "__main__":
    history = backfill_history()
    print(history.tail())
    print(f"Total records: {len(history)}")