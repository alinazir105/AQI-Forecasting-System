import pandas as pd


FEATURE_COLUMNS = [
    'pm25_rolling_7',
    'pm25_rolling_14',
    'month',
    'lag_1',
    'lag_2',
    'lag_3',
    'lag_7',
    'pm10_lag_1',
    'co_lag_1',
    'no2_lag_1',
    'so2_lag_1',
    'nh3_lag_1'
]


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")

    today = pd.to_datetime("today").date()
    df = df[df["date"] < today]

    daily_df = (
        df.groupby("date", as_index=False)
        .agg(
            pm25=("pm25", "mean"),
            pm10=("pm10", "mean"),
            co=("co", "mean"),
            no2=("no2", "mean"),
            so2=("so2", "mean"),
            nh3=("nh3", "mean"),
        )
    )

    daily_df["datetime"] = pd.to_datetime(daily_df["date"])
    daily_df = daily_df.sort_values("datetime").reset_index(drop=True)

    daily_df["month"] = daily_df["datetime"].dt.month

    daily_df["lag_1"] = daily_df["pm25"].shift(1)
    daily_df["lag_2"] = daily_df["pm25"].shift(2)
    daily_df["lag_3"] = daily_df["pm25"].shift(3)
    daily_df["lag_7"] = daily_df["pm25"].shift(7)

    daily_df["pm25_rolling_7"] = daily_df["pm25"].rolling(7).mean()
    daily_df["pm25_rolling_14"] = daily_df["pm25"].rolling(14).mean()

    daily_df["pm10_lag_1"] = daily_df["pm10"].shift(1)
    daily_df["co_lag_1"] = daily_df["co"].shift(1)
    daily_df["no2_lag_1"] = daily_df["no2"].shift(1)
    daily_df["so2_lag_1"] = daily_df["so2"].shift(1)
    daily_df["nh3_lag_1"] = daily_df["nh3"].shift(1)

    daily_df = daily_df.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)

    return daily_df