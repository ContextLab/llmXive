"""
FastAPI stub for the Chat Interface.

Mirrors the API surface of the structured harness for testing purposes.
Provides:
  * ``/init_session`` – shared session initialisation endpoint.
  * ``/edit`` – accepts a free‑form natural‑language instruction.
"""

from fastapi import FastAPI
from src.interfaces.session import router as session_router
from pydantic import BaseModel

app = FastAPI(title="Chat Interface")
# Include the shared session router
app.include_router(session_router)


class ChatEditRequest(BaseModel):
    """Placeholder model for a chat‑style edit payload."""
    figure_id: str
    instruction: str  # e.g., "Make the axis red"


@app.post("/edit")
def edit_endpoint(request: ChatEditRequest) -> dict:
    """
    Receive a chat‑style edit request.

    This stub simply acknowledges the instruction. Real logic would
    forward the text to an LLM, apply the resulting changes, and
    return the updated figure.
    """
    return {"status": "ok", "message": "Chat instruction received"}