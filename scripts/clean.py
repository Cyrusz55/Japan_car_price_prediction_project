from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / 'data' / 'raw' / 'cars.csv'
CLEAN_PATH = PROJECT_ROOT / 'data' / 'clean' / 'cleaned_cars.csv'
target_col = 'price_log'

def clean_data(df: pd.DataFrame) ->pd.DataFrame:
    print(f"[clean] Starting shape: {df.shape}")

    # drop uneccesary columns
    features = ["vehicle_age", "doors_num", "seats_num", "market_country", "stock_country", "is_overseas_stock", "make_clean", "model_clean", "age_bucket", "fuel_group", "transmission_group", "drive_group", "steering_group", "vin_region", "body_guess"]
    df_cleaned = df[features + [target_col]].copy()

    print(f"[clean] Final shape: {df_cleaned.shape}")

    return df_cleaned
if __name__ == "__main__":
    df_raw = pd.read_csv(RAW_PATH,low_memory=False)
    df_clean = clean_data(df_raw)
    df_clean.to_csv(CLEAN_PATH, index=False)
    print(f"[clean] Cleaned data saved to {CLEAN_PATH}")