-- Starter schema for RiskLens AI
-- This file will be updated as the data model evolves.

CREATE TABLE IF NOT EXISTS credit_applications (
    application_id INT PRIMARY KEY,
    customer_id INT,
    loan_amount DECIMAL(12, 2),
    annual_income DECIMAL(12, 2),
    credit_score INT,
    default_flag INT,
    created_at DATETIME2
);
