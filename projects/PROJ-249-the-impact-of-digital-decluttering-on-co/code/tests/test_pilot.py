"""
Test suite for the pilot validation (T000).

This test loads the pilot measurement records CSV, validates each row
against the dataset JSON schema, and checks that all SART response times
are within the required bounds (100 ms – 5000 ms) and that the accuracy
for each participant is at least 50 %.
"""
import csv
import json
import pathlib
from datetime import datetime

import pytest
import yaml
from jsonschema import validate, ValidationError

# Paths
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
PILOT_CSV = PROJECT_ROOT / "data" / "raw" / "pilot" / "measurement_records_pilot.csv"
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-the-impact-of-digital-decluttering-on-co" / "contracts" / "dataset.schema.yaml"

# Load JSON schema
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    schema = yaml.safe_load(f)

# Helper to parse ISO timestamps
def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def test_pilot_csv_exists():
    """The pilot CSV file must exist."""
    assert PILOT_CSV.exists(), f"Pilot CSV not found at {PILOT_CSV}"

def test_pilot_rows_schema_and_constraints():
    """Validate each row against the schema and pilot-specific constraints."""
    with open(PILOT_CSV, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    assert rows, "Pilot CSV is empty"

    for row in rows:
        # ---- Schema validation ----
        # Convert appropriate fields to correct types
        record = {
            "id": row["id"],
            "participant_id": row["participant_id"],
            "metric_type": row["metric_type"],
            "value": float(row["value"]),
            "timestamp": row["timestamp"],
            "session_type": row["session_type"],
        }

        # trial_data is optional; parse if present
        trial_data_raw = row.get("trial_data", "")
        if trial_data_raw:
            try:
                trial_data = json.loads(trial_data_raw)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"Invalid JSON in trial_data for row {row['id']}: {exc}") from exc
            record["trial_data"] = trial_data

        # Validate against the JSON schema
        try:
            validate(instance=record, schema=schema)
        except ValidationError as exc:
            raise AssertionError(f"Schema validation failed for row {row['id']}: {exc.message}") from exc

        # ---- Pilot-specific constraints ----
        # Only apply SART timing/accuracy checks for SART metrics
        if row["metric_type"] == "sart_mean_rt":
            # Ensure trial_data contains required fields
            assert "response_times" in trial_data, f"Missing response_times in row {row['id']}"
            assert "accuracies" in trial_data, f"Missing accuracies in row {row['id']}"

            response_times = trial_data["response_times"]
            accuracies = trial_data["accuracies"]

            # 1. All response times must be within 100 ms – 5000 ms
            for rt in response_times:
                assert isinstance(rt, (int, float)), f"Response time not numeric in row {row['id']}"
                assert 100 <= rt <= 5000, f"Response time {rt} out of bounds (100‑5000) in row {row['id']}"

            # 2. Accuracy must be at least 50 %
            # accuracies are booleans where True = correct
            correct_count = sum(1 for a in accuracies if a is True or a == "true")
            total = len(accuracies)
            assert total > 0, f"No accuracy entries for row {row['id']}"
            accuracy = correct_count / total
            assert accuracy >= 0.5, f"SART accuracy {accuracy:.2%} below 50 % for participant {row['participant_id']}"

# The test suite will be collected by pytest automatically. No additional
# execution script is required for T000.