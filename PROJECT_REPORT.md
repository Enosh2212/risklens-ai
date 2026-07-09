# RiskLens AI Project Report

## Problem Statement

Credit risk teams need fast, explainable ways to identify borrowers or customers with elevated probability of default. RiskLens AI explores this workflow as a local-first prototype: load credit data, train a classification model, generate prediction outputs, explain top risk drivers, and present results in an interactive dashboard.

The project is designed for education and portfolio demonstration, not production credit decisioning.

## Dataset

The real dataset mode uses the UCI Default of Credit Card Clients dataset from Yeh (2009). The dataset contains credit card customer attributes, repayment status history, bill amounts, payment amounts, and a target indicating default payment next month.

The ETL pipeline loads the Excel dataset into local SQLite tables:

- `credit_default_raw`
- `credit_default_features`

The feature table includes original fields such as credit limit, age, repayment status, bill amounts, and payment amounts, plus derived features such as average bill amount, total payment amount, payment-to-bill ratio, late payment count, and a credit utilization proxy.

## Methodology

The model training pipeline reads from `credit_default_features` and predicts `is_default`.

Features used:

- Customer profile fields: `limit_bal`, `sex`, `education`, `marriage`, `age`
- Repayment status fields: `pay_0`, `pay_2`, `pay_3`, `pay_4`, `pay_5`, `pay_6`
- Billing and payment fields: `bill_amt1` through `bill_amt6`, `pay_amt1` through `pay_amt6`
- Derived risk features: `avg_bill_amount`, `avg_payment_amount`, `total_bill_amount`, `total_payment_amount`, `payment_to_bill_ratio`, `late_payment_count`, `credit_utilization_proxy`

The training script uses an 80/20 stratified train-test split with `random_state=42`. It compares:

- Logistic Regression with median imputation, standard scaling, and balanced class weights
- Random Forest with median imputation and balanced class weights

The best model is selected by ROC AUC, with F1 score as a fallback if ROC AUC is unavailable.

## Model Results

Latest local run:

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

The selected model is saved locally as `models/risklens_uci_credit_default_model.joblib`. Predictions, explanations, and model metrics are stored in SQLite tables:

- `credit_default_predictions`
- `credit_default_explanations`
- `credit_default_model_metrics`

## Dashboard Features

The Streamlit dashboard supports two sidebar modes:

- `Demo Loan Dashboard`
- `Real UCI Credit Default Dashboard`

The demo mode preserves the original synthetic borrower and loan dashboard. The real UCI mode adds:

- Real model overview KPIs
- Customer risk queue
- Risk segmentation charts
- Customer detail page
- Top 3 explanation drivers per prediction
- Threshold simulator

The real dashboard joins `credit_default_features` and `credit_default_predictions` by `customer_id`, then uses `credit_default_explanations` and `credit_default_model_metrics` for explainability and model performance sections.

## Business Impact Simulator

The threshold simulator lets users adjust the risk threshold from 0.1 to 0.9 and immediately review:

- Customers flagged
- Flagged percentage
- True positives
- False positives
- False negatives
- Precision at threshold
- Recall at threshold

This helps demonstrate the operational tradeoff between catching more defaults and increasing manual review volume or false-positive burden.

## Limitations

- The project is a prototype and is not suitable for production lending decisions.
- Explanations are simple model-agnostic driver rankings, not full SHAP values for the real model.
- The dataset is historical and may not represent current borrowers, products, geographies, or macroeconomic conditions.
- Fairness, bias, drift, calibration, adverse-action compliance, and governance workflows are not production-grade.
- Azure SQL schema work is prepared, but local Azure SQL authentication/driver issues are parked; the current development workflow uses SQLite.

## Future Improvements

- Add calibrated probability outputs and threshold selection guidance.
- Add stronger explainability with SHAP or permutation-based explanations for the trained real model.
- Add fairness and subgroup performance analysis.
- Add model monitoring, drift checks, and retraining reports.
- Add screenshot assets under `docs/screenshots/`.
- Revisit Azure SQL connectivity once the local authentication/driver issue is resolved.
- Add automated tests for ETL, training, and dashboard data loading.
