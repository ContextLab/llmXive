"""
Session Server for the visual complexity experiment.

This module provides a Flask application that:
1. Loads the counterbalanced stimulus order from
   `data/processed/counterbalance_order.json`.
2. Exposes an endpoint to retrieve the full counterbalance mapping.
3. Allows a participant to start a session, enforces the exact stimulus
   order for that participant, and records the permutation ID used.
4. Persists a lightweight CSV log of each participant's session
   (`data/measurements/raw/participant_sessions.csv`).

The implementation is deliberately lightweight – it does **not** embed any
experiment UI. The UI is handled elsewhere (e.g., Streamlit). The server
only validates ordering and records provenance, which satisfies the
verification test `test_server_loads_counterbalance`.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from flask import Flask, request, jsonify, abort

# Project‑wide utilities
from src.config import ensure_directories_exist, get_relative_path

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
COUNTERBALANCE_JSON = Path("data/processed/counterbalance_order.json")
PARTICIPANT_SESSIONS_CSV = Path(
    "data/measurements/raw/participant_sessions.csv"
)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_counterbalance() -> Dict[str, List[str]]:
    """
    Load the counterbalanced stimulus order file.

    Returns
    -------
    dict
        Mapping from ``permutation_id`` (str) to a list of stimulus IDs
        (list of str). The JSON file is expected to have the structure:
        {
            "perm_001": ["stim1.jpg", "stim2.jpg", ...],
            "perm_002": [...]
        }
    Raises
    ------
    FileNotFoundError
        If the JSON file does not exist.
    json.JSONDecodeError
        If the file cannot be parsed as valid JSON.
    """
    if not COUNTERBALANCE_JSON.is_file():
        raise FileNotFoundError(
            f"Counterbalance file not found: {COUNTERBALANCE_JSON}"
        )
    with COUNTERBALANCE_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(
            f"Counterbalance JSON must be a dict, got {type(data)}"
        )
    # Ensure all values are lists of strings
    for key, val in data.items():
        if not isinstance(val, list) or not all(isinstance(v, str) for v in val):
            raise ValueError(
                f"Invalid entry for permutation '{key}': must be list of strings."
            )
    return data

def record_participant_session(
    participant_id: str, permutation_id: str
) -> None:
    """
    Append a record for a participant's session to the CSV log.

    Parameters
    ----------
    participant_id : str
        Unique identifier for the participant (e.g., UUID).
    permutation_id : str
        The permutation identifier assigned to this participant.
    """
    ensure_directories_exist(PARTICIPANT_SESSIONS_CSV.parent)
    file_exists = PARTICIPANT_SESSIONS_CSV.is_file()

    with PARTICIPANT_SESSIONS_CSV.open(
        "a", newline="", encoding="utf-8"
    ) as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["timestamp", "participant_id", "permutation_id"],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "participant_id": participant_id,
                "permutation_id": permutation_id,
            }
        )

# ----------------------------------------------------------------------
# Flask application
# ----------------------------------------------------------------------
app = Flask(__name__)

# Load counterbalance once at start‑up; failures are fatal – they surface
# immediately during import, which is desirable for the test suite.
COUNTERBALANCE_DATA = load_counterbalance()

@app.route("/counterbalance", methods=["GET"])
def get_counterbalance() -> Any:
    """
    Return the full counterbalance mapping as JSON.
    """
    return jsonify(COUNTERBALANCE_DATA)

@app.route("/session/<participant_id>", methods=["POST"])
def start_session(participant_id: str) -> Any:
    """
    Initialise a participant's session.

    Expected JSON payload:
    {
        "permutation_id": "<str>",
        "stimuli_order": ["stimX.jpg", "stimY.jpg", ...]   # optional
    }

    The server validates that the supplied ``stimuli_order`` (if provided)
    exactly matches the stored order for the given permutation. If the
    order is omitted, the server simply records the permutation assignment.

    Returns
    -------
    JSON with a ``status`` field.
    """
    if not request.is_json:
        abort(400, description="Request body must be JSON.")
    payload: Dict[str, Any] = request.get_json()

    permutation_id = payload.get("permutation_id")
    if not permutation_id:
        abort(400, description="Missing 'permutation_id' in payload.")

    if permutation_id not in COUNTERBALANCE_DATA:
        abort(400, description="Invalid permutation_id.")

    expected_order = COUNTERBALANCE_DATA[permutation_id]

    # If the client sends an explicit order, enforce exact match.
    provided_order = payload.get("stimuli_order")
    if provided_order is not None:
        if not isinstance(provided_order, list) or not all(
            isinstance(item, str) for item in provided_order
        ):
            abort(400, description="'stimuli_order' must be a list of strings.")
        if provided_order != expected_order:
            abort(
                400,
                description=(
                    "Provided stimuli order does not match the assigned permutation."
                ),
            )

    # Record the participant's assignment.
    record_participant_session(participant_id, permutation_id)

    return jsonify({"status": "session_started", "permutation_id": permutation_id})

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # The host/port are deliberately simple for CI environments.
    app.run(host="0.0.0.0", port=5000, debug=False)
