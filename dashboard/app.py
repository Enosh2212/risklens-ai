"""Streamlit dashboard for RiskLens AI Credit Risk Decision Support."""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="RiskLens AI - Credit Risk Decision Support",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    .small-note {
        color: #5f6368;
        font-size: 0.92rem;
        margin-top: -0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "local_db" / "risklens_local.db"


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Return True when a SQLite table exists."""
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table_name,),
    ).fetchone()
    return result is not None


@st.cache_data(ttl=60)
def load_demo_data():
    """Load the existing synthetic loan dashboard tables safely."""
    if not DB_PATH.exists():
        return pd.DataFrame(), pd.DataFrame(), f"Database not found at: {DB_PATH}"

    try:
        with sqlite3.connect(DB_PATH) as conn:
            required_tables = [
                "loans",
                "borrowers",
                "loan_features",
                "predictions",
                "shap_explanations",
                "underwriter_reviews",
            ]
            missing = [table for table in required_tables if not table_exists(conn, table)]
            if missing:
                return pd.DataFrame(), pd.DataFrame(), f"Missing demo tables: {missing}"

            query = """
            SELECT
                l.loan_id,
                b.borrower_id,
                b.borrower_name,
                b.annual_income,
                b.employment_length,
                b.home_ownership,
                b.state_code,
                l.loan_amount,
                l.term_months,
                l.interest_rate,
                l.installment,
                l.loan_grade,
                l.loan_purpose,
                l.loan_status,
                lf.dti,
                lf.delinq_2yrs,
                lf.open_accounts,
                lf.total_accounts,
                lf.loan_to_income_ratio,
                lf.revolving_utilization,
                p.default_probability,
                p.risk_band,
                p.prediction_id,
                ur.reviewer_name,
                ur.review_decision,
                ur.review_notes,
                ur.reviewed_at
            FROM loans l
            JOIN borrowers b ON l.borrower_id = b.borrower_id
            JOIN loan_features lf ON l.loan_id = lf.loan_id
            JOIN predictions p ON l.loan_id = p.loan_id
            LEFT JOIN underwriter_reviews ur ON l.loan_id = ur.loan_id
            """
            df = pd.read_sql_query(query, conn)

            if "review_decision" in df.columns:
                if "review_status" not in df.columns:
                    df["review_status"] = df["review_decision"]
                if "final_decision" not in df.columns:
                    df["final_decision"] = df["review_decision"]

            shap_df = pd.read_sql_query("SELECT * FROM shap_explanations", conn)

        return df, shap_df, None
    except Exception as exc:
        return pd.DataFrame(), pd.DataFrame(), str(exc)


@st.cache_data(ttl=60)
def load_real_credit_data():
    """Load Phase 6 real UCI dashboard tables safely."""
    if not DB_PATH.exists():
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), f"Database not found at: {DB_PATH}"

    try:
        with sqlite3.connect(DB_PATH) as conn:
            required_tables = [
                "credit_default_features",
                "credit_default_predictions",
                "credit_default_explanations",
                "credit_default_model_metrics",
            ]
            missing = [table for table in required_tables if not table_exists(conn, table)]
            if missing:
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), f"Missing real dashboard tables: {missing}"

            query = """
            SELECT
                f.customer_id,
                f.limit_bal,
                f.sex,
                f.education,
                f.marriage,
                f.age,
                f.pay_0,
                f.pay_2,
                f.pay_3,
                f.pay_4,
                f.pay_5,
                f.pay_6,
                f.bill_amt1,
                f.bill_amt2,
                f.bill_amt3,
                f.bill_amt4,
                f.bill_amt5,
                f.bill_amt6,
                f.pay_amt1,
                f.pay_amt2,
                f.pay_amt3,
                f.pay_amt4,
                f.pay_amt5,
                f.pay_amt6,
                f.avg_bill_amount,
                f.avg_payment_amount,
                f.total_bill_amount,
                f.total_payment_amount,
                f.payment_to_bill_ratio,
                f.late_payment_count,
                f.credit_utilization_proxy,
                f.is_default AS actual_label,
                p.prediction_id,
                p.default_probability,
                p.risk_band,
                p.predicted_label,
                p.threshold_used,
                p.model_name,
                p.predicted_at
            FROM credit_default_features f
            JOIN credit_default_predictions p ON f.customer_id = p.customer_id
            """
            real_df = pd.read_sql_query(query, conn)
            explanations_df = pd.read_sql_query(
                "SELECT * FROM credit_default_explanations ORDER BY prediction_id, explanation_rank",
                conn,
            )
            metrics_df = pd.read_sql_query(
                "SELECT * FROM credit_default_model_metrics ORDER BY metric_id DESC",
                conn,
            )

        return real_df, explanations_df, metrics_df, None
    except Exception as exc:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), str(exc)


def format_percent(value, decimals: int = 2) -> str:
    """Format a nullable decimal as a percentage."""
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def render_demo_dashboard():
    """Render the original synthetic loan dashboard mode."""
    df, shap_df, db_error = load_demo_data()

    if db_error:
        st.error(f"Error connecting to database: {db_error}")
        return
    if df.empty:
        st.warning("No demo loan data found. Please run the local SQLite ETL pipeline.")
        return

    st.sidebar.title("Filters")
    st.sidebar.markdown("Filter loans in the queue and overview")

    risk_band_opts = sorted(df["risk_band"].dropna().unique().tolist())
    selected_risk_bands = st.sidebar.multiselect(
        "Risk Band",
        options=risk_band_opts,
        default=risk_band_opts,
    )

    grade_opts = sorted(df["loan_grade"].dropna().unique().tolist())
    selected_grades = st.sidebar.multiselect(
        "Loan Grade",
        options=grade_opts,
        default=grade_opts,
    )

    status_opts = sorted(df["loan_status"].dropna().unique().tolist())
    selected_statuses = st.sidebar.multiselect(
        "Loan Status",
        options=status_opts,
        default=status_opts,
    )

    review_col = "review_status" if "review_status" in df.columns else "review_decision"
    review_opts = sorted(df[review_col].dropna().unique().tolist())
    selected_reviews = st.sidebar.multiselect(
        "Review Status",
        options=review_opts,
        default=review_opts,
    )

    filtered_df = df[
        df["risk_band"].isin(selected_risk_bands)
        & df["loan_grade"].isin(selected_grades)
        & df["loan_status"].isin(selected_statuses)
        & df[review_col].isin(selected_reviews)
    ]

    st.title("RiskLens AI - Credit Risk Decision Support")
    st.markdown("Interactive credit risk intelligence and decisioning dashboard.")

    st.header("Executive Overview")
    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
    else:
        col1, col2, col3, col4, col5 = st.columns(5)

        total_loans = len(filtered_df)
        total_loan_amount = filtered_df["loan_amount"].sum()
        avg_default_prob = filtered_df["default_probability"].mean()
        high_risk_count = len(filtered_df[filtered_df["risk_band"] == "High"])
        potential_exposure = filtered_df[filtered_df["risk_band"] == "High"]["loan_amount"].sum()

        col1.metric("Total Loans", f"{total_loans}")
        col2.metric("Total Loan Amount", f"${total_loan_amount:,.2f}")
        col3.metric("Avg Default Prob", format_percent(avg_default_prob))
        col4.metric("High Risk Count", f"{high_risk_count}")
        col5.metric("Exposure Flagged", f"${potential_exposure:,.2f}")

    st.markdown("---")

    st.header("Risk Queue")
    if filtered_df.empty:
        st.warning("No records to display in Risk Queue.")
    else:
        queue_cols = [
            "loan_id",
            "annual_income",
            "loan_amount",
            "loan_grade",
            "loan_purpose",
            "dti",
            "loan_to_income_ratio",
            "default_probability",
            "risk_band",
            "loan_status",
            "review_status",
            "final_decision",
        ]
        display_cols = [col for col in queue_cols if col in filtered_df.columns]
        st.dataframe(filtered_df[display_cols], width="stretch", hide_index=True)

    st.markdown("---")

    st.header("Risk Segmentation")
    if filtered_df.empty:
        st.warning("No data available for charts.")
    else:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            fig_prob_grade = px.box(
                filtered_df,
                x="loan_grade",
                y="default_probability",
                color="loan_grade",
                title="Default Probability by Loan Grade",
                category_orders={"loan_grade": sorted(df["loan_grade"].dropna().unique().tolist())},
                labels={"loan_grade": "Loan Grade", "default_probability": "Default Probability"},
            )
            st.plotly_chart(fig_prob_grade, width="stretch")

            status_counts = filtered_df["loan_status"].value_counts().reset_index()
            status_counts.columns = ["Loan Status", "Count"]
            fig_status = px.pie(
                status_counts,
                values="Count",
                names="Loan Status",
                hole=0.4,
                title="Loan Status Distribution",
            )
            st.plotly_chart(fig_status, width="stretch")

        with chart_col2:
            fig_amt_band = px.bar(
                filtered_df,
                x="risk_band",
                y="loan_amount",
                color="risk_band",
                title="Total Loan Amount by Risk Band",
                category_orders={"risk_band": ["Low", "Medium", "High"]},
                labels={"risk_band": "Risk Band", "loan_amount": "Total Loan Amount ($)"},
            )
            st.plotly_chart(fig_amt_band, width="stretch")

            band_counts = filtered_df["risk_band"].value_counts().reset_index()
            band_counts.columns = ["Risk Band", "Count"]
            fig_band = px.pie(
                band_counts,
                values="Count",
                names="Risk Band",
                hole=0.4,
                title="Risk Band Distribution",
            )
            st.plotly_chart(fig_band, width="stretch")

    st.markdown("---")

    st.header("Applicant Detail")
    loan_ids = sorted(df["loan_id"].dropna().unique().tolist())
    selected_loan_id = st.selectbox("Select Loan ID", options=loan_ids)

    if selected_loan_id:
        applicant = df[df["loan_id"] == selected_loan_id].iloc[0]
        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.subheader("Borrower Details")
            st.write(f"**Borrower ID:** {applicant.get('borrower_id', 'N/A')}")
            st.write(f"**Name:** {applicant.get('borrower_name', 'N/A')}")
            st.write(f"**Annual Income:** ${applicant.get('annual_income', 0.0):,.2f}")
            st.write(f"**Employment Length:** {applicant.get('employment_length', 'N/A')} years")
            st.write(f"**Home Ownership:** {applicant.get('home_ownership', 'N/A')}")
            st.write(f"**State Code:** {applicant.get('state_code', 'N/A')}")

            st.subheader("Loan Details")
            st.write(f"**Loan Amount:** ${applicant.get('loan_amount', 0.0):,.2f}")
            st.write(f"**Term:** {applicant.get('term_months', 'N/A')} months")
            st.write(f"**Interest Rate:** {applicant.get('interest_rate', 0.0):.2f}%")
            st.write(f"**Installment:** ${applicant.get('installment', 0.0):,.2f}")
            st.write(f"**Grade:** {applicant.get('loan_grade', 'N/A')}")
            st.write(f"**Purpose:** {applicant.get('loan_purpose', 'N/A')}")
            st.write(f"**Status:** {applicant.get('loan_status', 'N/A')}")

        with detail_col2:
            st.subheader("Financial & Risk Features")
            st.write(f"**DTI:** {applicant.get('dti', 'N/A')}%")
            st.write(f"**Delinquencies (2Yrs):** {applicant.get('delinq_2yrs', 'N/A')}")
            st.write(f"**Open Accounts:** {applicant.get('open_accounts', 'N/A')}")
            st.write(f"**Total Accounts:** {applicant.get('total_accounts', 'N/A')}")
            st.write(f"**Loan-to-Income Ratio:** {applicant.get('loan_to_income_ratio', 'N/A')}")
            st.write(f"**Revolving Utilization:** {applicant.get('revolving_utilization', 'N/A')}%")

            st.subheader("Model Predictions & Underwriter Decisions")
            st.write(f"**Default Probability:** {format_percent(applicant.get('default_probability', 0.0))}")
            st.write(f"**Risk Band:** {applicant.get('risk_band', 'N/A')}")
            st.write(f"**Reviewer:** {applicant.get('reviewer_name', 'N/A')}")
            st.write(f"**Review Decision:** {applicant.get('review_decision', 'N/A')}")
            st.write(f"**Notes:** {applicant.get('review_notes', 'N/A')}")
            st.write(f"**Reviewed At:** {applicant.get('reviewed_at', 'N/A')}")

        st.subheader("Top SHAP Feature Explanations")
        if not shap_df.empty and "prediction_id" in applicant:
            app_shap = shap_df[
                shap_df["prediction_id"] == applicant["prediction_id"]
            ].sort_values("explanation_rank")
            if not app_shap.empty:
                display_cols = [
                    col
                    for col in ["feature_name", "feature_value", "shap_value", "explanation_rank"]
                    if col in app_shap.columns
                ]
                st.dataframe(app_shap[display_cols], width="stretch", hide_index=True)
            else:
                st.info("No SHAP explanations available for this prediction.")
        else:
            st.info("No SHAP explanations found.")

    st.markdown("---")

    st.header("Business Impact Simulator")
    threshold = st.slider(
        "Risk Threshold (Default Probability)",
        min_value=0.1,
        max_value=0.9,
        value=0.5,
        step=0.05,
        key="demo_threshold",
    )

    flagged_loans = df[df["default_probability"] >= threshold]
    num_flagged = len(flagged_loans)
    total_exp_flagged = flagged_loans["loan_amount"].sum()
    avg_prob_flagged = flagged_loans["default_probability"].mean() if num_flagged else 0.0

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    sim_col1.metric("Loans Flagged", f"{num_flagged} / {len(df)}")
    sim_col2.metric("Total Exposure Flagged", f"${total_exp_flagged:,.2f}")
    sim_col3.metric("Avg Default Prob", format_percent(avg_prob_flagged))


def render_real_dashboard():
    """Render the Phase 6 real UCI credit default dashboard mode."""
    df, explanations_df, metrics_df, db_error = load_real_credit_data()

    if db_error:
        st.error(f"Error loading real dashboard data: {db_error}")
        st.info("Run the Phase 5 training script to create the real model output tables.")
        return
    if df.empty:
        st.warning("No real UCI credit default predictions found.")
        st.info("Run: .\\.venv\\Scripts\\python.exe .\\src\\models\\train_real_credit_model.py")
        return

    st.title("Real UCI Credit Default Dashboard")
    st.markdown(
        '<p class="small-note">Dataset: UCI Default of Credit Card Clients, CC BY 4.0. '
        "Prototype only — not for real lending decisions.</p>",
        unsafe_allow_html=True,
    )

    st.sidebar.title("Real Dataset Filters")
    risk_band_order = ["Low", "Medium", "High"]
    available_bands = [band for band in risk_band_order if band in df["risk_band"].dropna().unique()]
    selected_bands = st.sidebar.multiselect(
        "Risk Band",
        options=available_bands,
        default=available_bands,
    )
    filtered_df = df[df["risk_band"].isin(selected_bands)] if selected_bands else df.iloc[0:0]

    st.header("Real Model Overview")
    latest_metrics = metrics_df.iloc[0] if not metrics_df.empty else pd.Series(dtype="object")
    total_customers = len(filtered_df)
    default_rate = filtered_df["actual_label"].mean() if total_customers else 0.0
    avg_probability = filtered_df["default_probability"].mean() if total_customers else 0.0
    high_risk_count = len(filtered_df[filtered_df["risk_band"] == "High"])

    overview_cols = st.columns(7)
    overview_cols[0].metric("Total Customers", f"{total_customers:,}")
    overview_cols[1].metric("Default Rate", format_percent(default_rate))
    overview_cols[2].metric("Avg Default Prob", format_percent(avg_probability))
    overview_cols[3].metric("High Risk Customers", f"{high_risk_count:,}")
    overview_cols[4].metric("Model ROC AUC", f"{latest_metrics.get('roc_auc', float('nan')):.3f}" if not metrics_df.empty else "N/A")
    overview_cols[5].metric("Model PR AUC", f"{latest_metrics.get('pr_auc', float('nan')):.3f}" if not metrics_df.empty else "N/A")
    overview_cols[6].metric("Model F1", f"{latest_metrics.get('f1_score', float('nan')):.3f}" if not metrics_df.empty else "N/A")

    st.markdown("---")

    st.header("Customer Risk Queue")
    queue_cols = [
        "customer_id",
        "limit_bal",
        "age",
        "pay_0",
        "late_payment_count",
        "payment_to_bill_ratio",
        "credit_utilization_proxy",
        "default_probability",
        "risk_band",
        "predicted_label",
        "actual_label",
    ]
    if filtered_df.empty:
        st.warning("No customers match the selected filters.")
    else:
        st.dataframe(
            filtered_df[queue_cols].sort_values("default_probability", ascending=False),
            width="stretch",
            hide_index=True,
        )

    st.markdown("---")

    st.header("Real Risk Segmentation Charts")
    if filtered_df.empty:
        st.warning("No data available for charts.")
    else:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            fig_prob_band = px.box(
                filtered_df,
                x="risk_band",
                y="default_probability",
                color="risk_band",
                title="Default Probability by Risk Band",
                category_orders={"risk_band": risk_band_order},
                labels={"risk_band": "Risk Band", "default_probability": "Default Probability"},
            )
            st.plotly_chart(fig_prob_band, width="stretch")

            actual_counts = filtered_df["actual_label"].map({0: "No Default", 1: "Default"}).value_counts().reset_index()
            actual_counts.columns = ["Actual Label", "Count"]
            fig_actual = px.pie(
                actual_counts,
                values="Count",
                names="Actual Label",
                hole=0.4,
                title="Actual Default Distribution",
            )
            st.plotly_chart(fig_actual, width="stretch")

            fig_util = px.scatter(
                filtered_df,
                x="credit_utilization_proxy",
                y="default_probability",
                color="risk_band",
                opacity=0.55,
                title="Credit Utilization Proxy vs Default Probability",
                labels={
                    "credit_utilization_proxy": "Credit Utilization Proxy",
                    "default_probability": "Default Probability",
                },
            )
            st.plotly_chart(fig_util, width="stretch")

        with chart_col2:
            band_counts = filtered_df["risk_band"].value_counts().reindex(risk_band_order).dropna().reset_index()
            band_counts.columns = ["Risk Band", "Count"]
            fig_band = px.pie(
                band_counts,
                values="Count",
                names="Risk Band",
                hole=0.4,
                title="Risk Band Distribution",
            )
            st.plotly_chart(fig_band, width="stretch")

            fig_late = px.strip(
                filtered_df,
                x="late_payment_count",
                y="default_probability",
                color="actual_label",
                title="Late Payment Count vs Default Probability",
                labels={
                    "late_payment_count": "Late Payment Count",
                    "default_probability": "Default Probability",
                    "actual_label": "Actual Label",
                },
            )
            st.plotly_chart(fig_late, width="stretch")

    st.markdown("---")

    st.header("Customer Detail")
    customer_ids = sorted(df["customer_id"].dropna().astype(int).unique().tolist())
    selected_customer_id = st.selectbox("Select Customer ID", options=customer_ids)
    customer = df[df["customer_id"] == selected_customer_id].iloc[0]

    detail_col1, detail_col2, detail_col3 = st.columns(3)
    with detail_col1:
        st.subheader("Customer Profile")
        st.write(f"**Customer ID:** {int(customer['customer_id'])}")
        st.write(f"**Credit Limit:** ${customer.get('limit_bal', 0):,.0f}")
        st.write(f"**Age:** {customer.get('age', 'N/A')}")
        st.write(f"**Sex Code:** {customer.get('sex', 'N/A')}")
        st.write(f"**Education Code:** {customer.get('education', 'N/A')}")
        st.write(f"**Marriage Code:** {customer.get('marriage', 'N/A')}")

    with detail_col2:
        st.subheader("Repayment Status")
        status_cols = ["pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"]
        for col in status_cols:
            st.write(f"**{col}:** {customer.get(col, 'N/A')}")
        st.write(f"**Late Payment Count:** {customer.get('late_payment_count', 'N/A')}")

    with detail_col3:
        st.subheader("Model Prediction")
        st.write(f"**Default Probability:** {format_percent(customer.get('default_probability', 0.0))}")
        st.write(f"**Risk Band:** {customer.get('risk_band', 'N/A')}")
        st.write(f"**Predicted Label:** {customer.get('predicted_label', 'N/A')}")
        st.write(f"**Actual Label:** {customer.get('actual_label', 'N/A')}")
        st.write(f"**Threshold Used:** {customer.get('threshold_used', 'N/A')}")
        st.write(f"**Model:** {customer.get('model_name', 'N/A')}")

    st.subheader("Billing and Payment Summary")
    summary_cols = [
        "avg_bill_amount",
        "avg_payment_amount",
        "total_bill_amount",
        "total_payment_amount",
        "payment_to_bill_ratio",
        "credit_utilization_proxy",
    ]
    st.dataframe(
        customer[summary_cols].to_frame(name="Value"),
        width="stretch",
    )

    st.subheader("Top 3 Explanations")
    if explanations_df.empty:
        st.info("No explanations found.")
    else:
        customer_explanations = explanations_df[
            explanations_df["prediction_id"] == customer["prediction_id"]
        ].sort_values("explanation_rank")
        explanation_cols = [
            "feature_name",
            "feature_value",
            "contribution_score",
            "impact_direction",
            "explanation_rank",
        ]
        if customer_explanations.empty:
            st.info("No explanations found for this customer.")
        else:
            st.dataframe(
                customer_explanations[explanation_cols].head(3),
                width="stretch",
                hide_index=True,
            )

    st.markdown("---")

    st.header("Threshold Simulator")
    threshold = st.slider(
        "Risk threshold",
        min_value=0.1,
        max_value=0.9,
        value=0.5,
        step=0.05,
        key="real_threshold",
    )

    predicted_positive = df["default_probability"] >= threshold
    actual_positive = df["actual_label"] == 1
    customers_flagged = int(predicted_positive.sum())
    flagged_percentage = customers_flagged / len(df) if len(df) else 0.0
    true_positives = int((predicted_positive & actual_positive).sum())
    false_positives = int((predicted_positive & ~actual_positive).sum())
    false_negatives = int((~predicted_positive & actual_positive).sum())
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0.0

    sim_cols = st.columns(7)
    sim_cols[0].metric("Customers Flagged", f"{customers_flagged:,}")
    sim_cols[1].metric("Flagged %", format_percent(flagged_percentage))
    sim_cols[2].metric("True Positives", f"{true_positives:,}")
    sim_cols[3].metric("False Positives", f"{false_positives:,}")
    sim_cols[4].metric("False Negatives", f"{false_negatives:,}")
    sim_cols[5].metric("Precision", format_percent(precision))
    sim_cols[6].metric("Recall", format_percent(recall))


st.sidebar.title("RiskLens AI")
dashboard_mode = st.sidebar.radio(
    "Dashboard Mode",
    options=["Demo Loan Dashboard", "Real UCI Credit Default Dashboard"],
)
st.sidebar.caption(f"SQLite database: {DB_PATH}")

if dashboard_mode == "Demo Loan Dashboard":
    render_demo_dashboard()
else:
    render_real_dashboard()
