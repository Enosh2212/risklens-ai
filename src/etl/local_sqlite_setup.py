import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = PROJECT_ROOT / "data" / "local_db"
DB_PATH = DB_DIR / "risklens_local.db"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS borrowers (
    borrower_id INTEGER PRIMARY KEY,
    borrower_name TEXT NOT NULL,
    annual_income REAL NOT NULL,
    employment_length INTEGER NOT NULL,
    home_ownership TEXT NOT NULL,
    state_code TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id INTEGER PRIMARY KEY,
    borrower_id INTEGER NOT NULL,
    loan_amount REAL NOT NULL,
    term_months INTEGER NOT NULL,
    interest_rate REAL NOT NULL,
    installment REAL NOT NULL,
    loan_grade TEXT NOT NULL,
    loan_purpose TEXT NOT NULL,
    loan_status TEXT NOT NULL,
    is_default INTEGER NOT NULL CHECK (is_default IN (0, 1)),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrower_id) REFERENCES borrowers (borrower_id)
);

CREATE TABLE IF NOT EXISTS loan_features (
    feature_id INTEGER PRIMARY KEY,
    loan_id INTEGER NOT NULL,
    dti REAL NOT NULL,
    delinq_2yrs INTEGER NOT NULL,
    open_accounts INTEGER NOT NULL,
    total_accounts INTEGER NOT NULL,
    loan_to_income_ratio REAL NOT NULL,
    revolving_utilization REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans (loan_id)
);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INTEGER PRIMARY KEY,
    loan_id INTEGER NOT NULL,
    default_probability REAL NOT NULL,
    risk_band TEXT NOT NULL,
    model_version TEXT NOT NULL,
    predicted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans (loan_id)
);

CREATE TABLE IF NOT EXISTS shap_explanations (
    explanation_id INTEGER PRIMARY KEY,
    prediction_id INTEGER NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value TEXT,
    shap_value REAL NOT NULL,
    explanation_rank INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions (prediction_id)
);

CREATE TABLE IF NOT EXISTS underwriter_reviews (
    review_id INTEGER PRIMARY KEY,
    loan_id INTEGER NOT NULL,
    reviewer_name TEXT NOT NULL,
    review_decision TEXT NOT NULL,
    review_notes TEXT,
    reviewed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans (loan_id)
);

CREATE TABLE IF NOT EXISTS model_metrics (
    metric_id INTEGER PRIMARY KEY,
    model_version TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    evaluated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_SQL)
        tables = [
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
                """
            )
        ]

    print(f"SQLite database created: {DB_PATH}")
    print("Tables created/verified:")
    for table in tables:
        print(f"- {table}")


if __name__ == "__main__":
    main()
