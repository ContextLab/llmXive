"""
PSS‑10 and PANAS questionnaire web interface.

This Flask application provides two endpoints:
  * GET  /questionnaire/<participant_id>
    Returns a simple HTML page containing the PSS‑10 and PANAS questionnaires.
  * POST /questionnaire/submit
    Accepts a JSON payload with the participant's responses, validates the data,
    and appends the results to ``data/raw/questionnaire_responses.csv`` as
    MeasurementRecord entries that conform to ``contracts/dataset.schema.yaml``.

The CSV schema (see ``contracts/dataset.schema.yaml``) requires the following
columns:
  - id:                unique identifier for the record
  - participant_id:    e.g. ``P001``
  - phase:             ``baseline`` or ``post``
  - metric_type:       one of ``pss10_total``, ``panas_positive``, ``panas_negative``
  - value:             numeric score
  - timestamp:         ISO‑8601 UTC datetime string
  - session_type:      mirrors ``phase``
"""
import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, render_template_string, abort

# Paths helper – uses llmxive_toolkit to ensure directories exist
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

app = Flask(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _csv_path() -> Path:
    """Return the Path object for the questionnaire responses CSV."""
    # The specification requires the file to live under ``data/raw``.
    return paths.data("raw", "questionnaire_responses.csv")

def _ensure_csv():
    """Create the CSV file with a header if it does not exist."""
    csv_file = _csv_path()
    if not csv_file.exists():
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        with csv_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id",
                "participant_id",
                "phase",
                "metric_type",
                "value",
                "timestamp",
                "session_type"
            ])
        log.info(f"Created questionnaire responses file at {csv_file}")

def _append_record(participant_id: str, phase: str, metric_type: str, value: float):
    """Append a single measurement record to the CSV."""
    _ensure_csv()
    record_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    row = [
        record_id,
        participant_id,
        phase,
        metric_type,
        f"{value:.4f}",
        timestamp,
        phase  # session_type mirrors phase
    ]
    with _csv_path().open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)
    log.debug(f"Wrote {metric_type} record for {participant_id}")

# ----------------------------------------------------------------------
# HTML template (very lightweight – no external assets)
# ----------------------------------------------------------------------
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>PSS‑10 & PANAS Questionnaire</title>
</head>
<body>
    <h1>Digital Decluttering Study – Questionnaires</h1>
    <p>Participant ID: <strong>{{ participant_id }}</strong></p>

    <form id="questionnaire-form">
        <h2>PSS‑10 (Perceived Stress Scale – 10 items)</h2>
        {% for i in range(1, 11) %}
            <label>Item {{ i }} (0‑4): 
                <input type="number" name="pss{{ i }}" min="0" max="4" required>
            </label><br>
        {% endfor %}

        <h2>PANAS (Positive and Negative Affect Schedule)</h2>
        <p>Positive Affect (PA) – 10 items</p>
        {% for i in range(1, 11) %}
            <label>PA {{ i }} (1‑5): 
                <input type="number" name="pa{{ i }}" min="1" max="5" required>
            </label><br>
        {% endfor %}

        <p>Negative Affect (NA) – 10 items</p>
        {% for i in range(1, 11) %}
            <label>NA {{ i }} (1‑5): 
                <input type="number" name="na{{ i }}" min="1" max="5" required>
            </label><br>
        {% endfor %}

        <br>
        <button type="button" onclick="submitData()">Submit</button>
    </form>

    <script>
    async function submitData() {
        const form = document.getElementById('questionnaire-form');
        const data = new FormData(form);
        const participant_id = "{{ participant_id }}";
        const phase = "baseline"; // The client can change this if needed

        // Compute scores
        let pss_total = 0;
        for (let i = 1; i <= 10; i++) {
            pss_total += Number(data.get('pss' + i));
        }

        let pa_total = 0;
        for (let i = 1; i <= 10; i++) {
            pa_total += Number(data.get('pa' + i));
        }

        let na_total = 0;
        for (let i = 1; i <= 10; i++) {
            na_total += Number(data.get('na' + i));
        }

        const payload = {
            participant_id,
            phase,
            responses: {
                pss10_total: pss_total,
                panas_positive: pa_total,
                panas_negative: na_total
            }
        };

        const resp = await fetch('/questionnaire/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await resp.json();
        if (resp.ok) {
            alert('Responses saved successfully!');
        } else {
            alert('Error: ' + (result.error || 'unknown'));
        }
    }
    </script>
</body>
</html>
"""

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route("/questionnaire/<participant_id>", methods=["GET"])
def questionnaire_page(participant_id: str):
    """
    Render a minimal HTML page containing the PSS‑10 and PANAS questionnaires.
    The page posts JSON to ``/questionnaire/submit``.
    """
    if not participant_id or not participant_id.startswith("P"):
        abort(400, description="Invalid participant ID")
    return render_template_string(HTML_TEMPLATE, participant_id=participant_id)

@app.route("/questionnaire/submit", methods=["POST"])
def submit_questionnaire():
    """
    Accept a JSON payload:

    {
        "participant_id": "P001",
        "phase": "baseline",
        "responses": {
            "pss10_total": 23,
            "panas_positive": 34,
            "panas_negative": 12
        }
    }

    The endpoint validates the payload and appends three rows to the CSV.
    """
    if not request.is_json:
        return jsonify(error="Request must be JSON"), 400

    payload = request.get_json()
    required_top = {"participant_id", "phase", "responses"}
    if not required_top.issubset(payload):
        return jsonify(error="Missing required top‑level fields"), 400

    participant_id = payload["participant_id"]
    phase = payload["phase"]
    responses = payload["responses"]

    # Basic validation
    if not isinstance(participant_id, str) or not participant_id.startswith("P"):
        return jsonify(error="Invalid participant_id"), 400
    if phase not in {"baseline", "post"}:
        return jsonify(error="Invalid phase; must be 'baseline' or 'post'"), 400

    # Expected response keys
    expected_keys = {"pss10_total", "panas_positive", "panas_negative"}
    if set(responses.keys()) != expected_keys:
        return jsonify(error="Responses must contain exactly pss10_total, panas_positive, panas_negative"), 400

    try:
        pss_val = float(responses["pss10_total"])
        pa_val = float(responses["panas_positive"])
        na_val = float(responses["panas_negative"])
    except (ValueError, TypeError):
        return jsonify(error="All scores must be numeric"), 400

    # Write to CSV – three separate MeasurementRecord rows
    _append_record(participant_id, phase, "pss10_total", pss_val)
    _append_record(participant_id, phase, "panas_positive", pa_val)
    _append_record(participant_id, phase, "panas_negative", na_val)

    log.info(f"Saved questionnaire responses for {participant_id} (phase={phase})")
    return jsonify(message="Questionnaire responses recorded"), 200

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Running directly starts the Flask development server.
    # In production the app would be served via a WSGI server.
    app.run(host="0.0.0.0", port=5000, debug=False)
