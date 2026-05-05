import hopsworks
import pandas as pd
import os

FEATURE_GROUP_NAME = "karachi_aqi_features"
FEATURE_GROUP_VERSION = 1
MODEL_NAME = "karachi_aqi_ridge"
MODEL_VERSION = 1


def get_feature_store():
    project = hopsworks.login(
        host="eu-west.cloud.hopsworks.ai",  # correct host
        project=os.getenv("HOPSWORKS_PROJECT"),
        api_key_value=os.getenv("HOPSWORKS_API_KEY"),
    )
    return project.get_feature_store()


def push_features(df: pd.DataFrame) -> None:
    fs = get_feature_store()
    df = df.copy()
    df = df.reset_index(drop=True)
    df["row_id"] = df.index.astype("int64")  # correct primary key
    df = df.astype({col: "float64" for col in df.columns if col != "row_id"})

    fg = fs.get_or_create_feature_group(
        name=FEATURE_GROUP_NAME,
        version=FEATURE_GROUP_VERSION,
        description="Daily engineered AQI features for Karachi",
        primary_key=["row_id"],  # correct primary key
    )
    fg.insert(df, write_options={"wait_for_job": True})
    print(f"Pushed {len(df)} rows to Hopsworks feature store.")


def pull_features() -> pd.DataFrame:
    """Pull engineered features from Hopsworks feature store."""
    fs = get_feature_store()
    fg = fs.get_feature_group(FEATURE_GROUP_NAME, version=FEATURE_GROUP_VERSION)
    df = fg.read()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.sort_values("date").reset_index(drop=True)


def push_model(model_path: str, metrics: dict) -> None:
    project = hopsworks.login(
        host="eu-west.cloud.hopsworks.ai",  # fixed
        project=os.getenv("HOPSWORKS_PROJECT"),
        api_key_value=os.getenv("HOPSWORKS_API_KEY"),
    )
    mr = project.get_model_registry()
    model = mr.python.create_model(
        name=MODEL_NAME,
        metrics=metrics,
        description="Ridge Regression model for Karachi PM2.5 forecasting",
    )
    model.save(model_path)
    print("Model registered in Hopsworks model registry.")


def pull_model(local_path: str) -> str:
    project = hopsworks.login(
        host="eu-west.cloud.hopsworks.ai",  # fixed
        project=os.getenv("HOPSWORKS_PROJECT"),
        api_key_value=os.getenv("HOPSWORKS_API_KEY"),
    )
    mr = project.get_model_registry()
    model = mr.get_best_model(MODEL_NAME, metric="mae", direction="min")
    model_dir = model.download()
    return model_dir