from fastapi import FastAPI, APIRouter, HTTPException
from .models import CustomerInquiryRequest, CustomerInquiryResponse
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from .agents.customer_agent import CustomerAgentOrchestrator
from google.genai import types
import json
import re
import uuid
from contextlib import asynccontextmanager

# SQLlite DB init
DB_URL = "sqlite:///./multi_agent_data.db"
APP_NAME = "CustomerInquiryProcessor"

# Create a lifespan event to initialize and clean up the session service
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("Application starting up...")    
    # Initialize the DatabaseSessionService instance and store it in app.state
    try:
        app.state.session_service =DatabaseSessionService(db_url=DB_URL)
        print("Database session service initialized successfully.")
    except Exception as e:
        print("Database session service initialized failed.")
        print(e)
    
    yield # This is where the application runs, handling requests
    # Shutdown code
    print("Application shutting down...")
    
# FastAPI application setup
app = FastAPI(
    title="Customer Inquiry Processor",
    description="Multi-agent system for processing customer inquiries",
    version="1.0.0",
    lifespan=lifespan,
)
# Initializing the Orchestrator
customer_agent = CustomerAgentOrchestrator()
router = APIRouter()

@router.post("/process-inquiry", response_model=CustomerInquiryResponse)
async def process_customer_inquiry(
    request_body: CustomerInquiryRequest
):
    """
    Endpoint to interact with the multi-agent ADK system.
    request_body: {"customer_inquiry": "My internet is not working after the update, please help!"}
    """
    # Extract customer inquiry from request
    customer_inquiry = request_body.customer_inquiry
    
    # Generate unique IDs for this processing session
    unique_id = str(uuid.uuid4())
    session_id = unique_id
    user_id = unique_id

    try:
        # Get database session service from application state
        session_service: DatabaseSessionService = app.state.session_service
        
        # Try to get existing session or create new one
        current_session = None
        try:
            current_session = await session_service.get_session(
                app_name=APP_NAME,
                user_id = user_id,
                session_id=session_id,
            )
        except Exception as e:
            print(f"Existing Session retrieval failed for session_id='{session_id}' "
                    f"and user_uid='{user_id}': {e}")
        
        # If no session found, creating new session
        if current_session is None:
            current_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
        else:
            print(f"Existing session '{session_id}'has been found. Resuming session.")

        # Initialize the ADK Runner with our multi-agent pipeline
        runner = Runner(
            app_name=APP_NAME,
            agent=customer_agent.root_agent,
            session_service = session_service,
        )


        # Format the user query as a structured message using the google genais content types
        user_message = types.Content(
            role="user", parts=[types.Part.from_text(text=customer_inquiry)]
        )
        
        # Run the agent asynchronously
        events = runner.run_async(
            user_id = user_id,
            session_id = session_id,
            new_message = user_message,
        )

        # Process events to find the final response 
        final_response = None
        last_event_content = None
        async for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    last_event_content = event.content.parts[0].text

        if last_event_content:
            final_response = last_event_content
        else:
            print("No final response event found from the Sequential Agent.")
    
        # Parse the JSON response from agents
        if final_response is None:
            raise HTTPException(status_code=500, detail="No response received from agent.")
        
        # Clean up Markdown code block if it exists
        # This handles responses like: ```json\n{ ... }\n```
        cleaned_response = re.sub(r"^```(?:json)?\n|```$", "", final_response.strip(), flags=re.IGNORECASE)
        
        # Loading the cleaned JSON
        try:
            response_data = json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Agent response is not valid JSON.")
        
        # Return the structured response using your Pydantic model
        return CustomerInquiryResponse(
            original_inquiry=response_data.get("original_inquiry", ""),
            category=response_data.get("category", ""),
            suggested_response=response_data.get("suggested_response", "")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process agent query: {e}")
    
# Include the router in the FastAPI app
app.include_router(router, prefix="/api", tags=["Customer Inquiry Processing"])