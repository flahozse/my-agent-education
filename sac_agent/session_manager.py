"""Session manager for storing and retrieving student context.

This module provides functionality to persist student identification
(document number or email) across multiple interactions within a conversation,
avoiding the need to ask for it repeatedly.
"""

from typing import Optional, Dict
from datetime import datetime
from google.adk.tools import ToolContext


class StudentSessionManager:
    """
    Manages student session data across conversation turns.

    Stores student identifier (document number or email) and metadata
    to enable seamless access to BigQuery student information.
    """

    def __init__(self):
        """Initialize the session manager with an empty sessions dictionary."""
        self._sessions: Dict[str, Dict] = {}

    def set_student_identifier(
        self,
        session_id: str,
        identifier: str,
        identifier_type: str = "auto"
    ) -> bool:
        """
        Store the student identifier for a given session.

        Args:
            session_id: Unique session identifier (from ToolContext)
            identifier: The student's document number or email
            identifier_type: Type of identifier ("email", "document", or "auto")

        Returns:
            bool: True if successfully stored

        Example:
            manager.set_student_identifier("session_123", "juan@esic.edu", "email")
        """
        # Auto-detect identifier type if not specified
        if identifier_type == "auto":
            identifier_type = "email" if "@" in identifier else "document"

        self._sessions[session_id] = {
            "identifier": identifier.strip(),
            "identifier_type": identifier_type,
            "timestamp": datetime.now().isoformat(),
            "verified": False
        }

        return True

    def get_student_identifier(self, session_id: str) -> Optional[str]:
        """
        Retrieve the stored student identifier for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            Optional[str]: The student identifier if found, None otherwise

        Example:
            identifier = manager.get_student_identifier("session_123")
            # Returns: "juan@esic.edu"
        """
        session = self._sessions.get(session_id)
        if session:
            return session.get("identifier")
        return None

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve complete session information.

        Args:
            session_id: Unique session identifier

        Returns:
            Optional[Dict]: Session data including identifier, type, and timestamp
        """
        return self._sessions.get(session_id)

    def mark_verified(self, session_id: str) -> bool:
        """
        Mark a session as verified (after authentication check).

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if successfully marked as verified
        """
        session = self._sessions.get(session_id)
        if session:
            session["verified"] = True
            return True
        return False

    def is_verified(self, session_id: str) -> bool:
        """
        Check if a session has been verified.

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if verified, False otherwise
        """
        session = self._sessions.get(session_id)
        return session.get("verified", False) if session else False

    def clear_session(self, session_id: str) -> bool:
        """
        Clear session data for a given session.

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if session was found and cleared
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def has_identifier(self, session_id: str) -> bool:
        """
        Check if a session has a stored identifier.

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if identifier exists for this session
        """
        return session_id in self._sessions and bool(
            self._sessions[session_id].get("identifier")
        )


# Global session manager instance
_session_manager = StudentSessionManager()


def get_session_manager() -> StudentSessionManager:
    """
    Get the global session manager instance.

    Returns:
        StudentSessionManager: The global session manager
    """
    return _session_manager


def get_session_id(tool_context: ToolContext) -> str:
    """
    Extract or generate a session ID from the tool context.

    Args:
        tool_context: The ADK tool context

    Returns:
        str: A unique session identifier
    """
    # Use conversation ID or generate a fallback
    # ADK provides session info through the context
    if hasattr(tool_context, 'session_id'):
        return tool_context.session_id

    # Fallback: use a hash of the conversation context
    # This is a simplified version - in production, you'd want
    # a more robust session ID from the ADK framework
    return "default_session"
