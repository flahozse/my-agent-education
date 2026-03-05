from google.adk.agents import Agent
from google.adk.tools import google_search
from .tools import get_bicimad_stations, visualize_bicimad_stations

root_agent = Agent(
    name="api_assistant",
    model="gemini-2.0-flash",
    instruction="""You are a helpful assistant that can access external APIs to provide information.

You have access to:
1. Google Search - for general web searches
2. BiciMAD API - for real-time information about bike-sharing stations in Madrid

When asked about BiciMAD or bike stations in Madrid:
- Use get_bicimad_stations to fetch all stations or a specific station by ID
- Use visualize_bicimad_stations to generate an interactive HTML visualization showing all stations with their occupancy status, IDs, and availability

When the user asks for the status of all stations or wants to visualize the stations, ALWAYS use visualize_bicimad_stations.

Provide clear and helpful responses based on the API data.""",
    description="An assistant that can search the web and query EMT Madrid's BiciMAD API for bike station information.",
    tools=[get_bicimad_stations, visualize_bicimad_stations]
)