"""
Structured Harness Interface
============================

Provides a FastAPI endpoint for receiving structured edit requests.
Each request is logged via ``src.logger.interaction_logger.log_interaction``.
The endpoint validates the incoming JSON payload against the
``EditRequest`` Pydantic model, writes a log entry, and returns a simple
success response.

This implementation satisfies the integration tests which POST to
``/edit`` and expect a ``200 OK`` response and a correctly‑formatted
log entry.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from src.logger.interaction_logger import log_interaction

# FastAPI application instance
app = FastAPI()

class EditRequest(BaseModel):
    """
    Request model for a single edit interaction.

    Fields match the JSON payload used in the integration tests:
    - ``participant_id``: unique identifier for the participant/session.
    - ``figure_id``: identifier of the figure/task being edited.
    - ``interface``: either ``structured`` or ``chat`` (the endpoint does not
      enforce the enum – validation is performed by the logger schema).
    - ``payload``: the raw edit command (typed code) as a dict.
    - ``iteration``: 1‑based edit attempt counter.
    """
    participant_id: str
    figure_id: str
    interface: str
    payload: dict
    iteration: int

@app.post("/edit")
def edit_endpoint(request: EditRequest):
    """
    FastAPI edit endpoint.

    Logs the interaction and returns a minimal JSON payload indicating
    success. The logger handles task‑level start/end timestamps,
    abort detection, and writes a clean JSON‑Lines file
    ``data/logs/interactions_clean.jsonl``.
    """
    log_interaction(
        participant_id=request.participant_id,
        figure_id=request.figure_id,
        interface=request.interface,
        payload=request.payload,
        iteration=request.iteration,
    )
    return {"status": "ok"}
