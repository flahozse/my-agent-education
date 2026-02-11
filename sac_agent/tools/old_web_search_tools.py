"""Web search tools for ESIC information."""

from google.adk.tools import google_search


def search_esic_information(query: str, focus_domain: bool = True) -> str:
    """
    Search for information about ESIC programs, courses, admission process, and academic information.

    Use this tool when users ask about:
    - Program details (Master's programs, Executive programs, In-Company training)
    - Study plans, methodologies, and faculty
    - Start dates, academic calendars, and schedules
    - Admission processes, prices, and financing options
    - Campus information, facilities, and services
    - Any public information about ESIC not available in the student database

    Args:
        query: The search query about ESIC. Be specific and include "ESIC" in the query.
        focus_domain: If True, prioritizes results from official ESIC websites (esic.edu, esic.co)

    Returns:
        Search results with information about ESIC

    Examples:
        - search_esic_information("ESIC Master en Marketing Digital plan de estudios")
        - search_esic_information("ESIC Medellín fechas de inicio programas ejecutivos")
        - search_esic_information("ESIC proceso de admisión requisitos")
    """
    # If focus_domain is True, add site restriction to search primarily in ESIC domains
    if focus_domain and "site:" not in query.lower():
        # Search in ESIC domains: esic.edu (Spain), esic.co (Colombia)
        enhanced_query = f"{query} (site:esic.edu OR site:esic.co)"
    else:
        enhanced_query = query

    # Use Google's search tool to perform the search
    results = google_search(enhanced_query)

    return results


# Alias for direct google search (for cases where ESIC-specific search is not needed)
def search_web(query: str) -> str:
    """
    Perform a general web search. Use this when you need information beyond ESIC-specific content.

    For ESIC-related queries, prefer using search_esic_information() instead.

    Args:
        query: The search query

    Returns:
        Search results
    """
    return google_search(query)
