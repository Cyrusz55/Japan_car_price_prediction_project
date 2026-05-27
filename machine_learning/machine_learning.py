import os
import joblib
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor



MODEL_PATH = "models/japan_cars_price_model.pkl"
TARGET_COL = "price_log"

NUM_COLS = ['vehicle_age', 'doors_num', 'seats_num']
CAT_COLS = ['model_clean', 'make_clean', 'market_country', 'stock_country', 'is_overseas_stock', 'age_bucket', 'fuel_group', 'transmission_group', 'drive_group', 'steering_group', 'vin_region', 'body_guess']

High_card_cols = ['model_clean', 'make_clean']
Low_card_cols = ['market_country', 'stock_country', 'is_overseas_stock', 'age_bucket', 'fuel_group', 'transmission_group', 'drive_group', 'steering_group', 'vin_region', 'body_guess']

def get_X_y(df: pd.DataFrame):
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]
    return X, y
def to_string(X):
    """Convert array to string dtype for categorical handling."""
    if hasattr(X, 'fillna'):  # is pandas
        return X.fillna('MISSING').astype(str)
    else:  # is numpy array
        import pandas as pd
        return pd.Series(X).fillna('MISSING').astype(str).values

def build_pipeline():
    num_pipeline = Pipeline(
        steps = [
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]
    )

    # Create FunctionTransformer for string conversion (handles missing values)
    to_string_transformer = FunctionTransformer(
        to_string,
        validate=False,
        feature_names_out="one-to-one",
    )

    high_card_pipeline = Pipeline([
        ('to_string', to_string_transformer),
        ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value',
                                   unknown_value=-1, dtype='int64'))
    ])
    low_card_pipeline = Pipeline([
        ('to_string', to_string_transformer),
        ('encoder', OneHotEncoder(handle_unknown='ignore', drop='first', sparse_output=False, min_frequency=1))
    ])
    preprocessor = ColumnTransformer([
        ('num', num_pipeline, NUM_COLS),
        ('high_card_cat', high_card_pipeline, High_card_cols),
        ('low_card_cat', low_card_pipeline, Low_card_cols)
    ])
    model = Pipeline(
        steps = [
            ('preprocessor', preprocessor),
            ('regressor', GradientBoostingRegressor(random_state=42))
        ]
    )
    return model
def train_model(df: pd.DataFrame):
    X, y = get_X_y(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = build_pipeline()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"Model Training Results (Target in Log Scale):")
    print(f"  MAE (Log Scale): {mae:.4f}")
    print(f"  RMSE (Log Scale): {rmse:.4f}")
    print(f"  R² Score: {r2:.4f}")
    print(f"\nNote: Target variable (price) is in log scale using np.log1p()")
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return model, X_test, y_test
def predict_new_price(model, new_data: pd.DataFrame):
    return model.predict(new_data)
def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    return joblib.load(MODEL_PATH)
def predict_single(input_data: dict):
    model =load_model()
    df = pd.DataFrame([input_data])
    log_prediction = model.predict(df)[0]
    actual_price = np.expm1(log_prediction)
    return actual_price


if __name__ == "__main__":
    df = pd.read_csv("data/clean/cleaned_cars.csv", low_memory=False)
    train_model(df)