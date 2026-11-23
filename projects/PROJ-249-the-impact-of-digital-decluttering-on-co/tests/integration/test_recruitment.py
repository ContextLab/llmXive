"""
Integration test for the participant recruitment endpoint.

The test verifies that:
  1. A POST request to /register returns a 201 status code.
  2. The response contains a participant_id matching the pattern ^P\\d{3}$.
  3. The participant record is correctly written to data/raw/participants.csv.
"""
import csv
import re
from pathlib import Path

from llmxive_toolkit import paths

from code.recruitment.app import app

def test_register_participant(tmp_path, monkeypatch):
    # Ensure the participants CSV is placed in a temporary location for isolation.
    # Monkeypatch the path used by the application to point to the temporary dir.
    test_csv = tmp_path / "participants.csv"
    monkeypatch.setattr(
        "code.recruitment.app.PARTICIPANT_CSV",
        Path(test_csv)
    )

    client = app.test_client()

    # Send a registration request with optional demographics.
    payload = {
        "demographics": {
            "age": 28,
            "gender": "non-binary"
        }
    }
    response = client.post("/register", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    participant_id = data.get("participant_id")
    assert participant_id is not None

    # Verify the ID format.
    pattern = re.compile(r"^P\d{3}$")
    assert pattern.fullmatch(participant_id), f"ID {participant_id} does not match required pattern"

    # Verify the CSV file was created and contains the new participant.
    assert test_csv.exists(), "participants.csv was not created"

    with test_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # There should be exactly one data row (header is not counted).
    assert len(rows) == 1, f"Expected 1 participant record, found {len(rows)}"

    row = rows[0]
    assert row["participant_id"] == participant_id
    assert row["enrollment_date"] == data["enrollment_date"]
    # Demographics are stored as a JSON string; we only check that something was written.
    assert row["demographics"], "Demographics column is empty"