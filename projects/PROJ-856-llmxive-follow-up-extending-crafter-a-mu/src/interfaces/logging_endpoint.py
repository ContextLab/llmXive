"""
logging_endpoint.py
-------------------

FastAPI endpoint that exposes millisecond‑precision interaction logging.
It forwards the request payload to :func:`src.logger.interaction_logger.log_interaction`.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from src.logger.interaction_logger import log_interaction

app = FastAPI()


class LogInteractionRequest(BaseModel):
    """Schema for the ``/log_interaction`` POST request."""
    participant_id: str
    figure_id: str
    interface: str
    payload: Dict[str, Any]
    iteration: int = Field(..., ge=1, description="1‑based edit attempt number")
    subjective_load: Optional[float] = Field(
        None, ge=0, le=100, description="NASA‑TLX score (0‑100)"
    )


@app.post("/log_interaction")
def log_interaction_endpoint(request: LogInteractionRequest):
    """
    Record a single interaction.

    The function forwards the request data to the interaction logger.
    If the logger raises an exception we convert it to a 500 response.
    """
    try:
        log_interaction(
            participant_id=request.participant_id,
            figure_id=request.figure_id,
            interface=request.interface,
            payload=request.payload,
            iteration=request.iteration,
            subjective_load=request.subjective_load,
        )
    except Exception as exc:  # pragma: no cover – unexpected failures
        raise HTTPException(status_code=500, detail=str(exc))

    return {"detail": "logged"}
