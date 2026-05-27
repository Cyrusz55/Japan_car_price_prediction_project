from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from database.db_connection import get_engine

RAW_SCV_PATH = PROJECT_ROOT / "data"/"raw"/"cars.csv"

TARGET_TABLE = "japanese_cars_raw"
RAW_COLUMNS = [
    "vehicle_age",
    "doors_num",
    "seats_num",
    "market_country",
    "stock_country",
    "is_overseas_stock",
    "make_clean",
    "model_clean",
    "age_bucket",
    "fuel_group",
    "transmission_group",
    "drive_group",
    "steering_group",
    "vin_region",
    "body_guess",
    "price_log",
]
def ingest_raw_data():
    engine = get_engine()
    df = pd.read_csv(RAW_SCV_PATH, usecols=RAW_COLUMNS, low_memory=False)
    df["price_log"] = pd.to_numeric(df["price_log"], errors="coerce")
    df = df.dropna(subset=["price_log"])
    print(f"[ingest] Loaded {len(df)} rows from {RAW_SCV_PATH}")
    print(f"[ingest] Columns: {list(df.columns)}")

    with engine.begin() as conn:
        conn.exec_driver_sql(f'DROP TABLE IF EXISTS {TARGET_TABLE} CASCADE')

    df.to_sql(
        TARGET_TABLE,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )

    print("[ingest] Raw data loaded into 'dev_salary_raw' table")

if __name__ == "__main__":
    ingest_raw_data()