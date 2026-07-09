# RiskLens AI

RiskLens AI is a local-first credit risk analytics project for explainable loan and credit default prediction. It combines a synthetic demo loan workflow with a real UCI credit card default dataset mode, model training pipelines, SQLite-backed outputs, and a Streamlit dashboard for portfolio-ready risk analysis.

This project is for education and prototyping only. It is not intended for real lending, underwriting, credit approval, or adverse-action decisions.

## Features

- Local SQLite development database at `data/local_db/risklens_local.db`
- Synthetic demo loan dashboard with borrower, loan, risk queue, review, and explanation views
- Real UCI credit default dashboard with customer-level predictions and explanations
- Real model training using `credit_default_features`
- Logistic Regression and Random Forest model comparison
- Model metrics stored in SQLite for dashboard display
- Threshold simulator for precision, recall, false positives, and false negatives
- Simple model-agnostic top-driver explanations for real dataset predictions

## Architecture

```text
data/raw/                         Raw UCI dataset file, ignored by git
data/local_db/risklens_local.db    Local SQLite database, ignored by git
src/etl/                           SQLite setup and real dataset loading scripts
src/models/                        Model training scripts
dashboard/app.py                   Streamlit dashboard with demo and real modes
models/                            Trained joblib model artifacts, ignored by git
docs/screenshots/                  Placeholder for dashboard screenshots
```

The app currently uses the local SQLite path for development. Azure SQL schema work has been prepared, but the local Azure SQL authentication/driver issue is intentionally parked so development can continue safely without changing Azure resources.

## Setup

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create the local SQLite demo database and sample records:

```powershell
.\.venv\Scripts\python.exe .\src\etl\local_sqlite_setup.py
.\.venv\Scripts\python.exe .\src\etl\insert_sample_data.py
.\.venv\Scripts\python.exe .\src\etl\test_sqlite_connection.py
```

## Load Real Dataset

Place the UCI Excel file locally at:

```text
data/raw/default of credit card clients.xls
```

Then load and transform it into SQLite:

```powershell
.\.venv\Scripts\python.exe .\src\etl\load_real_dataset.py
```

This creates or replaces:

- `credit_default_raw`
- `credit_default_features`

Raw dataset files are intentionally ignored by git.

## Train Model

Train the real UCI credit default model:

```powershell
.\.venv\Scripts\python.exe .\src\models\train_real_credit_model.py
```

This trains and compares:

- `LogisticRegression` with `class_weight="balanced"`
- `RandomForestClassifier` with `class_weight="balanced"`

The best model is selected by ROC AUC, with F1 as a fallback, and saved to:

```text
models/risklens_uci_credit_default_model.joblib
```

It also creates or replaces the Phase 5 real model output tables:

- `credit_default_predictions`
- `credit_default_explanations`
- `credit_default_model_metrics`

## Run Dashboard

Start Streamlit:

```powershell
.\.venv\Scripts\streamlit.exe run .\dashboard\app.py
```

The dashboard sidebar includes two modes:

- `Demo Loan Dashboard`
- `Real UCI Credit Default Dashboard`

## Model Performance Summary

Latest local Phase 5 run on the UCI feature table:

| Metric | Value |
| --- | ---: |
| Selected model | RandomForestClassifier |
| Train rows | 24,000 |
| Test rows | 6,000 |
| Accuracy | 0.7935 |
| ROC AUC | 0.7625 |
| PR AUC | 0.5306 |
| Precision | 0.5363 |
| Recall | 0.4898 |
| F1 Score | 0.5120 |
| False positives | 562 |
| False negatives | 677 |

## Dataset Citation

Yeh, I. (2009). Default of Credit Card Clients [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C55S3H

Dataset: UCI Default of Credit Card Clients, CC BY 4.0.

## Security And Data Notes

- Do not commit `.env`.
- Do not commit raw datasets from `data/raw/`.
- Do not commit local SQLite databases from `data/local_db/`.
- Do not commit trained model artifacts from `models/`.
- Do not upload data or model artifacts unless a future project phase explicitly requires it.

## Disclaimer

RiskLens AI is a prototype for learning, portfolio demonstration, and analytics experimentation. It should not be used for real credit decisions, lending decisions, underwriting, compliance decisions, or consumer-impacting automation.
