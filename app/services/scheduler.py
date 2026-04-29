import time
from app.services.history_store import append_record
from app.services.api_fetcher import fetch_current_air_quality

while True:
    try:
        record = fetch_current_air_quality()
        append_record(record)
        print("Data collected")
    except Exception as e:
        print("Error:", e)

    time.sleep(3600)  # 1 hour