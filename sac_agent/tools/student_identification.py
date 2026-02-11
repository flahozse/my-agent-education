"""Tools for student identification and session management.

This module provides tools to request, store, and retrieve student
identifiers (document number or email) for use in BigQuery queries.
"""

from google.adk.tools import ToolContext
from ..session_manager import get_session_manager, get_session_id


def set_student_identifier(tool_context: ToolContext, identifier: str) -> str:
    """
    Store the student's identifier (document number or email) for the current session.

    This tool should be called when the user provides their identification.
    The identifier will be persisted across the conversation, eliminating
    the need to ask repeatedly.

    Args:
        tool_context: The tool context from ADK
        identifier: The student's document number or email address

    Returns:
        str: Confirmation message with the stored identifier

    Example:
        User: "Mi documento es 1234567890"
        Agent calls: set_student_identifier(tool_context, "1234567890")
        Returns: "He registrado tu identificación: 1234567890 (tipo: documento)"
    """
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)

    # Clean and validate the identifier
    identifier = identifier.strip()

    if not identifier:
        return "Error: El identificador no puede estar vacío. Por favor proporciona tu número de documento o correo electrónico."

    # Determine identifier type
    identifier_type = "email" if "@" in identifier else "document"

    # Store in session
    success = session_manager.set_student_identifier(
        session_id,
        identifier,
        identifier_type
    )

    if success:
        type_label = "correo electrónico" if identifier_type == "email" else "documento"
        return f"He registrado tu identificación: {identifier} (tipo: {type_label}). Ahora puedo consultar tu información sin necesidad de que vuelvas a proporcionarla."
    else:
        return "Error al registrar tu identificación. Por favor, intenta nuevamente."


def get_stored_student_identifier(tool_context: ToolContext) -> str:
    """
    Retrieve the student identifier stored in the current session.

    Use this tool to check if we already have the student's identification
    before asking for it again.

    Args:
        tool_context: The tool context from ADK

    Returns:
        str: The stored identifier or a message indicating it's not available

    Example:
        Agent calls: get_stored_student_identifier(tool_context)
        Returns: "1234567890" or "No hay identificación almacenada"
    """
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)

    identifier = session_manager.get_student_identifier(session_id)

    if identifier:
        session_info = session_manager.get_session_info(session_id)
        type_label = "correo electrónico" if session_info.get("identifier_type") == "email" else "documento"
        return f"Identificación almacenada: {identifier} (tipo: {type_label})"
    else:
        return "No hay identificación almacenada en la sesión actual."


def clear_student_identifier(tool_context: ToolContext) -> str:
    """
    Clear the stored student identifier from the session.

    Use this when the user wants to switch to a different student
    or explicitly requests to clear their information.

    Args:
        tool_context: The tool context from ADK

    Returns:
        str: Confirmation message

    Example:
        User: "Quiero consultar información de otro estudiante"
        Agent calls: clear_student_identifier(tool_context)
    """
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)

    success = session_manager.clear_session(session_id)

    if success:
        return "He eliminado la identificación almacenada. Por favor proporciona el nuevo número de documento o correo electrónico."
    else:
        return "No había ninguna identificación almacenada."


def check_has_student_identifier(tool_context: ToolContext) -> str:
    """
    Check if we have a student identifier stored in the current session.

    This is useful to determine if we need to ask the user for their
    identification before performing queries.

    Args:
        tool_context: The tool context from ADK

    Returns:
        str: "yes" if identifier exists, "no" otherwise

    Example:
        Agent calls: check_has_student_identifier(tool_context)
        Returns: "yes" or "no"
    """
    session_manager = get_session_manager()
    session_id = get_session_id(tool_context)

    has_id = session_manager.has_identifier(session_id)

    return "yes" if has_id else "no"
