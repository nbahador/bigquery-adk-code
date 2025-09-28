from data_agent_app.agent import get_insurance_claims_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import uuid
import interpretability_utils
import re
from typing import Dict

APP_NAME = "data_agent_app"
USER_ID = "insurance_analyst_101"

def validate_agent_response(response_text: str) -> Dict:
    """Smart validation that adapts to different response types"""
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check for completely empty responses
    if not response_text or len(response_text.strip()) < 5:
        validation_results['errors'].append("Response is empty or too short")
        validation_results['valid'] = False
        return validation_results
    
    # Check if it's meant to be a structured outlier analysis response
    is_outlier_analysis = any(keyword in response_text.upper() for keyword in [
        'OUTLIER', 'FLAGGED', 'BUSINESS RULE', 'TRIGGERED RULES', 'INTERPRETABILITY'
    ])
    
    if is_outlier_analysis:
        # For outlier analysis, expect structured format
        required_sections = ['SUMMARY:', 'TRIGGERED RULES:', 'CONFIDENCE:', 'RECOMMENDATION:']
        missing_sections = []
        
        for section in required_sections:
            if section not in response_text:
                missing_sections.append(section)
        
        if missing_sections:
            validation_results['warnings'].append(f"Structured response missing sections: {missing_sections}")
            # Don't mark as invalid - just warn
    
    # Check for obvious errors or system failures
    error_indicators = [
        "error occurred",
        "unable to retrieve",
        "failed to process",
        "timeout",
        "connection failed"
    ]
    
    for indicator in error_indicators:
        if indicator.lower() in response_text.lower():
            validation_results['errors'].append(f"Response indicates system error: {indicator}")
            validation_results['valid'] = False
    
    # Check for PII patterns
    pii_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email pattern
    ]
    
    for pattern in pii_patterns:
        if re.search(pattern, response_text):
            validation_results['warnings'].append("Potential PII detected in response")
    
    # Check for reasonable content length and structure
    if len(response_text.strip()) < 20:
        validation_results['warnings'].append("Response seems very short")
    
    # Check if response actually addresses the question (basic heuristic)
    question_keywords = [
        'claims', 'outlier', 'amount', 'procedure', 'diagnosis', 'state', 
        'provider', 'flagged', 'analysis', 'distribution'
    ]
    
    has_relevant_content = any(keyword.lower() in response_text.lower() 
                              for keyword in question_keywords)
    
    if not has_relevant_content:
        validation_results['warnings'].append("Response may not be relevant to insurance claims analysis")
    
    return validation_results

async def run_conversation(prompt: str):
    """Runs a conversation with the Insurance Claims agent using the ADK Runner."""
    
    session_service = InMemorySessionService()
    session_id = f"{APP_NAME}-{uuid.uuid4().hex[:8]}"
    root_agent = get_insurance_claims_agent()

    runner = Runner(
        agent=root_agent, app_name=APP_NAME, session_service=session_service
    )
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id
    )
    final_response_text = "Unable to retrieve final response."
    tool_calls = []

    try:
        # Run the agent and process the events as they are generated
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
        ):

            if (
                event.content
                and event.content.parts
                and event.content.parts[0].function_call
            ):

                func_call = event.content.parts[0].function_call

                tool_call = {
                    "tool_name": func_call.name,
                    "tool_input": dict(func_call.args),
                }
                tool_calls.append(tool_call)

            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                break

    except Exception as e:
        print(f"Error in run_conversation: {e}")
        final_response_text = f"An error occurred during the conversation: {e}"

    # Smart validation - only override truly problematic responses
    validation = validate_agent_response(final_response_text)
    
    if not validation['valid']:
        print(f"Response validation failed: {validation['errors']}")
        # Log the original response for debugging
        print(f"Original response was: {final_response_text[:200]}...")
        final_response_text = "Response validation failed. Please try again."
    elif validation['warnings']:
        # Log warnings but keep the response
        print(f"Response validation warnings: {validation['warnings']}")

    return {
        "response": final_response_text,
        "predicted_trajectory": tool_calls,
        "validation_results": validation
    }