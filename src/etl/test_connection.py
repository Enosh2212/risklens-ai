import os
import sys
from pathlib import Path

import mssql_python as mssql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

try:
    sys.stdout.reconfigure(line_buffering=True)
except AttributeError:
    pass


def clean_value(value: str) -> str:
    if value is None:
        return ""
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1].strip()
    return value


if not ENV_PATH.exists():
    print(f"ERROR: .env file not found at: {ENV_PATH}")
    print("Create .env from .env.example and add Azure SQL values.")
    raise SystemExit(1)

load_dotenv(ENV_PATH, encoding="utf-8-sig", override=True)

server = clean_value(os.getenv("AZURE_SQL_SERVER"))
database = clean_value(os.getenv("AZURE_SQL_DATABASE"))
entra_username = clean_value(os.getenv("AZURE_ENTRA_USERNAME"))

required = {
    "AZURE_SQL_SERVER": server,
    "AZURE_SQL_DATABASE": database,
    "AZURE_ENTRA_USERNAME": entra_username,
}
missing = [key for key, value in required.items() if not value]

print("==== Safe environment check ====")
print(f"ENV_PATH: {ENV_PATH}")
print(f"AZURE_SQL_SERVER: {server or 'MISSING'}")
print(f"AZURE_SQL_DATABASE: {database or 'MISSING'}")
print(f"AZURE_ENTRA_USERNAME: {entra_username or 'MISSING'}")
print("Driver: mssql-python")
print("Authentication: Microsoft Entra interactive")

if missing:
    print(f"ERROR: Missing environment variables: {', '.join(missing)}")
    raise SystemExit(1)

connection_string = (
    f"Server=tcp:{server},1433;"
    f"Database={database};"
    f"UID={entra_username};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Authentication=ActiveDirectoryInteractive;"
)

print("\n==== Test: connect with mssql-python and Microsoft Entra ====")
try:
    with mssql.connect(connection_string, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                DB_NAME() AS current_database,
                SUSER_SNAME() AS login_name,
                USER_NAME() AS database_user;
            """
        )
        identity = cursor.fetchone()

        print("OK: Connected to Azure SQL database.")
        print(f"Current database: {identity.current_database}")
        print(f"Login name: {identity.login_name}")
        print(f"Database user: {identity.database_user}")

        cursor.execute(
            """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE='BASE TABLE'
            ORDER BY TABLE_NAME;
            """
        )
        tables = [row.TABLE_NAME for row in cursor.fetchall()]

    print("Tables found:")
    for table in tables:
        print(f"- {table}")
except Exception as exc:
    print(f"ERROR: mssql-python Entra connection failed for database: {database}")
    print(str(exc))
    print("\nLikely causes:")
    print("- browser sign-in was cancelled or blocked")
    print("- signed-in Entra identity does not have access to this Azure SQL database")
    print("- database name/server name is incorrect")
    print("- Azure SQL firewall or network access is blocking the connection")
    raise SystemExit(1)
