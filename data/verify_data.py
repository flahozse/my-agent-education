"""Quick verification script to test BigQuery data."""

import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("BQ_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID")

client = bigquery.Client(project=PROJECT_ID)

print("=" * 60)
print("Verificando datos en BigQuery")
print("=" * 60)

# Test 1: Count records
query = f"""
SELECT 'student_info' as table_name, COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.student_info`
UNION ALL
SELECT 'payments', COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.payments`
UNION ALL
SELECT 'enrollment', COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.enrollment`
UNION ALL
SELECT 'grades', COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.grades`
"""

print("\n1. Conteo de registros por tabla:")
print("-" * 40)
results = client.query(query).result()
for row in results:
    print(f"   {row.table_name}: {row.count} registros")

# Test 2: Sample student
query = f"""
SELECT full_name, email, program_name, status
FROM `{PROJECT_ID}.{DATASET_ID}.student_info`
WHERE document_number = '1234567890'
LIMIT 1
"""

print("\n2. Ejemplo de búsqueda por documento (1234567890):")
print("-" * 40)
results = client.query(query).result()
for row in results:
    print(f"   Nombre: {row.full_name}")
    print(f"   Email: {row.email}")
    print(f"   Programa: {row.program_name}")
    print(f"   Estado: {row.status}")

# Test 3: Payment status
query = f"""
SELECT
    s.full_name,
    p.concept,
    p.amount,
    p.status,
    p.due_date
FROM `{PROJECT_ID}.{DATASET_ID}.payments` p
JOIN `{PROJECT_ID}.{DATASET_ID}.student_info` s
  ON p.student_id = s.student_id
WHERE s.document_number = '1234567890'
ORDER BY p.due_date DESC
LIMIT 3
"""

print("\n3. Últimos 3 pagos de María González:")
print("-" * 40)
results = client.query(query).result()
for row in results:
    amount = f"${row.amount:,.0f}" if row.amount else "N/A"
    due_date = row.due_date.strftime("%Y-%m-%d") if row.due_date else "N/A"
    print(f"   {row.concept}: {amount} - {row.status} (Vence: {due_date})")

print("\n" + "=" * 60)
print("✓ Verificación completada exitosamente!")
print("=" * 60)
