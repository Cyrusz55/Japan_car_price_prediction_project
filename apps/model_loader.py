import joblib
import os

_model = None
def load_model():
    global _model
    path = os.getenv("MODEL_PATH", "models/car_price_model.joblib")
    _model = joblib.load(path)
    return _model
def get_model():
    if _model is None:
        load_model()
    return _model