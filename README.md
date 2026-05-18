# Japan Car Price Prediction Project

Project overview

This repository contains code and notebooks for collecting, cleaning, feature-engineering, and modeling used-car listings (primarily from Japanese exporters). The project includes: a production-ready scraper (`main.py`) that extracts vehicle-detail pages into a CSV dataset, an analysis/feature-engineering Jupyter notebook (`book1.ipynb`) that builds an engineered dataset and trains a range of regression models, and several CSV artifacts produced during processing.

Motivation

Estimate market prices for used vehicles exported from Japan by combining web-scraped listings with systematic feature engineering. The codebase demonstrates an end-to-end workflow: scrape, clean, engineer features, build baseline models, and evaluate performance.

Features

- Robust site scraper for two exporters (BeForward and SBT Japan) implemented in `main.py`.
- Parsers for common vehicle attributes (price, year, mileage, engine displacement, stock/chassis identifiers).
- Feature engineering routine implemented in `book1.ipynb` that:
  - normalizes make/model, price, fuel, transmission, drive, steering
  - derives vehicle_age and age buckets
  - computes price buckets and log-price
  - infers stock/chassis characteristics (VIN detection, region)
  - derives a body-style proxy (`body_guess`) using heuristics and keyword lists
  - computes completeness/quality score and within-make/model price ranks
- Modeling pipeline that preprocesses numeric and categorical features and evaluates multiple regressors with K-fold cross validation.

Data pipeline (high-level)

1. Scraping (`main.py`)
   - `main.py` contains a configurable scraper for two sites: `beforward` and `sbtjapan`.
   - Default output file name in the script is `cars_dataset.csv` (argument `--output`).
   - The scraper extracts a fixed field set (see FIELDNAMES in `main.py`) and writes rows as CSV.

2. Intermediate cleaning
   - The notebook `book1.ipynb` reads `cars.csv` and writes `df_clean.csv` after initial cleaning.

3. Feature engineering
   - The notebook contains `engineer_features(csv_path)` which reads a CSV (used with `df_clean.csv`) and produces engineered outputs `beforward_engineered.csv` and `beforward_engineered_listings_only.csv`.

4. Modeling
   - The notebook builds preprocessing (ColumnTransformer) and evaluates multiple models using scikit-learn cross-validation and a held-out test split.

Feature engineering (details)

The function `engineer_features` (in `book1.ipynb`) implements the main transformations. Key points:

- Column dropping: `mileage_km`, `engine_cc`, `trim`, `body_type`, `scraped_at_utc`, `source` are removed early (configurable in DROP_COLS).
- URL-derived fields: `page_type`, `is_listing`, `market_country`, `url_make`, `url_model`, `make_clean`, `model_clean`.
- Numeric conversions: `price_value`, `year_clean`, `doors_num`, `seats_num`, `stock_seq`.
- Derived variables: `price_log`, `price_bucket` (bins provided in code), `vehicle_age`, `age_bucket`.
- Categorical normalization: `fuel_group`, `transmission_group`, `drive_group`, `steering_group`.
- Chassis/VIN handling: `chassis_no_clean`, `is_vin`, `vin_region`, `frame_no_type`.
- Body-style heuristic: `body_guess` using keyword lists and simple rules.
- Data quality metric: `completeness_score` based on presence of several important fields.
- Price rank features: percentile rank within make/model and within make/model/year.

Models and evaluation

Models evaluated (from the notebook):

- Linear Regression
- Ridge, Lasso, ElasticNet
- Decision Tree Regressor
- Random Forest Regressor
- Gradient Boosting Regressor (sklearn)
- AdaBoost Regressor
- XGBoost (XGBRegressor)
- Support Vector Regressor (SVR)
- K-Nearest Neighbors Regressor

Preprocessing pipeline

- Numeric columns: median imputation + StandardScaler.
- High-cardinality categorical columns (`model_clean`, `make_clean`): converted to string, imputed (most-frequent), encoded with `OrdinalEncoder` (unknowns encoded as -1).
- Low-cardinality categorical columns: imputed (most-frequent) then `OneHotEncoder` (drop='first', handle unknowns).
- ColumnTransformer assembles these pipelines and is used inside scikit-learn Pipelines with each model.

Evaluation metrics computed

- Cross-validated metrics (KFold, n_splits=5): R², MAE, RMSE (derived from neg MSE), with mean and std reported.
- Held-out test set metrics: MAE, MSE, RMSE, MAPE, R².

Project structure (observed)

- main.py — web scraper for beforward.jp and sbtjapan.com (requests + BeautifulSoup)
- book1.ipynb — exploratory notebook implementing EDA, feature engineering and model evaluation
- cars.csv — raw CSV (present in repo)
- df_clean.csv — intermediate cleaned CSV produced by the notebook
- beforward_engineered.csv — full engineered dataset (saved by notebook)
- beforward_engineered_listings_only.csv — subset containing rows classified as listings
- past_csv/ — directory with historical artifacts; contains `cars_dataset.csv` in the workspace
- .venv/ — local virtual environment directory (present but not committed)

Installation

The repository does not contain a pinned dependency file. The code requires Python 3.8+ (not explicitly pinned) and the following packages (inferred from the code):

- requests
- beautifulsoup4
- urllib3
- pandas
- numpy
- seaborn
- matplotlib
- scikit-learn
- imbalanced-learn (imblearn)
- xgboost

Install into a virtual environment (PowerShell example):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install requests beautifulsoup4 urllib3 pandas numpy seaborn matplotlib scikit-learn imbalanced-learn xgboost
```

Note: package versions are not specified in the repository. If reproducible results are required, pin versions after a successful run.

Usage

1. Scraping (produce raw CSV)

Run the scraper to collect vehicle detail pages into a CSV. Example (PowerShell):

```powershell
# create/activate virtual environment first (see Installation)
python .\main.py --site beforward --max-cars 0 --delay 1.5 --output cars_dataset.csv
```

Key arguments:
- `--site`: `beforward`, `sbtjapan` or `all` (default `all`).
- `--max-cars`: maximum rows to save per site (0 = no limit).
- `--delay`: seconds to wait between requests.
- `--output`: output CSV filename (default `cars_dataset.csv`).
- `--overwrite`: delete existing output file before starting.

The scraper writes rows with the fields defined in `FIELDNAMES` (see `main.py`).

2. Feature engineering and modeling (notebook)

Open `book1.ipynb` in JupyterLab / Jupyter Notebook and run cells sequentially. The notebook expects a CSV named `cars.csv` (or you can adapt the file path in the first cells). The notebook performs:

- EDA and missing-value inspection
- Writes `df_clean.csv` (intermediate cleaned data)
- Runs `engineer_features('df_clean.csv')` to produce `beforward_engineered.csv` and `beforward_engineered_listings_only.csv`
- Builds preprocessing and evaluates the models listed above

Reproducing the notebook programmatically

If you prefer a script-based run, call the same functions used in the notebook (for example, import `engineer_features` from a converted python module or run the notebook with nbconvert). The repository currently contains the implementation inside the notebook rather than as an importable module.

Results (from the notebook)

- The notebook contains a comment indicating the best-performing model was XGBoost with a reported CV R² mean ≈ 0.5757 and Test R² ≈ 0.6396 and Test RMSE ≈ 9129.59. These numbers appear as notebook commentary and should be treated as provisional results produced by the notebook run included in the repository.

Explicit uncertainties and assumptions

- Package versions are not available in the repository; therefore environment reproducibility is not guaranteed. The code appears compatible with Python 3.8+ but this is not asserted inside the project.
- The exact provenance of `cars.csv` is not recorded in the code. The scraper (`main.py`) can generate a CSV with similar fields, but the repository contains pre-existing CSV artifacts whose source (date/seed) is not encoded in the files here.
- The notebook contains in-line parameters (e.g., REF_YEAR = 2026, price buckets, feature selections). These were chosen by the notebook author and are reflected verbatim in the code; if you need different choices, modify the notebook.
- The notebook performs model training and evaluation in-memory and does not persist trained model objects (no serialized model files found). If you need deployment-ready artifacts, add model export (joblib / pickle) after training.

Limitations (observed from code)

- No explicit dependency management (no requirements.txt or pinned versions).
- The scraper does not include an explicit robots.txt acceptance or throttling beyond the `--delay` parameter. It implements retries, but responsible scraping requires confirming terms of service and adding rate limits / caching.
- The notebook mixes EDA, feature engineering and modeling in one monolithic notebook rather than modular, importable Python modules, which reduces reusability for production pipelines.
- No unit tests or CI configuration are present.
- No model persistence or reproducible experiment tracking was implemented.

Future work (practical next steps)

- Extract core functions from `book1.ipynb` into importable modules (e.g., `scraper/`, `ingest/`, `features/`, `models/`) to make automated runs and testing easier.
- Add a `requirements.txt` or `pyproject.toml` with pinned package versions and a small `Makefile` or `invoke` tasks to reproduce experiments.
- Persist trained models and preprocessing pipelines (joblib) and add a small inference script and tests.
- Add lightweight data validation (e.g., `pandas_schema` or `great_expectations`) to assert schema assumptions on scraped data.
- Add experiment tracking (MLflow or similar) and reproducible notebook execution (papermill / nbconvert) for production evaluation.

Contact / next steps

If you want, I can:

- generate a pinned `requirements.txt` by running the code and recording working versions, or
- extract core functions from the notebook into a small Python package and add a reproducible runner, or
- add model persistence and an inference script.

Tell me which of these (or other) tasks you want next and I will implement it.

