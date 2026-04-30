import joblib
import pandas as pd
from datetime import timedelta
from app.services.feature_pipeline import create_features

MODEL_PATH = "models/Ridge-Regression-Pipeline.pkl"
FEATURES_PATH = "models/features.pkl"

model = joblib.load(MODEL_PATH)
feature_names = joblib.load(FEATURES_PATH)


def predict_next(df: pd.DataFrame) -> float:
    df_feat = create_features(df)
    latest = df_feat.iloc[-1:][feature_names]
    prediction = model.predict(latest)
    return float(prediction[0])


def forecast_next_days(df: pd.DataFrame, days: int = 3) -> list[dict]:
    history = df.copy()
    forecasts = []

    # Carry forward last known pollutant values into forecasted rows
    last_known = history.iloc[-1]

    for _ in range(days):
        prediction = predict_next(history)

        last_date = pd.to_datetime(history["date"]).max().date()
        next_date = last_date + timedelta(days=1)

        new_row = {
            "datetime": pd.Timestamp(next_date, tz="UTC"),
            "date": next_date,
            "pm25": prediction,
            "aqi": None,
            "source": "Forecasted",
            "pm10": last_known.get("pm10"),
            "co":   last_known.get("co"),
            "no":   last_known.get("no"),
            "no2":  last_known.get("no2"),
            "o3":   last_known.get("o3"),
            "so2":  last_known.get("so2"),
            "nh3":  last_known.get("nh3"),
            "lat":  last_known.get("lat"),
            "lon":  last_known.get("lon"),
        }

        history = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)

        # Update so next iteration uses the latest appended row
        last_known = pd.Series(new_row)

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