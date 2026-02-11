"""Web search sub-agent for ESIC information and general web searches."""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import ToolContext


# Sub-agent specialized in web searches
web_search_agent = Agent(
    name="web_search_specialist",
    model="gemini-2.0-flash",
    instruction="""You are a web search specialist. Your role is to search the web and return relevant,
    concise information based on the user's query. Focus on providing accurate and up-to-date information.

    When searching for ESIC-related information, prioritize results from official ESIC websites.
    Always cite your sources when providing information.""",
    description="A specialized agent for performing web searches",
    tools=[google_search]  # Only search tools allowed together
)


async def search_esic_information(query: str, tool_context: ToolContext, focus_domain: bool = True) -> str:
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

    # Use the web search sub-agent to perform the search
    search_prompt = f"""Search for the following information: {enhanced_query}

    Provide a concise summary of the most relevant findings, including:
    - Key information found
    - Sources (URLs)
    - Any relevant dates or specific details
    """

    agent_tool = AgentTool(agent=web_search_agent)
    result = await agent_tool.run_async(
        args={"request": search_prompt},
        tool_context=tool_context
    )
    return result


async def search_web(query: str, tool_context: ToolContext) -> str:
    """
    Perform a general web search. Use this when you need information beyond ESIC-specific content.

    For ESIC-related queries, prefer using search_esic_information() instead.

    Args:
        query: The search query

    Returns:
        Search results with relevant information
    """
    search_prompt = f"""Search for the following information: {query}

    Provide a concise summary of the most relevant findings, including sources (URLs)
    and any important details."""

    agent_tool = AgentTool(agent=web_search_agent)
    result = await agent_tool.run_async(
        args={"request": search_prompt},
        tool_context=tool_context
    )
    return result
