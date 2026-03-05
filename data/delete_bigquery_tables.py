"""Script to delete BigQuery tables created by load_data_to_bigquery.py.

Requirements:
    - google-cloud-bigquery
    - Environment variables set in .env file

Usage:
    python delete_bigquery_tables.py
"""

import os
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from dotenv import load_dotenv
load_dotenv()

# Configuration
PROJECT_ID = os.getenv("BQ_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID")

# Tables to delete (same as those created in load_data_to_bigquery.py)
TABLES = ["student_info", "payments", "enrollment", "grades"]

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID)


def delete_table(table_name: str) -> None:
    """Delete a BigQuery table if it exists."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    try:
        client.delete_table(table_id)
        print(f"✓ Deleted table {table_id}")
    except NotFound:
        print(f"  Table {table_id} not found, skipping")


def main() -> None:
    print("=" * 60)
    print("BigQuery Table Deletion Script")
    print("=" * 60)
    print(f"\nProject : {PROJECT_ID}")
    print(f"Dataset : {DATASET_ID}\n")

    print("Deleting tables...")
    for table_name in TABLES:
        delete_table(table_name)

    print("\n" + "=" * 60)
    print("Deletion completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
