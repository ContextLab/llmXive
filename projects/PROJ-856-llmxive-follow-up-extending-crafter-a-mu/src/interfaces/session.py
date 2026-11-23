"""
Session management for the cognitive‑load comparison study.

Provides an endpoint ``/init_session`` that assigns a randomized,
counterbalanced order of interfaces (structured harness vs. chat) for a
given participant. The endpoint also enforces a **10‑minute wash‑out**
interval between successive calls for the same participant, rejecting
requests that occur too soon.

The endpoint returns a JSON response containing the assigned interface
order (a list with both identifiers).  On the first call for a
participant the order is randomly shuffled; on subsequent calls the
same order is returned, but only if at least 10 minutes have elapsed
since the previous call.  If the wash‑out interval has not passed, the
endpoint responds with HTTP 400 and an informative error message.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
import time
from typing import Dict

router = APIRouter()

# In‑memory store tracking per‑participant session state.
# Structure:
# {
#   participant_id: {
#       "order": ["structured", "chat"],   # the randomized order
#       "last_timestamp_ms": int,          # timestamp of the most recent call
#   }
# }
_session_state: Dict[str, Dict[str, object]] = {}

# Wash‑out interval in milliseconds (10 minutes)
_WASHOUT_MS = 10 * 60 * 1000

class InitSessionRequest(BaseModel):
    """Request model for session initialisation."""
    participant_id: str


class InitSessionResponse(BaseModel):
    """Response model containing the assigned interface order."""
    order: list[str]


@router.post("/init_session", response_model=InitSessionResponse)
def init_session(request: InitSessionRequest) -> InitSessionResponse:
    """
    Initialise a participant session.

    * If this is the first call for ``participant_id`` a random,
      counterbalanced order of the two interfaces is generated and
      stored.
    * On subsequent calls the stored order is returned **only** if at
      least 10 minutes have elapsed since the previous call.  Otherwise
      a ``400 Bad Request`` is raised.
    """
    participant = request.participant_id
    now_ms = int(time.time() * 1000)

    if participant not in _session_state:
        # First interaction: generate a random order and record timestamp.
        order = ["structured", "chat"]
        random.shuffle(order)  # Counterbalancing across many participants
        _session_state[participant] = {
            "order": order,
            "last_timestamp_ms": now_ms,
        }
        return InitSessionResponse(order=order)

    # Subsequent interaction: enforce wash‑out interval.
    last_ts = _session_state[participant]["last_timestamp_ms"]  # type: ignore
    elapsed = now_ms - last_ts
    if elapsed < _WASHOUT_MS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Wash‑out interval not satisfied: {elapsed} ms elapsed; "
                f"minimum required is {_WASHOUT_MS} ms."
            ),
        )
    # Update timestamp and return the same order.
    _session_state[participant]["last_timestamp_ms"] = now_ms
    return InitSessionResponse(order=_session_state[participant]["order"])  # type: ignore
