"""ETL script to load the real UCI Default of Credit Card Clients dataset into SQLite."""

import sqlite3
import os
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Path Resolutions using pathlib
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "local_db" / "risklens_local.db"
XLS_PATH = PROJECT_ROOT / "data" / "raw" / "default of credit card clients.xls"

def clean_column_names(df):
    """Normalize column names to lowercase, stripped, with underscores."""
    cleaned_cols = []
    for col in df.columns:
        col_str = str(col).strip().lower()
        col_str = col_str.replace(" ", "_").replace(".", "_")
        cleaned_cols.append(col_str)
    df.columns = cleaned_cols
    return df

def detect_and_rename_target(df):
    """Identify the target column and rename it to is_default."""
    target_candidates = ['default_payment_next_month', 'default_payment_next_month_']
    detected = None
    for candidate in target_candidates:
        if candidate in df.columns:
            detected = candidate
            break
            
    # Fallback search if exact match fails
    if not detected:
        for col in df.columns:
            if "default" in col or col == "y":
                detected = col
                break
                
    if detected:
        df = df.rename(columns={detected: "is_default"})
        print(f"Target column detected and renamed: {detected} -> is_default")
    else:
        print("Warning: Could not automatically detect target column. 'is_default' will not be set.")
    return df, detected

def process_features(df):
    """Create credit_default_features dataset with derived columns."""
    # Ensure ID/id is customer_id
    if "id" in df.columns:
        df = df.rename(columns={"id": "customer_id"})
    elif "unnamed:_0" in df.columns:
        df = df.rename(columns={"unnamed:_0": "customer_id"})
        
    bill_cols = [f"bill_amt{i}" for i in range(1, 7)]
    pay_cols = [f"pay_amt{i}" for i in range(1, 7)]
    status_cols = ["pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"]
    
    # Verify these columns exist in the dataframe
    existing_bill_cols = [c for c in bill_cols if c in df.columns]
    existing_pay_cols = [c for c in pay_cols if c in df.columns]
    existing_status_cols = [c for c in status_cols if c in df.columns]

    print("Generating derived features...")
    
    # 1. avg_bill_amount & avg_payment_amount
    df["avg_bill_amount"] = df[existing_bill_cols].mean(axis=1) if existing_bill_cols else 0.0
    df["avg_payment_amount"] = df[existing_pay_cols].mean(axis=1) if existing_pay_cols else 0.0
    
    # 2. total_bill_amount & total_payment_amount
    df["total_bill_amount"] = df[existing_bill_cols].sum(axis=1) if existing_bill_cols else 0.0
    df["total_payment_amount"] = df[existing_pay_cols].sum(axis=1) if existing_pay_cols else 0.0
    
    # 3. payment_to_bill_ratio
    df["payment_to_bill_ratio"] = np.where(
        df["total_bill_amount"] != 0,
        df["total_payment_amount"] / df["total_bill_amount"],
        0.0
    )
    
    # 4. late_payment_count (months where pay status is > 0)
    if existing_status_cols:
        # Check if values are > 0 (1 means 1 month delay, etc.)
        df["late_payment_count"] = (df[existing_status_cols] > 0).sum(axis=1)
    else:
        df["late_payment_count"] = 0
        
    # 5. credit_utilization_proxy
    if "limit_bal" in df.columns:
        df["credit_utilization_proxy"] = np.where(
            df["limit_bal"] != 0,
            df["avg_bill_amount"] / df["limit_bal"],
            0.0
        )
    else:
        df["credit_utilization_proxy"] = 0.0
        
    # Return selected columns for features table
    base_feature_cols = [
        "customer_id", "limit_bal", "sex", "education", "marriage", "age",
        "pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6",
        "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6",
        "pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6",
        "is_default"
    ]
    derived_cols = [
        "avg_bill_amount", "avg_payment_amount", "total_bill_amount", "total_payment_amount",
        "payment_to_bill_ratio", "late_payment_count", "credit_utilization_proxy"
    ]
    
    # Filter only existing columns
    final_cols = [c for c in (base_feature_cols + derived_cols) if c in df.columns]
    return df[final_cols]

def main():
    print("--- Starting UCI Dataset Integration ---")
    if not XLS_PATH.exists():
        raise FileNotFoundError(f"Raw dataset file not found at: {XLS_PATH}")
        
    print(f"Reading Excel file: {XLS_PATH}")
    
    # Load dataset with header=1 to bypass the title header row (usually first row is descriptive title)
    df = pd.read_excel(XLS_PATH, header=1)
    raw_rows = len(df)
    print(f"Raw rows loaded: {raw_rows}")
    
    # Clean columns
    df = clean_column_names(df)
    print(f"Normalized columns: {df.columns.tolist()[:10]}... (Total: {len(df.columns)})")
    
    # Detect target
    df, target_col = detect_and_rename_target(df)
    
    # Verify/create DB connection
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    # Save raw data to credit_default_raw
    print("Inserting cleaned raw dataset into 'credit_default_raw'...")
    df.to_sql("credit_default_raw", conn, if_exists="replace", index=False)
    
    # Process features
    feature_df = process_features(df)
    
    # Save features data to credit_default_features
    print("Inserting processed features into 'credit_default_features'...")
    feature_df.to_sql("credit_default_features", conn, if_exists="replace", index=False)
    
    conn.commit()
    conn.close()
    
    print("\n--- Summary of Loaded Data ---")
    print(f"Raw rows: {raw_rows}")
    print(f"Target column: is_default (mapped from {target_col})")
    print(f"Rows inserted into credit_default_raw: {len(df)}")
    print(f"Rows inserted into credit_default_features: {len(feature_df)}")
    
    if "is_default" in feature_df.columns:
        dist = feature_df["is_default"].value_counts()
        print(f"Class distribution for target 'is_default':\n{dist}")
    
    print("\nDataset successfully integrated with local SQLite database.")

if __name__ == "__main__":
    main()
