"""
FastAPI stub for the Structured Harness interface.

Exposes two endpoints:
  * ``/init_session`` – imported from ``session.py`` for participant
    initialisation.
  * ``/edit`` – receives a JSON payload representing a typed edit and
    returns a generic success response. The endpoint is deliberately
    minimal because the full editing logic is outside the scope of this
    task.
"""

from fastapi import FastAPI
from src.interfaces.session import router as session_router
from pydantic import BaseModel

app = FastAPI(title="Structured Harness Interface")
# Include the shared session router
app.include_router(session_router)


class EditRequest(BaseModel):
    """Placeholder model for a structured edit payload."""
    figure_id: str
    edit_commands: list[dict]  # e.g., [{"action": "set_color", "target": "axis", "value": "red"}]


@app.post("/edit")
def edit_endpoint(request: EditRequest) -> dict:
    """
    Receive a structured edit request.

    The implementation is a stub – it simply acknowledges receipt.
    In a full system this would apply the commands to the figure and
    return the updated image or status.
    """
    return {"status": "ok", "message": "Edit received"}
