"""Tools package for SAC Agent."""

from .rag_student_context import load_student_context

from .bigquery_tools import (
    get_student_info,
    get_payment_status,
    get_enrollment_status,
    get_academic_grades,
)

from .student_identification import (
    set_student_identifier,
    get_stored_student_identifier,
    clear_student_identifier,
    check_has_student_identifier,
)

from .certification_tools import (
    generate_certification,
)

# Note: Web search tools are now implemented as a sub-agent
# Import from sac_agent.sub_agents if needed

__all__ = [
    # RAG context loader (call once after set_student_identifier)
    "load_student_context",
    # Student data (read from session state, no BigQuery per call)
    "get_student_info",
    "get_payment_status",
    "get_enrollment_status",
    "get_academic_grades",
    # Session management
    "set_student_identifier",
    "get_stored_student_identifier",
    "clear_student_identifier",
    "check_has_student_identifier",
    # Certifications
    "generate_certification",
]
