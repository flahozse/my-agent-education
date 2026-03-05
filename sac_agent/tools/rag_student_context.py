"""
RAG-style student context loader.

Instead of querying BigQuery on every tool call, this module loads the
complete student profile once into session state (tool_context.state).
All other tools then read from that in-memory context, eliminating
repeated BigQuery queries within the same conversation.

Flow:
    1. Student provides identifier → set_student_identifier()
    2. load_student_context() → ONE BigQuery round-trip, stores in session
    3. get_student_info / get_payment_status / etc. → read from session state
"""

import os
from datetime import date, datetime
from google.cloud import bigquery
from google.adk.tools import ToolContext
from ..session_manager import get_session_manager, get_session_id

# Key used to store the student context in tool_context.state
SESSION_CONTEXT_KEY = "student_rag_context"

# Initialize BigQuery client once at module level
try:
    _bq_client = bigquery.Client(project=os.getenv("BQ_PROJECT_ID"))
except Exception as e:
    print(f"[rag_student_context] Error initializing BigQuery client: {e}")
    _bq_client = None


def _serialize(value):
    """Convert non-JSON-serializable types (date, datetime) to strings."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def load_student_context(tool_context: ToolContext) -> str:
    """
    Loads the complete student profile from BigQuery into session state.

    This is the single BigQuery round-trip for the entire conversation.
    It fetches student info, payments, enrollment and grades in 4 queries
    and caches the results in tool_context.state under SESSION_CONTEXT_KEY.

    Subsequent calls in the same session are no-ops (data already cached).

    Args:
        tool_context: ADK ToolContext that carries session state.

    Returns:
        str: Confirmation message or error description.

    Example:
        After set_student_identifier(), the agent should call this tool so
        that get_student_info / get_payment_status / etc. can serve the
        data without touching BigQuery again.
    """
    # ── 0. Guard: already loaded ─────────────────────────────────────────────
    if SESSION_CONTEXT_KEY in tool_context.state:
        name = tool_context.state[SESSION_CONTEXT_KEY].get("profile", {}).get(
            "full_name", "el estudiante"
        )
        return f"El contexto del estudiante ya estaba cargado en sesión para: {name}"

    # ── 1. Require BigQuery client ────────────────────────────────────────────
    if _bq_client is None:
        return (
            "Error: No se pudo conectar con BigQuery. "
            "Verifica la configuración de credenciales."
        )

    # ── 2. Require student identifier ─────────────────────────────────────────
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)
    student_id = session_manager.get_student_identifier(session_id)

    if not student_id:
        return (
            "No hay identificación almacenada en la sesión. "
            "Primero llama a set_student_identifier()."
        )

    project = _bq_client.project
    dataset = os.getenv("BQ_DATASET_ID")

    job_cfg = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("student_id", "STRING", student_id)
        ]
    )

    try:
        # ── 3a. Student profile ───────────────────────────────────────────────
        profile_rows = list(
            _bq_client.query(
                f"""
                SELECT student_id, full_name, email, phone,
                       document_number, program_name, enrollment_date, status
                FROM `{project}.{dataset}.{os.getenv("BQ_STUDENTS_TABLE", "student_info")}`
                WHERE document_number = @student_id OR email = @student_id
                LIMIT 1
                """,
                job_config=job_cfg,
            ).result()
        )

        if not profile_rows:
            return f"No se encontró ningún estudiante con el identificador: {student_id}"

        row = profile_rows[0]
        internal_student_id = row.student_id

        profile = {k: _serialize(row[k]) for k in row.keys()}

        # ── 3b. Payment history ───────────────────────────────────────────────
        pay_cfg = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "internal_id", "STRING", str(internal_student_id)
                )
            ]
        )
        payments = [
            {k: _serialize(r[k]) for k in r.keys()}
            for r in _bq_client.query(
                f"""
                SELECT payment_date, amount, payment_method, status, concept, due_date
                FROM `{project}.{dataset}.{os.getenv("BQ_PAYMENTS_TABLE", "payments")}`
                WHERE student_id = @internal_id
                ORDER BY payment_date DESC
                LIMIT 10
                """,
                job_config=pay_cfg,
            ).result()
        ]

        # ── 3c. Enrollment ───────────────────────────────────────────────────
        enrollment = [
            {k: _serialize(r[k]) for k in r.keys()}
            for r in _bq_client.query(
                f"""
                SELECT e.academic_period, e.enrollment_status,
                       e.enrollment_date, e.credits_enrolled,
                       s.program_name, s.full_name
                FROM `{project}.{dataset}.{os.getenv("BQ_ENROLLMENT_TABLE", "enrollment")}` e
                JOIN `{project}.{dataset}.{os.getenv("BQ_STUDENTS_TABLE", "student_info")}` s
                  ON e.student_id = s.student_id
                WHERE e.student_id = @internal_id
                ORDER BY e.academic_period DESC
                LIMIT 1
                """,
                job_config=pay_cfg,
            ).result()
        ]

        # ── 3d. Grades ───────────────────────────────────────────────────────
        grades = [
            {k: _serialize(r[k]) for k in r.keys()}
            for r in _bq_client.query(
                f"""
                SELECT course_name, course_code, grade, credits, academic_period, status
                FROM `{project}.{dataset}.{os.getenv("BQ_GRADES_TABLE", "grades")}`
                WHERE student_id = @internal_id
                ORDER BY academic_period DESC, course_name
                LIMIT 20
                """,
                job_config=pay_cfg,
            ).result()
        ]

        # ── 4. Store everything in session state ──────────────────────────────
        tool_context.state[SESSION_CONTEXT_KEY] = {
            "profile": profile,
            "payments": payments,
            "enrollment": enrollment,
            "grades": grades,
        }

        return (
            f"Contexto cargado correctamente para: {profile['full_name']} "
            f"({len(payments)} pagos, {len(grades)} calificaciones)."
        )

    except Exception as exc:
        return f"Error al cargar el contexto desde BigQuery: {exc}"
