"""BigQuery tools for querying student information.

This module provides tools to query student data from BigQuery tables,
including enrollment status, payment history, and academic records.
"""

import os
from google.cloud import bigquery
from google.adk.tools import ToolContext
from ..session_manager import get_session_manager, get_session_id

# Initialize BigQuery client
try:
    client = bigquery.Client(project=os.getenv("BQ_PROJECT_ID"))
except Exception as e:
    print(f"Error initializing BigQuery client: {e}")
    client = None


def get_student_info(tool_context: ToolContext) -> str:
    """
    Retrieves general information about a student from BigQuery.

    Uses the student identifier stored in the current session. If no identifier
    is stored, returns an error message prompting to provide identification first.

    Args:
        tool_context: The tool context from ADK

    Returns:
        str: Student information formatted as text, or an error message.

    Example:
        User: "Muestra mi información de estudiante"
        Returns: Student name, email, program, enrollment date, etc.
    """
    if client is None:
        return "Error: No se pudo conectar con BigQuery. Por favor, verifica la configuración."

    # Get student identifier from session
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)
    student_id = session_manager.get_student_identifier(session_id)

    if not student_id:
        return "No tengo tu identificación almacenada. Por favor, proporciona tu número de documento o correo electrónico para poder consultar tu información."

    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = os.getenv("BQ_STUDENTS_TABLE", "student_info")

    query = f"""
        SELECT
            student_id,
            full_name,
            email,
            phone,
            document_number,
            program_name,
            enrollment_date,
            status
        FROM
            `{client.project}.{dataset_id}.{table_id}`
        WHERE
            document_number = @student_id
            OR email = @student_id
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("student_id", "STRING", student_id)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        for row in results:
            return f"""
**Información del Estudiante:**

- **Nombre:** {row.full_name}
- **Email:** {row.email}
- **Teléfono:** {row.phone if row.phone else 'No registrado'}
- **Documento:** {row.document_number}
- **Programa:** {row.program_name}
- **Fecha de matrícula:** {row.enrollment_date}
- **Estado:** {row.status}
"""

        return f"No se encontró información para el identificador: {student_id}"

    except Exception as e:
        return f"Error al consultar BigQuery: {str(e)}"


def get_payment_status(tool_context: ToolContext) -> str:
    """
    Retrieves payment history and status for a student.

    Uses the student identifier stored in the current session.

    Args:
        tool_context: The tool context from ADK

    Returns:
        str: Payment history formatted as a markdown table, or an error message.

    Example:
        User: "¿Cuál es el estado de mis pagos?"
    """
    if client is None:
        return "Error: No se pudo conectar con BigQuery. Por favor, verifica la configuración."

    # Get student identifier from session
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)
    student_id = session_manager.get_student_identifier(session_id)

    if not student_id:
        return "No tengo tu identificación almacenada. Por favor, proporciona tu número de documento o correo electrónico para poder consultar tus pagos."

    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = os.getenv("BQ_PAYMENTS_TABLE", "payments")

    query = f"""
        SELECT
            payment_date,
            amount,
            payment_method,
            status,
            concept,
            due_date
        FROM
            `{client.project}.{dataset_id}.{table_id}`
        WHERE
            student_id IN (
                SELECT student_id
                FROM `{client.project}.{dataset_id}.student_info`
                WHERE document_number = @student_id OR email = @student_id
            )
        ORDER BY payment_date DESC
        LIMIT 10
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("student_id", "STRING", student_id)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        markdown_table = "**Historial de Pagos:**\n\n"
        markdown_table += "| Fecha Pago | Concepto | Monto | Método | Estado | Fecha Vencimiento |\n"
        markdown_table += "|------------|----------|-------|--------|--------|-------------------|\n"

        count = 0
        for row in results:
            count += 1
            payment_date = row.payment_date.strftime("%Y-%m-%d") if row.payment_date else "N/A"
            due_date = row.due_date.strftime("%Y-%m-%d") if row.due_date else "N/A"
            amount = f"${row.amount:,.2f}" if row.amount else "N/A"

            markdown_table += f"| {payment_date} | {row.concept} | {amount} | {row.payment_method} | {row.status} | {due_date} |\n"

        if count == 0:
            return f"No se encontraron registros de pagos para el estudiante: {student_id}"

        return markdown_table

    except Exception as e:
        return f"Error al consultar BigQuery: {str(e)}"


def get_enrollment_status(tool_context: ToolContext) -> str:
    """
    Retrieves enrollment status and current academic period information.

    Uses the student identifier stored in the current session.

    Args:
        tool_context: The tool context from ADK

    Returns:
        str: Enrollment status information, or an error message.

    Example:
        User: "¿Cuál es mi estado de matrícula?"
    """
    if client is None:
        return "Error: No se pudo conectar con BigQuery. Por favor, verifica la configuración."

    # Get student identifier from session
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)
    student_id = session_manager.get_student_identifier(session_id)

    if not student_id:
        return "No tengo tu identificación almacenada. Por favor, proporciona tu número de documento o correo electrónico para poder consultar tu matrícula."

    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = os.getenv("BQ_ENROLLMENT_TABLE", "enrollment")

    query = f"""
        SELECT
            e.academic_period,
            e.enrollment_status,
            e.enrollment_date,
            e.credits_enrolled,
            s.program_name,
            s.full_name
        FROM
            `{client.project}.{dataset_id}.{table_id}` e
        JOIN
            `{client.project}.{dataset_id}.student_info` s
        ON
            e.student_id = s.student_id
        WHERE
            (s.document_number = @student_id OR s.email = @student_id)
        ORDER BY e.academic_period DESC
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("student_id", "STRING", student_id)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        for row in results:
            enrollment_date = row.enrollment_date.strftime("%Y-%m-%d") if row.enrollment_date else "N/A"
            return f"""
**Estado de Matrícula:**

- **Estudiante:** {row.full_name}
- **Programa:** {row.program_name}
- **Período Académico:** {row.academic_period}
- **Estado:** {row.enrollment_status}
- **Fecha de Matrícula:** {enrollment_date}
- **Créditos Matriculados:** {row.credits_enrolled}
"""

        return f"No se encontró información de matrícula para el estudiante: {student_id}"

    except Exception as e:
        return f"Error al consultar BigQuery: {str(e)}"


def get_academic_grades(tool_context: ToolContext) -> str:
    """
    Retrieves academic grades and performance for a student.

    Uses the student identifier stored in the current session.

    Args:
        tool_context: The tool context from ADK

    Returns:
        str: Academic grades formatted as a markdown table, or an error message.

    Example:
        User: "Muéstrame mis calificaciones"
    """
    if client is None:
        return "Error: No se pudo conectar con BigQuery. Por favor, verifica la configuración."

    # Get student identifier from session
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)
    student_id = session_manager.get_student_identifier(session_id)

    if not student_id:
        return "No tengo tu identificación almacenada. Por favor, proporciona tu número de documento o correo electrónico para poder consultar tus calificaciones."

    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = os.getenv("BQ_GRADES_TABLE", "grades")

    query = f"""
        SELECT
            g.course_name,
            g.course_code,
            g.grade,
            g.credits,
            g.academic_period,
            g.status
        FROM
            `{client.project}.{dataset_id}.{table_id}` g
        WHERE
            g.student_id IN (
                SELECT student_id
                FROM `{client.project}.{dataset_id}.student_info`
                WHERE document_number = @student_id OR email = @student_id
            )
        ORDER BY g.academic_period DESC, g.course_name
        LIMIT 20
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("student_id", "STRING", student_id)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        markdown_table = "**Historial Académico:**\n\n"
        markdown_table += "| Período | Código | Curso | Créditos | Nota | Estado |\n"
        markdown_table += "|---------|--------|-------|----------|------|--------|\n"

        count = 0
        total_grade = 0
        for row in results:
            count += 1
            grade_display = f"{row.grade:.2f}" if row.grade is not None else "N/A"
            if row.grade is not None:
                total_grade += row.grade

            markdown_table += f"| {row.academic_period} | {row.course_code} | {row.course_name} | {row.credits} | {grade_display} | {row.status} |\n"

        if count == 0:
            return f"No se encontraron calificaciones para el estudiante: {student_id}"

        # Calculate average
        if count > 0:
            average = total_grade / count
            markdown_table += f"\n**Promedio General:** {average:.2f}\n"

        return markdown_table

    except Exception as e:
        return f"Error al consultar BigQuery: {str(e)}"
