"""Script to load CSV data into BigQuery tables.

This script creates the necessary BigQuery dataset and tables,
and loads the sample data from CSV files.

Requirements:
    - google-cloud-bigquery
    - Environment variables set in .env file

Usage:
    python load_data_to_bigquery.py
"""

import os
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
PROJECT_ID = os.getenv("BQ_PROJECT_ID", "mo-snowflake-bigquery-poc")
DATASET_ID = os.getenv("BQ_DATASET_ID", "test")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-southwest1")

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID)

# Table schemas
SCHEMAS = {
    "student_info": [
        bigquery.SchemaField("student_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("full_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("phone", "STRING"),
        bigquery.SchemaField("document_number", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("program_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("enrollment_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
    ],
    "payments": [
        bigquery.SchemaField("payment_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("student_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("payment_date", "DATE"),
        bigquery.SchemaField("amount", "FLOAT64"),
        bigquery.SchemaField("payment_method", "STRING"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("concept", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("due_date", "DATE"),
    ],
    "enrollment": [
        bigquery.SchemaField("enrollment_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("student_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("academic_period", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("enrollment_status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("enrollment_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("credits_enrolled", "INT64", mode="REQUIRED"),
    ],
    "grades": [
        bigquery.SchemaField("grade_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("student_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("course_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("course_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("grade", "FLOAT64"),
        bigquery.SchemaField("credits", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("academic_period", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
    ],
}


def create_dataset():
    """Create the BigQuery dataset if it doesn't exist."""
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"

    try:
        client.get_dataset(dataset_id)
        print(f"✓ Dataset {dataset_id} already exists")
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = LOCATION
        dataset.description = "Dataset for ESIC Corporate Medellín student information"

        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✓ Created dataset {dataset_id}")


def create_table(table_name, schema):
    """Create a BigQuery table if it doesn't exist."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    try:
        client.get_table(table_id)
        print(f"✓ Table {table_id} already exists")
        return False  # Table already exists
    except NotFound:
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        print(f"✓ Created table {table_id}")
        return True  # Table was created


def load_csv_to_table(table_name, csv_file):
    """Load data from CSV file into BigQuery table."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=False,
        schema=SCHEMAS[table_name],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    with open(csv_file, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)

    job.result()  # Wait for the job to complete

    table = client.get_table(table_id)
    print(f"✓ Loaded {table.num_rows} rows into {table_id}")


def main():
    """Main function to orchestrate the data loading process."""
    print("=" * 60)
    print("BigQuery Data Loading Script")
    print("=" * 60)
    print(f"\nProject: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Location: {LOCATION}\n")

    # Step 1: Create dataset
    print("Step 1: Creating dataset...")
    create_dataset()

    # Step 2: Create tables
    print("\nStep 2: Creating tables...")
    for table_name, schema in SCHEMAS.items():
        create_table(table_name, schema)

    # Step 3: Load data from CSV files
    print("\nStep 3: Loading data from CSV files...")
    script_dir = os.path.dirname(os.path.abspath(__file__))

    csv_files = {
        "student_info": os.path.join(script_dir, "student_info.csv"),
        "payments": os.path.join(script_dir, "payments.csv"),
        "enrollment": os.path.join(script_dir, "enrollment.csv"),
        "grades": os.path.join(script_dir, "grades.csv"),
    }

    for table_name, csv_file in csv_files.items():
        if os.path.exists(csv_file):
            load_csv_to_table(table_name, csv_file)
        else:
            print(f"✗ CSV file not found: {csv_file}")

    print("\n" + "=" * 60)
    print("Data loading completed successfully!")
    print("=" * 60)
    print("\nYou can now query the tables using:")
    print(f"  - {PROJECT_ID}.{DATASET_ID}.student_info")
    print(f"  - {PROJECT_ID}.{DATASET_ID}.payments")
    print(f"  - {PROJECT_ID}.{DATASET_ID}.enrollment")
    print(f"  - {PROJECT_ID}.{DATASET_ID}.grades")
    print("\nExample query:")
    print(f"  SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.student_info` LIMIT 10")


if __name__ == "__main__":
    main()
