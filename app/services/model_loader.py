from app.services.history_store import load_history
from app.services.feature_pipeline import create_features
import joblib

history = load_history()
features = create_features(history)

feature_names = joblib.load("models/features.pkl")

print(features.tail())
print(features[feature_names].tail())