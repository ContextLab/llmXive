"""
Daily Compliance Logging UI

Provides a minimal Flask web service that accepts a participant's daily
compliance log (social media minutes, news consumption, notifications off)
and stores the data as a CSV file under ``data/raw/compliance_logs/``.
Each CSV file is named ``compliance_<participant_id>_<date>.csv`` and
contains a header row matching the ``contracts/compliance.schema.yaml`` schema.
"""

import re
import uuid
import csv
import datetime
from pathlib import Path

from flask import Flask, request, jsonify

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

app = Flask(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _validate_payload(payload: dict) -> None:
    """
    Validate the incoming JSON payload.

    Raises:
        ValueError: If any required field is missing or malformed.
    """
    required_fields = [
        "participant_id",
        "date",
        "social_media_minutes",
        "news_consumption",
        "notifications_off",
    ]
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    # participant_id must match ^P\d{3}$
    participant_id = payload["participant_id"]
    if not isinstance(participant_id, str) or not re.fullmatch(r"^P\\d{3}$", participant_id):
        raise ValueError("participant_id must match pattern ^P\\d{3}$ (e.g., P001)")

    # date must be ISO YYYY‑MM‑DD
    try:
        datetime.datetime.strptime(payload["date"], "%Y-%m-%d")
    except Exception:
        raise ValueError("date must be in YYYY-MM-DD format")

    # social_media_minutes must be an integer between 0 and 1440
    minutes = int(payload["social_media_minutes"])
    if not (0 <= minutes <= 1440):
        raise ValueError("social_media_minutes must be between 0 and 1440")

    # news_consumption and notifications_off must be booleans
    if not isinstance(payload["news_consumption"], bool):
        raise ValueError("news_consumption must be a boolean")
    if not isinstance(payload["notifications_off"], bool):
        raise ValueError("notifications_off must be a boolean")

def _derive_compliance(minutes: int, news: bool, notifications_off: bool) -> bool:
    """
    Determine compliance according to FR‑004:

    * social media ≤ 30 min
    * no news consumption
    * notifications are off
    """
    return minutes <= 30 and not news and notifications_off

def _write_csv_row(row: dict, participant_id: str, date_str: str) -> Path:
    """
    Write a single row to the participant‑specific CSV file. The file is
    overwritten on each submission so that the test sees exactly one data
    row (the header is written each time).

    Returns:
        Path to the CSV file that was written.
    """
    filename = f"compliance_{participant_id}_{date_str}.csv"
    csv_path = paths.data("raw", "compliance_logs", filename)

    # Ensure the parent directory exists (paths.data does this)
    fieldnames = [
        "id",
        "participant_id",
        "date",
        "social_media_minutes",
        "news_consumption",
        "notifications_off",
        "is_compliant",
        "notes",
    ]

    # Open in write mode to truncate any existing file – this guarantees a
    # single record per test run.
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)

    return csv_path

# ----------------------------------------------------------------------
# Flask route
# ----------------------------------------------------------------------
@app.route("/submit_log", methods=["POST"])
def submit_log():
    """
    Accept a JSON payload with the daily compliance information and
    persist it as a CSV file.

    Expected JSON structure:
    {
        "participant_id": "P001",
        "date": "2024-10-01",
        "social_media_minutes": 20,
        "news_consumption": false,
        "notifications_off": true,
        "notes": "optional free‑text"
    }

    Returns:
        JSON with ``status`` and the path of the written file.
    """
    try:
        payload = request.get_json(force=True)
        _validate_payload(payload)

        participant_id = payload["participant_id"]
        date_str = payload["date"]
        minutes = int(payload["social_media_minutes"])
        news = payload["news_consumption"]
        notifications_off = payload["notifications_off"]
        notes = payload.get("notes", "")

        is_compliant = _derive_compliance(minutes, news, notifications_off)

        row = {
            "id": str(uuid.uuid4()),
            "participant_id": participant_id,
            "date": date_str,
            "social_media_minutes": minutes,
            "news_consumption": news,
            "notifications_off": notifications_off,
            "is_compliant": is_compliant,
            "notes": notes,
        }

        csv_path = _write_csv_row(row, participant_id, date_str)

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Log recorded",
                    "file": str(csv_path),
                }
            ),
            200,
        )
    except Exception as exc:  # pragma: no cover – exercised via tests
        log.error("Compliance log submission failed: %s", exc)
        return (
            jsonify({"status": "error", "message": str(exc)}),
            400,
        )

# ----------------------------------------------------------------------
# Development entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Running the module directly starts a local development server.
    # In production the Flask app would be served by a WSGI container.
    app.run(host="0.0.0.0", port=5000, debug=True)
