from pathlib import Path
import pandas as pd
from app.services.api_fetcher import fetch_current_air_quality
from pandas.errors import EmptyDataError

HISTORY_PATH = Path("data/api_history.csv")

EXPECTED_COLUMNS = [
    "datetime",
    "date",
    "aqi",
    "pm25",
    "pm10",
    "co",
    "no",
    "no2",
    "o3",
    "so2",
    "nh3",
    "source",
    "lat",
    "lon",
]


def load_history() -> pd.DataFrame:
    if not HISTORY_PATH.exists() or HISTORY_PATH.stat().st_size == 0:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    try:
        df = pd.read_csv(HISTORY_PATH)
    except EmptyDataError:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    if not df.empty:
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("datetime").reset_index(drop=True)

    return df


def save_history(df: pd.DataFrame) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    df = df.drop_duplicates(subset=["datetime"], keep="last")
    df = df.sort_values("datetime").reset_index(drop=True)

    df.to_csv(HISTORY_PATH, index=False)


def append_record(record: dict) -> pd.DataFrame:
    history = load_history()

    new_row = pd.DataFrame([record])
    new_row["datetime"] = pd.to_datetime(new_row["datetime"], utc=True)
    new_row["date"] = pd.to_datetime(new_row["date"]).dt.date

    updated_history = pd.concat([history, new_row], ignore_index=True)

    save_history(updated_history)

    return load_history()


if __name__ == "__main__":
    record = fetch_current_air_quality()
    history = append_record(record)
    print(history.tail())