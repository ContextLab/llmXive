"""
Session management for the cognitive‑load comparison study.

Provides an endpoint ``/init_session`` that assigns a randomized,
counterbalanced order of interfaces (structured harness vs. chat) for a
given participant. The order is returned as a JSON list, e.g.
``["structured", "chat"]`` or ``["chat", "structured"]``.
"""

from fastapi import APIRouter
from pydantic import BaseModel
import random

router = APIRouter()


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

    The function randomly shuffles the two interface identifiers,
    ensuring that across many participants the order is counterbalanced.
    """
    # Deterministic randomisation per participant can be achieved by
    # seeding with the participant_id hash, but for simplicity we rely on
    # the global PRNG – the overall distribution will be balanced.
    order = ["structured", "chat"]
    random.shuffle(order)
    return InitSessionResponse(order=order)
