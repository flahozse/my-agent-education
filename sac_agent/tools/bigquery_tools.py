"""BigQuery tools for querying student information.

This module provides tools to query student data. Data is served from the
in-memory session context loaded by load_student_context() instead of
issuing a new BigQuery query on every call.

The BigQuery round-trip happens exactly ONCE per conversation (inside
load_student_context). These functions simply format and return the cached
data, making them fast and cheap.
"""

from google.adk.tools import ToolContext
from .rag_student_context import SESSION_CONTEXT_KEY

_NOT_LOADED_MSG = (
    "El contexto del estudiante no está cargado todavía. "
    "Asegúrate de llamar a load_student_context() después de "
    "registrar la identificación del estudiante."
)


def get_student_info(tool_context: ToolContext) -> str:
    """
    Retrieves general information about a student from the session context.

    Uses data previously loaded by load_student_context(). If the context
    has not been loaded yet, returns an error message.

    Args:
        tool_context: The tool context from ADK.

    Returns:
        str: Student information formatted as text, or an error message.

    Example:
        User: "Muéstrame mi información de estudiante"
        Returns: Student name, email, program, enrollment date, etc.
    """
    context = tool_context.state.get(SESSION_CONTEXT_KEY)
    if not context:
        return _NOT_LOADED_MSG

    p = context.get("profile", {})
    if not p:
        return "No se encontró información de perfil en el contexto de sesión."

    return f"""
**Información del Estudiante:**

- **Nombre:** {p.get("full_name", "N/A")}
- **Email:** {p.get("email", "N/A")}
- **Teléfono:** {p.get("phone") or "No registrado"}
- **Documento:** {p.get("document_number", "N/A")}
- **Programa:** {p.get("program_name", "N/A")}
- **Fecha de matrícula:** {p.get("enrollment_date", "N/A")}
- **Estado:** {p.get("status", "N/A")}
"""


def get_payment_status(tool_context: ToolContext) -> str:
    """
    Retrieves payment history and status for a student from the session context.

    Uses data previously loaded by load_student_context(). If the context
    has not been loaded yet, returns an error message.

    Args:
        tool_context: The tool context from ADK.

    Returns:
        str: Payment history formatted as a markdown table, or an error message.

    Example:
        User: "¿Cuál es el estado de mis pagos?"
    """
    context = tool_context.state.get(SESSION_CONTEXT_KEY)
    if not context:
        return _NOT_LOADED_MSG

    payments = context.get("payments", [])
    if not payments:
        return "No se encontraron registros de pagos para este estudiante."

    markdown = "**Historial de Pagos:**\n\n"
    markdown += "| Fecha Pago | Concepto | Monto | Método | Estado | Fecha Vencimiento |\n"
    markdown += "|------------|----------|-------|--------|--------|-------------------|\n"

    for row in payments:
        amount = f"${float(row['amount']):,.2f}" if row.get("amount") is not None else "N/A"
        markdown += (
            f"| {row.get('payment_date', 'N/A')} "
            f"| {row.get('concept', 'N/A')} "
            f"| {amount} "
            f"| {row.get('payment_method', 'N/A')} "
            f"| {row.get('status', 'N/A')} "
            f"| {row.get('due_date', 'N/A')} |\n"
        )

    return markdown


def get_enrollment_status(tool_context: ToolContext) -> str:
    """
    Retrieves enrollment status and current academic period from the session context.

    Uses data previously loaded by load_student_context(). If the context
    has not been loaded yet, returns an error message.

    Args:
        tool_context: The tool context from ADK.

    Returns:
        str: Enrollment status information, or an error message.

    Example:
        User: "¿Cuál es mi estado de matrícula?"
    """
    context = tool_context.state.get(SESSION_CONTEXT_KEY)
    if not context:
        return _NOT_LOADED_MSG

    enrollment_list = context.get("enrollment", [])
    if not enrollment_list:
        return "No se encontró información de matrícula para este estudiante."

    row = enrollment_list[0]
    return f"""
**Estado de Matrícula:**

- **Estudiante:** {row.get("full_name", "N/A")}
- **Programa:** {row.get("program_name", "N/A")}
- **Período Académico:** {row.get("academic_period", "N/A")}
- **Estado:** {row.get("enrollment_status", "N/A")}
- **Fecha de Matrícula:** {row.get("enrollment_date", "N/A")}
- **Créditos Matriculados:** {row.get("credits_enrolled", "N/A")}
"""


def get_academic_grades(tool_context: ToolContext) -> str:
    """
    Retrieves academic grades and performance from the session context.

    Uses data previously loaded by load_student_context(). If the context
    has not been loaded yet, returns an error message.

    Args:
        tool_context: The tool context from ADK.

    Returns:
        str: Academic grades formatted as a markdown table, or an error message.

    Example:
        User: "Muéstrame mis calificaciones"
    """
    context = tool_context.state.get(SESSION_CONTEXT_KEY)
    if not context:
        return _NOT_LOADED_MSG

    grades = context.get("grades", [])
    if not grades:
        return "No se encontraron calificaciones para este estudiante."

    markdown = "**Historial Académico:**\n\n"
    markdown += "| Período | Código | Curso | Créditos | Nota | Estado |\n"
    markdown += "|---------|--------|-------|----------|------|--------|\n"

    total_grade = 0.0
    graded_count = 0

    for row in grades:
        grade_val = row.get("grade")
        grade_display = f"{float(grade_val):.2f}" if grade_val is not None else "N/A"
        if grade_val is not None:
            total_grade += float(grade_val)
            graded_count += 1

        markdown += (
            f"| {row.get('academic_period', 'N/A')} "
            f"| {row.get('course_code', 'N/A')} "
            f"| {row.get('course_name', 'N/A')} "
            f"| {row.get('credits', 'N/A')} "
            f"| {grade_display} "
            f"| {row.get('status', 'N/A')} |\n"
        )

    if graded_count > 0:
        average = total_grade / graded_count
        markdown += f"\n**Promedio General:** {average:.2f}\n"

    return markdown
