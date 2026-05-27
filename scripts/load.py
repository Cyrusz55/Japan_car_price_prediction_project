from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from database.db_connection import get_engine
from database.models import create_tables
from scripts.clean import CLEAN_PATH

def load_clean_data():
    engine = get_engine()
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS cleaned_japan_cars")
    create_tables(engine)

    df = pd.read_csv(CLEAN_PATH, low_memory=False)
    print(f"[load] {len(df)} cleaned records to load")

    df.to_sql(
        "cleaned_japan_cars",
        engine,
        if_exists = 'append',
        index = False,
        method = 'multi',
        chunksize = 500
    )
    print("[load] Cleaned data loaded into 'cleaned_japan_cars' table")
if __name__ == "__main__":
    load_clean_data()