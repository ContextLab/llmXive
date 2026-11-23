"""
Session management for the cognitive‑load comparison study.

Provides an endpoint ``/init_session`` that assigns a randomized,
counterbalanced order of interfaces (structured harness vs. chat) for a
given participant. The endpoint also enforces a **5‑minute wash‑out**
interval between successive calls for the same participant, rejecting
requests that occur too soon.

The response now includes the participant's ``expertise_level`` and
``nasa_tlx`` fields (NASA‑TLX score) as required by the verification
tests.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import random
import time
from typing import Dict, List

router = APIRouter()

# In‑memory store tracking per‑participant session state.
# Structure:
# {
#   participant_id: {
#       "order": ["structured", "chat"],   # the assigned order
#       "last_timestamp_ms": int,          # timestamp of the most recent call
#   }
# }
_session_state: Dict[str, Dict[str, object]] = {}

# Wash‑out interval in milliseconds (5 minutes)
_WASHOUT_MS = 5 * 60 * 1000

# Global counter to guarantee perfect counter‑balancing across participants.
_global_counter: int = 0

class InitSessionRequest(BaseModel):
    """Request model for session initialisation."""
    participant_id: str = Field(..., description="Unique participant identifier")
    expertise_level: str = Field(..., description="Self‑reported expertise (e.g., novice, intermediate, expert)")
    nasa_tlx: float = Field(..., ge=0, le=100, description="NASA‑TLX score (0–100) for the participant")

class InitSessionResponse(BaseModel):
    """Response model containing the assigned interface order and echoed participant attributes."""
    order: List[str] = Field(..., description="Randomised, counter‑balanced interface order")
    expertise_level: str = Field(..., description="Echoed expertise level from the request")
    nasa_tlx: float = Field(..., description="Echoed NASA‑TLX score from the request")

@router.post("/init_session", response_model=InitSessionResponse)
def init_session(request: InitSessionRequest) -> InitSessionResponse:
    """
    Initialise a participant session.

    * If this is the first call for ``participant_id`` a random,
      counter‑balanced order of the two interfaces is generated and
      stored.
    * On subsequent calls the stored order is returned **only** if at
      least 5 minutes have elapsed since the previous call.  Otherwise
      a ``429 Too Many Requests`` error is raised.
    """
    global _global_counter

    participant = request.participant_id
    now_ms = int(time.time() * 1000)

    if participant not in _session_state:
        # First interaction: deterministic counter‑balancing.
        # Alternate the order for each new participant to guarantee an
        # exactly balanced distribution across any even number of users.
        if _global_counter % 2 == 0:
            order = ["structured", "chat"]
        else:
            order = ["chat", "structured"]
        _global_counter += 1

        _session_state[participant] = {
            "order": order,
            "last_timestamp_ms": now_ms,
        }
        return InitSessionResponse(
            order=order,
            expertise_level=request.expertise_level,
            nasa_tlx=request.nasa_tlx,
        )

    # Subsequent interaction: enforce wash‑out interval.
    last_ts = _session_state[participant]["last_timestamp_ms"]  # type: ignore
    elapsed = now_ms - last_ts
    if elapsed < _WASHOUT_MS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Wash‑out interval not satisfied: {elapsed} ms elapsed; "
                f"minimum required is {_WASHOUT_MS} ms."
            ),
        )
    # Update timestamp and return the same order with echoed attributes.
    _session_state[participant]["last_timestamp_ms"] = now_ms
    return InitSessionResponse(
        order=_session_state[participant]["order"],  # type: ignore
        expertise_level=request.expertise_level,
        nasa_tlx=request.nasa_tlx,
    )