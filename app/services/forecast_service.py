import joblib
import pandas as pd
from datetime import timedelta
from app.services.feature_pipeline import create_features

MODEL_PATH = "models/Ridge-Regression-Pipeline.pkl"
FEATURES_PATH = "models/features.pkl"

model = joblib.load(MODEL_PATH)
feature_names = joblib.load(FEATURES_PATH)


def forecast_next_days(df: pd.DataFrame, days: int = 3) -> list[dict]:
    # Build features once from real history
    df_feat = create_features(df)

    # Get last known raw pollutant values to carry forward
    last_raw = df.sort_values("datetime").iloc[-1]

    forecasts = []

    for i in range(days):
        last_row = df_feat.iloc[-1]

        # Predict using current feature row
        latest_features = df_feat.iloc[-1:][feature_names]
        prediction = float(model.predict(latest_features)[0])

        # Calculate next date
        last_date = last_row["date"]
        if hasattr(last_date, 'date'):
            last_date = last_date.date()
        next_date = last_date + timedelta(days=1)

        # Manually build next feature row by shifting lags
        next_row = {
            "date": next_date,
            "datetime": pd.Timestamp(next_date, tz="UTC"),
            "pm25": prediction,
            "pm10": float(last_raw.get("pm10") or 0),
            "co":   float(last_raw.get("co") or 0),
            "no2":  float(last_raw.get("no2") or 0),
            "so2":  float(last_raw.get("so2") or 0),
            "nh3":  float(last_raw.get("nh3") or 0),
            # Shift pm25 lags forward
            "lag_1": prediction,
            "lag_2": float(last_row["lag_1"]),
            "lag_3": float(last_row["lag_2"]),
            "lag_7": float(last_row["lag_3"]),
            # Update rolling averages
            "pm25_rolling_7":  float((last_row["pm25_rolling_7"] * 6 + prediction) / 7),
            "pm25_rolling_14": float((last_row["pm25_rolling_14"] * 13 + prediction) / 14),
            "month": pd.Timestamp(next_date).month,
            # Carry forward pollutant lags
            "pm10_lag_1": float(last_raw.get("pm10") or 0),
            "co_lag_1":   float(last_raw.get("co") or 0),
            "no2_lag_1":  float(last_raw.get("no2") or 0),
            "so2_lag_1":  float(last_raw.get("so2") or 0),
            "nh3_lag_1":  float(last_raw.get("nh3") or 0),
        }

        df_feat = pd.concat(
            [df_feat, pd.DataFrame([next_row])],
            ignore_index=True
        )

        forecasts.append({
            "date": next_date.isoformat(),
            "predicted_pm25": round(prediction, 2)
        })

    return forecasts


if __name__ == "__main__":
    from app.services.history_store import load_history
    history = load_history()
    forecast = forecast_next_days(history, days=3)
    for row in forecast:
        print(row)