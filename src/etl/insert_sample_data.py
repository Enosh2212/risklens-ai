import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "local_db" / "risklens_local.db"


SAMPLE_ROWS = [
    ("Aarav Sharma", 95000, 8, "MORTGAGE", "CA", 18000, 36, 8.4, 567.1, "B", "debt_consolidation", 14.2, 0, 9, 24, 0.19, 41.5, "Fully Paid"),
    ("Maya Patel", 62000, 5, "RENT", "NY", 12000, 36, 11.8, 397.5, "C", "credit_card", 22.9, 1, 7, 18, 0.19, 68.2, "Current"),
    ("Noah Williams", 42000, 2, "RENT", "TX", 16000, 60, 19.7, 421.1, "E", "small_business", 31.4, 2, 6, 12, 0.38, 86.4, "Charged Off"),
    ("Sophia Chen", 130000, 10, "MORTGAGE", "WA", 25000, 36, 7.2, 774.0, "A", "home_improvement", 10.1, 0, 14, 33, 0.19, 28.0, "Fully Paid"),
    ("Liam Brown", 54000, 3, "RENT", "FL", 14000, 36, 15.5, 488.6, "D", "medical", 27.5, 1, 8, 19, 0.26, 72.9, "Late"),
    ("Emma Johnson", 78000, 6, "OWN", "IL", 10000, 36, 9.6, 320.8, "B", "car", 13.8, 0, 10, 22, 0.13, 36.7, "Current"),
    ("Ethan Miller", 36000, 1, "RENT", "AZ", 15000, 60, 21.3, 405.9, "F", "debt_consolidation", 34.2, 3, 5, 11, 0.42, 93.1, "Charged Off"),
    ("Olivia Davis", 88000, 7, "MORTGAGE", "CO", 20000, 36, 10.2, 647.0, "B", "major_purchase", 16.6, 0, 12, 27, 0.23, 44.0, "Fully Paid"),
    ("Kabir Singh", 58000, 4, "RENT", "NJ", 9000, 36, 13.9, 307.3, "C", "vacation", 24.4, 1, 6, 16, 0.16, 62.3, "Late"),
    ("Ava Martinez", 112000, 9, "MORTGAGE", "VA", 30000, 60, 12.1, 667.3, "C", "debt_consolidation", 18.2, 0, 15, 31, 0.27, 49.8, "Current"),
    ("Lucas Garcia", 47000, 2, "RENT", "NV", 13000, 36, 18.4, 472.9, "E", "credit_card", 30.7, 2, 7, 13, 0.28, 84.2, "Charged Off"),
    ("Isabella Wilson", 72000, 5, "OWN", "OR", 11000, 36, 8.9, 349.2, "B", "moving", 15.9, 0, 11, 21, 0.15, 39.4, "Fully Paid"),
    ("Mason Anderson", 68000, 6, "RENT", "GA", 17000, 60, 16.2, 414.8, "D", "home_improvement", 26.1, 1, 9, 20, 0.25, 76.0, "Late"),
    ("Mia Thomas", 99000, 8, "MORTGAGE", "MA", 22000, 36, 9.1, 700.8, "B", "credit_card", 12.5, 0, 13, 29, 0.22, 33.1, "Current"),
    ("James Lee", 39000, 1, "RENT", "OH", 10000, 36, 23.4, 389.1, "G", "medical", 36.9, 4, 4, 10, 0.26, 97.5, "Charged Off"),
    ("Charlotte Kim", 85000, 7, "OWN", "NC", 16000, 36, 10.7, 521.8, "C", "car", 17.1, 0, 10, 26, 0.19, 46.6, "Fully Paid"),
    ("Benjamin Clark", 61000, 3, "RENT", "PA", 12500, 60, 14.8, 296.3, "D", "debt_consolidation", 25.3, 1, 8, 17, 0.20, 70.1, "Current"),
    ("Amelia Lewis", 145000, 10, "MORTGAGE", "CA", 35000, 60, 8.1, 712.0, "A", "home_improvement", 9.4, 0, 18, 40, 0.24, 21.9, "Fully Paid"),
    ("Henry Walker", 52000, 2, "RENT", "MI", 15500, 60, 20.2, 412.5, "F", "small_business", 33.8, 3, 5, 14, 0.30, 90.2, "Charged Off"),
    ("Harper Young", 76000, 5, "RENT", "TN", 9500, 36, 12.6, 318.4, "C", "major_purchase", 19.6, 0, 9, 23, 0.13, 55.4, "Current"),
]


def risk_band(probability):
    if probability >= 0.70:
        return "High"
    if probability >= 0.40:
        return "Medium"
    return "Low"


def estimate_default_probability(status, dti, delinq_2yrs, revolving_utilization, loan_grade):
    grade_risk = {"A": 0.08, "B": 0.14, "C": 0.22, "D": 0.35, "E": 0.52, "F": 0.68, "G": 0.78}
    probability = grade_risk.get(loan_grade, 0.30)
    probability += min(dti / 100, 0.25)
    probability += min(delinq_2yrs * 0.06, 0.18)
    probability += min(revolving_utilization / 250, 0.35)
    if status == "Charged Off":
        probability = max(probability, 0.82)
    elif status == "Late":
        probability = max(probability, 0.58)
    elif status == "Fully Paid":
        probability = min(probability, 0.28)
    return round(min(probability, 0.98), 4)


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"SQLite database not found at {DB_PATH}. Run local_sqlite_setup.py first.")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        for table in [
            "shap_explanations",
            "predictions",
            "underwriter_reviews",
            "loan_features",
            "loans",
            "borrowers",
            "model_metrics",
        ]:
            conn.execute(f"DELETE FROM {table};")

        for idx, row in enumerate(SAMPLE_ROWS, start=1):
            (
                name,
                annual_income,
                employment_length,
                home_ownership,
                state_code,
                loan_amount,
                term_months,
                interest_rate,
                installment,
                loan_grade,
                loan_purpose,
                dti,
                delinq_2yrs,
                open_accounts,
                total_accounts,
                loan_to_income_ratio,
                revolving_utilization,
                loan_status,
            ) = row

            is_default = 1 if loan_status == "Charged Off" else 0
            probability = estimate_default_probability(
                loan_status, dti, delinq_2yrs, revolving_utilization, loan_grade
            )

            conn.execute(
                """
                INSERT INTO borrowers (
                    borrower_id, borrower_name, annual_income, employment_length,
                    home_ownership, state_code
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (idx, name, annual_income, employment_length, home_ownership, state_code),
            )
            conn.execute(
                """
                INSERT INTO loans (
                    loan_id, borrower_id, loan_amount, term_months, interest_rate,
                    installment, loan_grade, loan_purpose, loan_status, is_default
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    idx,
                    idx,
                    loan_amount,
                    term_months,
                    interest_rate,
                    installment,
                    loan_grade,
                    loan_purpose,
                    loan_status,
                    is_default,
                ),
            )
            conn.execute(
                """
                INSERT INTO loan_features (
                    feature_id, loan_id, dti, delinq_2yrs, open_accounts,
                    total_accounts, loan_to_income_ratio, revolving_utilization
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    idx,
                    idx,
                    dti,
                    delinq_2yrs,
                    open_accounts,
                    total_accounts,
                    loan_to_income_ratio,
                    revolving_utilization,
                ),
            )
            conn.execute(
                """
                INSERT INTO predictions (
                    prediction_id, loan_id, default_probability, risk_band, model_version
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (idx, idx, probability, risk_band(probability), "local_sample_v1"),
            )
            shap_rows = [
                ("loan_grade", loan_grade, probability * 0.22, 1),
                ("dti", dti, dti / 200, 2),
                ("revolving_utilization", revolving_utilization, revolving_utilization / 300, 3),
            ]
            for rank_idx, (feature, value, shap_value, rank) in enumerate(shap_rows, start=1):
                explanation_id = ((idx - 1) * 3) + rank_idx
                conn.execute(
                    """
                    INSERT INTO shap_explanations (
                        explanation_id, prediction_id, feature_name, feature_value,
                        shap_value, explanation_rank
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (explanation_id, idx, feature, str(value), round(shap_value, 4), rank),
                )
            conn.execute(
                """
                INSERT INTO underwriter_reviews (
                    review_id, loan_id, reviewer_name, review_decision, review_notes
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    idx,
                    idx,
                    "Local Analyst",
                    "Manual Review" if probability >= 0.40 else "Approve",
                    f"Sample review for {risk_band(probability).lower()} risk loan.",
                ),
            )

        metrics = [
            ("local_sample_v1", "sample_size", 20),
            ("local_sample_v1", "default_rate", 5 / 20),
            ("local_sample_v1", "mean_default_probability", 0.4935),
        ]
        conn.executemany(
            """
            INSERT INTO model_metrics (model_version, metric_name, metric_value)
            VALUES (?, ?, ?);
            """,
            metrics,
        )
        conn.commit()

    print(f"Inserted {len(SAMPLE_ROWS)} sample borrowers, loans, features, predictions, explanations, and reviews.")
    print(f"SQLite database: {DB_PATH}")


if __name__ == "__main__":
    main()
