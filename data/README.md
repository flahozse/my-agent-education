# Datos de Ejemplo para BigQuery

Este directorio contiene datos de ejemplo para el sistema de gestión de estudiantes de ESIC Corporate Medellín.

## Archivos CSV Incluidos

1. **student_info.csv** - Información general de estudiantes (15 registros)
   - ID del estudiante, nombre completo, email, teléfono, documento, programa, fecha de matrícula, estado

2. **payments.csv** - Historial de pagos (51 registros)
   - ID de pago, ID del estudiante, fecha de pago, monto, método, estado, concepto, fecha de vencimiento

3. **enrollment.csv** - Información de matrículas (19 registros)
   - ID de matrícula, ID del estudiante, período académico, estado, fecha, créditos

4. **grades.csv** - Calificaciones académicas (87 registros)
   - ID de calificación, ID del estudiante, nombre del curso, código, nota, créditos, período, estado

## Estructura de Datos

### Programas Incluidos:
- Máster en Marketing Digital
- Máster en Dirección de Empresas (MBA)
- Máster en Big Data y Business Analytics
- Programa Ejecutivo en Transformación Digital
- Máster en Finanzas Corporativas
- Máster en Recursos Humanos y Gestión del Talento
- Programa Ejecutivo en Liderazgo Estratégico

### Períodos Académicos:
- 2023-2 (Segundo semestre 2023)
- 2024-1 (Primer semestre 2024)

### Estados de Pago:
- Pagado
- Pendiente
- Vencido

### Métodos de Pago:
- Transferencia Bancaria
- Tarjeta de Crédito
- PSE

## Carga de Datos en BigQuery

### Opción 1: Script Python Automatizado (Recomendado)

1. **Instalar dependencias:**
   ```bash
   pip3 install google-cloud-bigquery python-dotenv
   ```

2. **Configurar autenticación de Google Cloud:**
   ```bash
   # Opción A: Usar credenciales de cuenta de servicio
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

   # Opción B: Usar gcloud auth
   gcloud auth application-default login
   ```

3. **Verificar las variables de entorno en `.env`:**
   ```bash
   cat ../.env
   ```

   Debe contener:
   ```
   BQ_PROJECT_ID=<GCP PROJECT>
   BQ_DATASET_ID=students
   GOOGLE_CLOUD_LOCATION=<LOCATION>
   ```

4. **Ejecutar el script de carga:**
   ```bash
   python3 load_data_to_bigquery.py
   ```

   El script:
   - Crea el dataset `students` si no existe
   - Crea las 4 tablas con sus esquemas
   - Carga los datos desde los archivos CSV
   - Muestra un resumen de las filas cargadas

### Opción 2: Carga Manual vía Consola de BigQuery

1. **Ir a BigQuery Console:**
   https://console.cloud.google.com/bigquery

2. **Crear el dataset:**
   - Click en tu proyecto `mo-snowflake-bigquery-poc`
   - Click en "CREATE DATASET"
   - Dataset ID: `students`
   - Location: `europe-southwest1`
   - Click "CREATE DATASET"

3. **Crear cada tabla:**
   - Click en el dataset `students`
   - Click en "CREATE TABLE"
   - Source: "Upload"
   - File: Selecciona el archivo CSV correspondiente
   - Table name: nombre de la tabla (student_info, payments, enrollment, grades)
   - Schema: "Auto detect" o pega el esquema desde abajo
   - Click "CREATE TABLE"

### Opción 3: Usando bq command-line tool

```bash
# Crear dataset
bq mk \
  --location=europe-southwest1 \
  --dataset \
  mo-snowflake-bigquery-poc:students

# Cargar student_info
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  mo-snowflake-bigquery-poc:students.student_info \
  student_info.csv \
  student_id:STRING,full_name:STRING,email:STRING,phone:STRING,document_number:STRING,program_name:STRING,enrollment_date:DATE,status:STRING

# Cargar payments
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  mo-snowflake-bigquery-poc:students.payments \
  payments.csv \
  payment_id:STRING,student_id:STRING,payment_date:DATE,amount:FLOAT64,payment_method:STRING,status:STRING,concept:STRING,due_date:DATE

# Cargar enrollment
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  mo-snowflake-bigquery-poc:students.enrollment \
  enrollment.csv \
  enrollment_id:STRING,student_id:STRING,academic_period:STRING,enrollment_status:STRING,enrollment_date:DATE,credits_enrolled:INT64

# Cargar grades
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  mo-snowflake-bigquery-poc:students.grades \
  grades.csv \
  grade_id:STRING,student_id:STRING,course_name:STRING,course_code:STRING,grade:FLOAT64,credits:INT64,academic_period:STRING,status:STRING
```

## Verificación de Datos

Una vez cargados los datos, verifica con estas consultas:

```sql
-- Contar registros en cada tabla
SELECT 'student_info' as table_name, COUNT(*) as count FROM `mo-snowflake-bigquery-poc.students.student_info`
UNION ALL
SELECT 'payments', COUNT(*) FROM `mo-snowflake-bigquery-poc.students.payments`
UNION ALL
SELECT 'enrollment', COUNT(*) FROM `mo-snowflake-bigquery-poc.students.enrollment`
UNION ALL
SELECT 'grades', COUNT(*) FROM `mo-snowflake-bigquery-poc.students.grades`;

-- Ver estudiantes activos
SELECT full_name, program_name, status
FROM `mo-snowflake-bigquery-poc.students.student_info`
WHERE status = 'Activo'
ORDER BY enrollment_date DESC;

-- Ver pagos pendientes
SELECT s.full_name, p.concept, p.amount, p.due_date
FROM `mo-snowflake-bigquery-poc.students.payments` p
JOIN `mo-snowflake-bigquery-poc.students.student_info` s
  ON p.student_id = s.student_id
WHERE p.status = 'Pendiente'
ORDER BY p.due_date;
```

## Datos de Prueba para el Agente

Puedes probar el agente con estos ejemplos:

### Búsqueda por documento:
- "Busca información del estudiante con documento 1234567890"
- "¿Cuál es el estado de pagos del estudiante 2345678901?"
- "Muéstrame las calificaciones del documento 3456789012"

### Búsqueda por email:
- "Busca información del estudiante maria.gonzalez@esic.edu.co"
- "Estado de matrícula de juan.perez@esic.edu.co"
- "Calificaciones de ana.martinez@esic.edu.co"

### Estudiantes con situaciones especiales:
- **STU013 (Isabella Martín)** - Estado Inactivo con pagos vencidos
- **STU011 (Valentina Restrepo)** - Estudiante graduado
- **STU001 (María González)** - Tiene pago pendiente para abril

## Notas Importantes

1. **Formato de montos:** Los montos están en pesos colombianos (COP)
2. **Escala de calificaciones:** 0-5 (sistema colombiano)
3. **Fechas:** Formato YYYY-MM-DD
4. **Campos vacíos:** En CSV, campos vacíos representan valores NULL en BigQuery

## Troubleshooting

### Error: "Permission denied"
- Verifica que tienes permisos de BigQuery Admin o Data Editor en el proyecto
- Confirma que las credenciales están configuradas correctamente

### Error: "Dataset not found"
- Ejecuta primero la creación del dataset
- Verifica que el nombre del proyecto sea correcto en `.env`

### Error: "Schema mismatch"
- Verifica que el archivo CSV no tenga caracteres especiales
- Asegúrate de que las fechas estén en formato YYYY-MM-DD
- Revisa que los números no tengan formato de texto

## Próximos Pasos

Después de cargar los datos:

1. Prueba las herramientas de BigQuery del agente
2. Verifica que las consultas retornan los datos esperados
3. Ajusta los prompts del agente según sea necesario
4. Añade más datos de prueba si lo requieres

Para cualquier pregunta o problema, revisa la documentación de Google Cloud BigQuery:
https://cloud.google.com/bigquery/docs
