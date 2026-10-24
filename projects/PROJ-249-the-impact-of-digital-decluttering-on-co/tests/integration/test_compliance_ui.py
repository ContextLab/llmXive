"""
Integration test for the daily compliance‑logging UI.

The test posts a valid compliance record to the Flask endpoint,
checks that a CSV file is created under ``data/raw/compliance_logs/``,
and validates the written row against ``contracts/compliance.schema.yaml``.
"""

import csv
import uuid
import yaml
from pathlib import Path

import pytest
from jsonschema import validate

from llmxive_toolkit import paths
from code.web.compliance.compliance_ui import app

@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_submit_log_and_schema_validation(client, monkeypatch):
    """
    Submit a well‑formed compliance payload, verify CSV output and JSON‑Schema
    conformance.
    """
    payload = {
        "participant_id": "P001",
        "date": "2024-10-01",
        "social_media_minutes": 20,
        "news_consumption": False,
        "notifications_off": True,
        "notes": "All good",
    }

    response = client.post("/submit_log", json=payload)
    assert response.status_code == 200
    resp_json = response.get_json()
    assert resp_json["status"] == "success"

    # Expected CSV file location
    expected_filename = f"compliance_{payload['participant_id']}_{payload['date']}.csv"
    csv_path = paths.data("raw", "compliance_logs", expected_filename)
    assert csv_path.is_file(), f"CSV file not created at {csv_path}"

    # Load the row that was written
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1, "Exactly one record should be written"
    row = rows[0]

    # Convert CSV strings to proper Python types for schema validation
    row_converted = {
        "id": row["id"],
        "participant_id": row["participant_id"],
        "date": row["date"],
        "social_media_minutes": int(row["social_media_minutes"]),
        "news_consumption": row["news_consumption"].lower() == "true",
        "notifications_off": row["notifications_off"].lower() == "true",
        "is_compliant": row["is_compliant"].lower() == "true",
    }

    # Load and validate against the JSON‑Schema
    schema_path = Path("contracts/compliance.schema.yaml")
    with schema_path.open() as f:
        schema = yaml.safe_load(f)

    validate(instance=row_converted, schema=schema)