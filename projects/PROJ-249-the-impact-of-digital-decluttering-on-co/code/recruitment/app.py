"""
Minimal Flask application for participant recruitment.

Endpoint:
  POST /register
    - Accepts JSON payload with optional demographic fields.
    - Generates a unique participant ID of the form "P###".
    - Records the participant in `data/raw/participants.csv`.
    - Returns JSON with the generated participant_id and enrollment_date.
"""
from flask import Flask, request, jsonify
import csv
import json
from pathlib import Path
from datetime import datetime
import re

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

app = Flask(__name__)

PARTICIPANT_CSV = paths.data("raw", "participants.csv")

ID_PATTERN = re.compile(r"^P\d{3}$")

def _ensure_csv_exists():
    """Create the CSV file with a header if it does not already exist."""
    if not PARTICIPANT_CSV.exists():
        PARTICIPANT_CSV.parent.mkdir(parents=True, exist_ok=True)
        with PARTICIPANT_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id", "demographics", "enrollment_date"])
            writer.writeheader()
            log.info(f"Created participants file at {PARTICIPANT_CSV}")

def _load_existing_ids():
    """Return a set of participant IDs already present in the CSV."""
    ids = set()
    if PARTICIPANT_CSV.exists():
        with PARTICIPANT_CSV.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("participant_id")
                if pid:
                    ids.add(pid)
    return ids

def _generate_new_id(existing_ids):
    """Generate the next sequential participant ID (P001, P002, ...)."""
    max_num = 0
    for pid in existing_ids:
        match = ID_PATTERN.match(pid)
        if match:
            num = int(pid[1:])
            if num > max_num:
                max_num = num
    new_num = max_num + 1
    new_id = f"P{new_num:03d}"
    return new_id

@app.route("/register", methods=["POST"])
def register_participant():
    """
    Register a new participant.

    Expected JSON payload (all fields optional):
        {
            "demographics": {
                "age": 30,
                "gender": "female",
                ...
            }
        }
    """
    data = request.get_json(silent=True) or {}
    demographics = data.get("demographics", {})

    # Ensure the CSV file exists and load existing IDs
    _ensure_csv_exists()
    existing_ids = _load_existing_ids()
    participant_id = _generate_new_id(existing_ids)

    # Validate the generated ID matches the required pattern
    if not ID_PATTERN.fullmatch(participant_id):
        log.error(f"Generated participant ID does not match pattern: {participant_id}")
        return jsonify({"error": "Internal ID generation error"}), 500

    enrollment_date = datetime.utcnow().date().isoformat()
    # Store demographics as a JSON string for simplicity
    demographics_str = "" if not demographics else json.dumps(demographics, ensure_ascii=False)

    # Append the new participant to the CSV
    with PARTICIPANT_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["participant_id", "demographics", "enrollment_date"])
        writer.writerow({
            "participant_id": participant_id,
            "demographics": demographics_str,
            "enrollment_date": enrollment_date
        })

    log.info(f"Registered new participant: {participant_id}")

    return jsonify({
        "participant_id": participant_id,
        "enrollment_date": enrollment_date
    }), 201

if __name__ == "__main__":
    # Running directly starts a development server on localhost.
    # In production or testing environments the Flask app is imported
    # and used via the WSGI interface.
    app.run(host="0.0.0.0", port=5000, debug=False)