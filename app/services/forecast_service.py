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

    for _ in range(days):
        prediction = predict_next(history)

        last_date = pd.to_datetime(history["date"]).max().date()
        next_date = last_date + timedelta(days=1)

        new_row = {
            "datetime": pd.to_datetime(next_date),
            "date": next_date,
            "pm25": prediction,
            "aqi": None,
            "station": "Forecasted"
        }

        history = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)

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