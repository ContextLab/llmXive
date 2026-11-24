"""
Integration test for the PSS‑10 / PANAS questionnaire endpoint.

The test starts the Flask app in testing mode, submits a well‑formed
JSON payload, and then checks that three rows have been written to
``data/raw/questionnaire_responses.csv``.  It also validates that the
CSV conforms to ``contracts/dataset.schema.yaml`` using jsonschema.
"""
import csv
import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

from code.web.questionnaires import pss_panas

# Load the JSON‑Schema for a MeasurementRecord (the contracts file
# defines a full dataset schema; we extract the single record definition).
SCHEMA_PATH = Path(__file__).parents[2] / "contracts" / "dataset.schema.yaml"
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    dataset_schema = json.load(f)

# The schema defines an array under the top‑level ``measurements`` key.
# For per‑row validation we extract the definition of a single record.
RECORD_SCHEMA = dataset_schema["definitions"]["MeasurementRecord"]

@pytest.fixture
def client():
    """Flask test client."""
    pss_panas.app.testing = True
    with pss_panas.app.test_client() as client:
        yield client

def test_questionnaire_submission_writes_csv(client, tmp_path, monkeypatch):
    # Use a temporary CSV location to avoid polluting the repo data folder.
    temp_csv = tmp_path / "questionnaire_responses.csv"
    monkeypatch.setattr(
        pss_panas,
        "_csv_path",
        lambda: temp_csv
    )

    payload = {
        "participant_id": "P123",
        "phase": "baseline",
        "responses": {
            "pss10_total": 22,
            "panas_positive": 35,
            "panas_negative": 12
        }
    }

    resp = client.post(
        "/questionnaire/submit",
        json=payload
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("message") == "Questionnaire responses recorded"

    # Verify CSV was created and contains three rows (+header)
    with open(temp_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 3  # one row per metric

    # Validate each row against the MeasurementRecord schema
    for row in rows:
        # Convert types to match schema expectations
        row_converted = {
            "participant_id": row["participant_id"],
            "metric_type": row["metric_type"],
            "value": float(row["value"]),
            "timestamp": row["timestamp"],
            "session_type": row["session_type"]
        }
        # The schema also requires an ``id`` field; we include it here.
        row_converted["id"] = row["id"]
        try:
            validate(instance=row_converted, schema=RECORD_SCHEMA)
        except ValidationError as e:
            pytest.fail(f"CSV row failed schema validation: {e}")