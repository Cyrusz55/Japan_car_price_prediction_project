from fastapi import APIRouter, HTTPException
import os
import joblib
import pandas as pd
import numpy as np

from apps.schemas import JapanCarInput, PredictionResponse

from machine_learning.machine_learning import (
load_model,
predict_new_price,
)
router = APIRouter()
@router.get("/health")
def health_check():
    return {"status": "ok", "message": "API is healthy"}

@router.post("/predict", response_model=PredictionResponse)
def predict(input_data: JapanCarInput):
    try:
        model = load_model()
        new_data = pd.DataFrame([input_data.model_dump()])
        # model predicts in log scale, converts back to actual salary
        log_prediction = predict_new_price(model, new_data)[0]
        actual_price = np.expm1(log_prediction)
        return PredictionResponse(predicted_price=float(actual_price))
    except FileNotFoundError:
        raise HTTPException(
            status_code = 503,
            detail = "Model not yet trained. Run training first."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-info")
def model_info():
    path = os.getenv("MODEL_PATH", "models/car_price_model.joblib")

    if not os.path.exists(path):
        return {"status": "no model found"}

    model = joblib.load(path)
    return{
        "model_type": type(model).__name__,
        "model_path": path,
    }
