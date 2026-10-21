"""
Chat Interface
=============

Provides a FastAPI endpoint for receiving natural‑language edit requests.
The endpoint mirrors the structured harness API so that the same
logging machinery can be reused.  It simply records the interaction and
returns a generic success response – the actual LLM processing is out of
scope for the current verification tests.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from src.logger.interaction_logger import log_interaction

# FastAPI application instance for the chat interface
app = FastAPI()

class ChatEditRequest(BaseModel):
    """
    Request model for a chat‑style edit interaction.

    The fields are identical to ``EditRequest`` in the structured harness
    to keep the logging contract consistent.
    """
    participant_id: str
    figure_id: str
    interface: str
    payload: dict
    iteration: int

@app.post("/edit")
def edit_endpoint(request: ChatEditRequest):
    """
    FastAPI edit endpoint for the chat interface.

    Delegates to the same interaction logger used by the structured
    harness, guaranteeing that all required fields (including timestamps,
    task_start_ms, task_end_ms, and abort handling) are recorded.
    """
    log_interaction(
        participant_id=request.participant_id,
        figure_id=request.figure_id,
        interface=request.interface,
        payload=request.payload,
        iteration=request.iteration,
    )
    return {"status": "ok"}