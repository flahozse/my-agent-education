"""Tools for generating student certifications.

This module provides tools to generate academic certifications for students
based on their completed programs and courses.
"""

import os
from datetime import datetime
from google.cloud import bigquery
from google.adk.tools import ToolContext
from ..session_manager import get_session_manager, get_session_id

# Initialize BigQuery client
try:
    client = bigquery.Client(project=os.getenv("BQ_PROJECT_ID"))
except Exception as e:
    print(f"Error initializing BigQuery client: {e}")
    client = None


def generate_certification(
    tool_context: ToolContext,
    certification_type: str = "program_completion"
) -> str:
    """
    Generate an academic certification for the student.

    This tool creates a formatted certification document based on the student's
    academic records. It includes the student's name, program completed,
    completion date, and other relevant information.

    Uses the student identifier stored in the current session.

    Args:
        tool_context: The tool context from ADK
        certification_type: Type of certification to generate.
                          Options: "program_completion", "course_completion", "grades_transcript"
                          Default: "program_completion"

    Returns:
        str: Formatted certification document in markdown, or an error message.

    Example:
        User: "Genera mi certificación de estudios"
        Agent calls: generate_certification(tool_context, "program_completion")
        Returns: A formatted certification document with student name, program, dates, etc.
    """
    if client is None:
        return "Error: No se pudo conectar con BigQuery. Por favor, verifica la configuración."

    # Get student identifier from session
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)
    student_id = session_manager.get_student_identifier(session_id)

    if not student_id:
        return "No tengo tu identificación almacenada. Por favor, proporciona tu número de documento o correo electrónico para poder generar tu certificación."

    dataset_id = os.getenv("BQ_DATASET_ID")

    # Query to get student information and program details
    query = f"""
        SELECT
            s.full_name,
            s.document_number,
            s.program_name,
            s.enrollment_date,
            e.academic_period,
            e.enrollment_status,
            e.credits_enrolled
        FROM
            `{client.project}.{dataset_id}.student_info` s
        LEFT JOIN
            `{client.project}.{dataset_id}.enrollment` e
        ON
            s.student_id = e.student_id
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
            # Get current date for certification issue date
            issue_date = datetime.now().strftime("%d de %B de %Y")
            enrollment_date_formatted = row.enrollment_date.strftime("%d/%m/%Y") if row.enrollment_date else "N/A"

            if certification_type == "program_completion":
                return _generate_program_completion_cert(
                    row.full_name,
                    row.document_number,
                    row.program_name,
                    enrollment_date_formatted,
                    row.academic_period,
                    issue_date,
                    row.credits_enrolled
                )
            elif certification_type == "course_completion":
                return _generate_course_completion_cert(
                    tool_context,
                    row.full_name,
                    row.document_number,
                    issue_date
                )
            elif certification_type == "grades_transcript":
                return _generate_grades_transcript(
                    tool_context,
                    row.full_name,
                    row.document_number,
                    row.program_name,
                    issue_date
                )
            else:
                return f"Tipo de certificación no válido: {certification_type}. Opciones válidas: program_completion, course_completion, grades_transcript"

        return f"No se encontró información para generar la certificación del estudiante: {student_id}"

    except Exception as e:
        return f"Error al generar la certificación: {str(e)}"


def _generate_program_completion_cert(
    full_name: str,
    document_number: str,
    program_name: str,
    enrollment_date: str,
    academic_period: str,
    issue_date: str,
    credits: int
) -> str:
    """Generate a program completion certification."""
    return f"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                   CERTIFICADO DE FINALIZACIÓN                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

                        INSTITUCIÓN EDUCATIVA
                     Centro de Estudios Superiores


La Dirección Académica certifica que:

**{full_name}**
Documento de Identidad: {document_number}

Ha completado satisfactoriamente el programa académico:

**{program_name}**

Fecha de matrícula: {enrollment_date}
Período académico: {academic_period}
Total de créditos cursados: {credits}

Este certificado se expide a petición del interesado para los fines que
estime conveniente.

Fecha de expedición: {issue_date}


─────────────────────────────────────────────────────────────────────

_________________________              _________________________
Director Académico                     Secretaría Académica

─────────────────────────────────────────────────────────────────────

                    Certificado número: CERT-{document_number[-6:]}-{datetime.now().year}

Este documento es una certificación simulada generada automáticamente.
Para certificaciones oficiales, contacte con la secretaría académica.
"""


def _generate_course_completion_cert(
    tool_context: ToolContext,
    full_name: str,
    document_number: str,
    issue_date: str
) -> str:
    """Generate a course completion certification with course details."""
    # Get student identifier from session
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)
    student_id = session_manager.get_student_identifier(session_id)

    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = os.getenv("BQ_GRADES_TABLE", "grades")

    # Query to get completed courses
    query = f"""
        SELECT
            g.course_name,
            g.course_code,
            g.grade,
            g.credits,
            g.academic_period
        FROM
            `{client.project}.{dataset_id}.{table_id}` g
        WHERE
            g.student_id IN (
                SELECT student_id
                FROM `{client.project}.{dataset_id}.student_info`
                WHERE document_number = @student_id OR email = @student_id
            )
            AND g.status = 'Aprobado'
        ORDER BY g.academic_period DESC
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

        courses_list = ""
        total_credits = 0

        for row in results:
            courses_list += f"- {row.course_name} ({row.course_code}) - {row.credits} créditos - Nota: {row.grade:.2f}\n"
            total_credits += row.credits

        return f"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              CERTIFICADO DE CURSOS COMPLETADOS                       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

                        INSTITUCIÓN EDUCATIVA
                     Centro de Estudios Superiores


La Dirección Académica certifica que:

**{full_name}**
Documento de Identidad: {document_number}

Ha completado satisfactoriamente los siguientes cursos:

{courses_list}
**Total de créditos completados:** {total_credits}

Este certificado se expide a petición del interesado para los fines que
estime conveniente.

Fecha de expedición: {issue_date}


─────────────────────────────────────────────────────────────────────

_________________________              _________________________
Director Académico                     Secretaría Académica

─────────────────────────────────────────────────────────────────────

                    Certificado número: CERT-{document_number[-6:]}-{datetime.now().year}

Este documento es una certificación simulada generada automáticamente.
Para certificaciones oficiales, contacte con la secretaría académica.
"""

    except Exception as e:
        return f"Error al generar la certificación de cursos: {str(e)}"


def _generate_grades_transcript(
    tool_context: ToolContext,
    full_name: str,
    document_number: str,
    program_name: str,
    issue_date: str
) -> str:
    """Generate an official grades transcript."""
    # Get student identifier from session
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)
    student_id = session_manager.get_student_identifier(session_id)

    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = os.getenv("BQ_GRADES_TABLE", "grades")

    # Query to get all grades
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
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("student_id", "STRING", student_id)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        markdown_table = "| Período | Código | Curso | Créditos | Nota | Estado |\n"
        markdown_table += "|---------|--------|-------|----------|------|--------|\n"

        total_credits = 0
        total_grade = 0
        count = 0

        for row in results:
            count += 1
            grade_display = f"{row.grade:.2f}" if row.grade is not None else "N/A"
            if row.grade is not None:
                total_grade += row.grade
                total_credits += row.credits

            markdown_table += f"| {row.academic_period} | {row.course_code} | {row.course_name} | {row.credits} | {grade_display} | {row.status} |\n"

        average = total_grade / count if count > 0 else 0

        return f"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                  CERTIFICADO DE CALIFICACIONES                       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

                        INSTITUCIÓN EDUCATIVA
                     Centro de Estudios Superiores


**Estudiante:** {full_name}
**Documento:** {document_number}
**Programa:** {program_name}

**HISTORIAL ACADÉMICO COMPLETO:**

{markdown_table}

**RESUMEN:**
- Total de créditos completados: {total_credits}
- Promedio general: {average:.2f}

Este certificado se expide a petición del interesado para los fines que
estime conveniente.

Fecha de expedición: {issue_date}


─────────────────────────────────────────────────────────────────────

_________________________              _________________________
Director Académico                     Secretaría Académica

─────────────────────────────────────────────────────────────────────

                    Certificado número: CERT-{document_number[-6:]}-{datetime.now().year}

Este documento es una certificación simulada generada automáticamente.
Para certificaciones oficiales, contacte con la secretaría académica.
"""

    except Exception as e:
        return f"Error al generar el certificado de calificaciones: {str(e)}"
