from google.adk.agents import Agent
from .prompt import return_instructions_root
#from callback_logging import log_query_to_model, log_model_response

from .tools import (
    get_student_info,
    get_payment_status,
    get_enrollment_status,
    get_academic_grades,
    set_student_identifier,
    get_stored_student_identifier,
    clear_student_identifier,
    check_has_student_identifier,
    generate_certification,
)

from .sub_agents import (
    search_esic_information,
    search_web,
)

root_agent = Agent(
    name="education_assistant",
    model="gemini-2.0-flash", # Gemini 2.5 Flash supports Live API
    instruction=return_instructions_root(),
    description="An assistant for education care",
    #before_model_callback=log_query_to_model,
    #after_model_callback=log_model_response,
    tools=[
        # Web search tools (use for ESIC information, program details, admission process, etc.)
        search_esic_information,  # Prioritizes ESIC official websites
        search_web,                # General web search
        # Student identification tools (use these first!)
        check_has_student_identifier,
        set_student_identifier,
        get_stored_student_identifier,
        clear_student_identifier,
        # Student information query tools (require identifier to be set)
        get_student_info,
        get_payment_status,
        get_enrollment_status,
        get_academic_grades,
        # Certification generation
        generate_certification,
    ]
)