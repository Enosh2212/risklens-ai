import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "local_db" / "risklens_local.db"


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"SQLite database not found at {DB_PATH}. Run local_sqlite_setup.py first.")

    with sqlite3.connect(DB_PATH) as conn:
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

        print(f"Connected to local SQLite database: {DB_PATH}")
        print("Tables found:")
        for table in tables:
            print(f"- {table}")

        print("\nRow counts:")
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
            print(f"{table}: {count}")


if __name__ == "__main__":
    main()
