# 🚗 Japan Used Car Price Predictor

**ML-powered valuation system for Japanese used car exports with production-ready FastAPI backend and premium web frontend.**

---

## 📋 Overview

This project provides an end-to-end machine learning pipeline to predict market prices for used vehicles exported from Japan. It combines web scraping, automated feature engineering, rigorous model evaluation, and a production-ready API with an intuitive web interface.

**Key capabilities:**
- **Real-time predictions** via REST API
- **Feature engineering** pipeline with 40+ engineered features
- **Multiple model comparisons** (Gradient Boosting, XGBoost, Random Forest, etc.)
- **Premium web frontend** with smooth UX and responsive design
- **Database persistence** with PostgreSQL integration

---

## 🎯 Model Performance

### Cross-Validation Results (5-Fold)

| Model | CV R² Mean | CV MAE | CV RMSE | Test R² | Test RMSE |
|-------|-----------|--------|---------|---------|-----------|
| **Gradient Boosting** ⭐ | **0.7417** | 0.4216 | 0.4537 | **0.7653** | **0.39** |
| XGBoost | 0.7118 | 0.4395 | 0.4825 | 0.7638 | 0.39 |
| Random Forest | 0.6647 | 0.4892 | 0.5237 | 0.7397 | 0.41 |
| Linear Regression | 0.6654 | 0.5104 | 0.5141 | 0.5954 | 0.51 |
| Ridge Regression | 0.6450 | 0.5341 | 0.5237 | 0.5928 | 0.52 |
| Decision Tree | 0.5056 | 0.6234 | 0.6123 | 0.5726 | 0.53 |
| Lasso Regression | 0.2648 | 0.9871 | 0.8904 | 0.3261 | 0.66 |
| KNN (k=5) | 0.5198 | 0.7123 | 0.6945 | 0.5105 | 0.57 |

**Best Model:** Gradient Boosting with **R² = 0.7653** on test set

---

## 🛠️ Technology Stack

### Backend
- **Python 3.13**
- **FastAPI** – high-performance async API
- **SQLAlchemy** – ORM with PostgreSQL
- **Scikit-learn** – preprocessing & model training
- **Gradient Boosting** – production model
- **APScheduler** – weekly model retraining
- **Pydantic** – request/response validation

### Frontend
- **HTML5 + Vanilla JavaScript** – zero-dependency UI
- **CSS3 with CSS Variables** – modern, responsive styling
- **Geist Font** – professional typography
- **Smooth animations** – spring-based, snappy transitions

### Infrastructure
- **Supabase PostgreSQL** – cloud database
- **Environment variables** – secure configuration

---

## 📊 Dataset & Features

### Data Sources
- BeForward.jp (primary)
- SBT Japan (secondary)
- ~300k+ vehicle listings

### Feature Categories

**Numeric Features (3)**
- Vehicle age (years)
- Number of doors
- Number of seats

**Categorical Features (12)**
- Manufacturer (e.g., TOYOTA, NISSAN, BMW)
- Model name (high-cardinality)
- Market country (e.g., Japan, Mozambique)
- Stock country (Japan, Singapore, UK, Australia)
- Fuel type (Petrol, Diesel, Hybrid, Electric)
- Transmission (Manual, Automatic, CVT)
- Drive system (2WD, 4WD)
- Steering (Left, Right)
- VIN region (inferred from chassis)
- Body type (sedan, SUV, wagon, truck, etc.)
- Age bucket (0-1, 2-3, 4-5, 6-10, 11-20, 20+ years)
- Overseas stock indicator

### Feature Engineering Pipeline
- **URL parsing** – extract manufacturer and model from listing URLs
- **Price transformation** – log-scale normalization (`price_log = np.log1p(price)`)
- **Age derivation** – computed from model year (reference: 2026)
- **Categorical normalization** – standardized fuel, transmission, drive categories
- **VIN detection** – identify valid VINs and extract region code
- **Body-style heuristic** – keyword-based classification with logic rules
- **Price ranking** – percentile rank within make/model groups

- **Price ranking** – percentile rank within make/model groups

---

## 📈 Visualizations

### Distribution Analysis
![Normal and Log Distribution](./photos/normal_and_log_distribution.png)
*Price distribution in normal and log-scale. Log transformation helps normalize skewed price data for better model performance.*

### Correlation Heatmap
![Correlation Matrix](./photos/correlation.png)
*Feature correlations reveal relationships between vehicle attributes and price. Used to guide feature selection.*

### Frontend Screenshots

**Input Form Section**
![Frontend - Input Form](./photos/frontend1.png)
*Organized input panels for vehicle specifications, market & location, and powertrain details.*

**Results Display**
![Frontend - Results](./photos/frontend2.png)
*Real-time price predictions with formatted currency display, status indicator, and smooth reveal animation.*

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- PostgreSQL database (or Supabase)
- pip or Poetry

### Installation

```bash
# Clone repository
git clone <repo-url>
cd Japan_car_price_prediction_project

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# or: source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```dotenv
DATABASE_URL="postgresql://user:password@host:port/dbname"
# Example: postgresql://postgres:pass@localhost:5432/japan_cars
```

### Database Setup

```bash
# Create tables and load initial data
python scripts/load.py
```

### Running the Application

```bash
# Start FastAPI server with auto-reload
uvicorn apps.main:app --reload --host 0.0.0.0 --port 8000
```

Open browser to: **http://localhost:8000**

---

## 📁 Project Structure

```
Japan_car_price_prediction_project/
├── apps/
│   ├── main.py               # FastAPI application entry point
│   ├── routes.py             # API endpoints
│   ├── schemas.py            # Pydantic models for request/response
│   └── model_loader.py       # Model initialization
├── database/
│   ├── db_connection.py      # PostgreSQL connection
│   └── models.py             # SQLAlchemy ORM models
├── machine_learning/
│   └── machine_learning.py   # Training & inference functions
├── scripts/
│   ├── clean.py              # Data cleaning pipeline
│   ├── ingest.py             # Data ingestion
│   ├── load.py               # Load cleaned data to database
│   └── test_connection.py    # Database connectivity test
├── frontend/
│   └── index.html            # Production-ready web UI
├── models/
│   └── japan_cars_price_model.pkl  # Trained model artifact
├── photos/                   # Documentation images
├── book1.ipynb              # Exploratory analysis & model development
├── main_scraper.py          # Web scraper for vehicle listings
├── scheduler.py             # Weekly model retraining job
├── .env                      # Environment variables (git-ignored)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 🔌 API Endpoints

### Predict Price

**POST** `/api/v1/predict`

Request body:
```json
{
  "vehicle_age": 8.0,
  "doors_num": 4.0,
  "seats_num": 5.0,
  "market_country": "Japan",
  "stock_country": "Japan",
  "is_overseas_stock": false,
  "make_clean": "TOYOTA",
  "model_clean": "Corolla Fielder",
  "age_bucket": "6-10",
  "fuel_group": "Petrol",
  "transmission_group": "Automatic",
  "drive_group": "2WD",
  "steering_group": "Right",
  "vin_region": "Japan",
  "body_guess": "sedan_like"
}
```

Response:
```json
{
  "predicted_price": 8991.83,
  "predicted_price_log": 9.10,
  "status": "success"
}
```

---

## 📊 Data Pipeline

```
Raw Scrape (BeForward/SBT Japan)
    ↓
Initial Cleaning (cars.csv → df_clean.csv)
    ↓
Feature Engineering (engineer_features)
    ↓
Train/Test Split (80/20)
    ↓
Preprocessing Pipeline (StandardScaler, Encoders)
    ↓
Model Training (Gradient Boosting)
    ↓
Model Evaluation (Cross-validation, Test metrics)
    ↓
Model Persistence (joblib)
    ↓
API Deployment (FastAPI)
    ↓
Web UI Predictions (Frontend)
```

---

## 🔄 Automated Retraining

The application includes an **APScheduler** that automatically retrains the model every **Saturday at 12:00 PM** to keep predictions current with new market data.

```bash
# Scheduler runs automatically on app startup
# See: scheduler.py for configuration
```

---

## 🧪 Development

### Running Tests

```bash
# Test database connection
python scripts/test_connection.py

# Train model from scratch
python machine_learning/machine_learning.py
```

### Jupyter Notebook

Explore the full analysis in `book1.ipynb`:

```bash
jupyter notebook book1.ipynb
```

The notebook includes:
- Exploratory Data Analysis (EDA)
- Missing-value assessment
- Feature engineering deep-dive
- Model training loop
- Cross-validation results
- Feature importance analysis

---

## 📈 Key Insights

1. **Price Log-normalization** – Raw prices are highly skewed; log-transformation improves model fit
2. **Vehicle Age** – Strong negative correlation with price; captured via age buckets
3. **Make/Model** – High-cardinality categorical; OrdinalEncoder handles unknowns gracefully
4. **Geographic Factors** – Market country and stock location affect predicted value
5. **Fuel Type** – Electric/Hybrid vehicles command different premiums than traditional fuel

---

## ⚠️ Limitations

- **No model versioning** – Single production model (future: implement model registry)
- **Limited explainability** – Gradient Boosting lacks SHAP/LIME integration
- **Seasonal variation** – Model does not account for market seasonality
- **Geopolitical factors** – Exchange rates and tariffs not modeled
- **Data lag** – Web scraper updates are manual; automate with CI/CD

---

## 🔐 Security Considerations

- Database credentials stored in `.env` (never commit)
- API runs on localhost by default; add authentication for production
- Input validation via Pydantic; sanitize model names
- CORS not configured; enable if frontend is on separate domain

---

## 📦 Dependencies

See `requirements.txt` for full list. Key packages:

```
fastapi==0.104.1
sqlalchemy==2.0.23
pandas==2.1.4
scikit-learn==1.3.2
xgboost==2.0.3
numpy==1.24.3
psycopg2-binary==2.9.9
apscheduler==3.10.4
pydantic==2.5.1
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in FastAPI app
- [ ] Enable CORS for frontend domain
- [ ] Use environment variables for all secrets
- [ ] Configure proper logging
- [ ] Set up monitoring/alerting
- [ ] Add request rate limiting
- [ ] Enable HTTPS/TLS
- [ ] Configure database backups
- [ ] Set up CI/CD pipeline
- [ ] Add API documentation (auto-generated by FastAPI at `/docs`)

---

## 📝 License

This project is provided as-is for educational and commercial use.

---

## 👤 Author

Developed as an end-to-end machine learning engineering project demonstrating data pipeline automation, feature engineering, model evaluation, and API deployment.

---

## 📧 Support & Next Steps

### Future Enhancements

1. **Model Versioning** – MLflow or DVC for experiment tracking
2. **SHAP Explainability** – Feature importance for individual predictions
3. **Ensemble Stacking** – Combine models for better performance
4. **Real-time Updates** – Streaming data pipeline with Kafka
5. **Mobile App** – React Native frontend
6. **Price Clustering** – Identify vehicle market segments
7. **Anomaly Detection** – Flag unusual listings

For questions or issues, submit a GitHub issue or email the maintainer.

---

**Last Updated:** May 28, 2026  
**Status:** ✅ Production Ready (R² = 0.7653)

