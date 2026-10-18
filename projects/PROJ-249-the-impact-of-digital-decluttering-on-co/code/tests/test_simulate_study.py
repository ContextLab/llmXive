"""
Tests for the deterministic study simulation (Task T003).

The tests verify:
* The expected files are created.
* Participant IDs follow the ``P\\d{3}`` pattern.
* Trial‑level files contain the required columns.
* The scored measurements file conforms to the JSON schema in
 ``contracts/dataset.schema.yaml``.
* Running the simulation twice with the same seed yields identical files
 (determinism).
"""

import hashlib
import re
from pathlib import Path

import pandas as pd
import yaml
import jsonschema
from llmxive_toolkit import paths

# Import the script entry point so we can invoke it programmatically.
from code.validation.simulate_study import main as simulate_study

def test_files_exist(tmp_path):
    """
    Run the simulation and check that all required files are present.
    """
    # Ensure a clean data directory for the test run.
    data_root = paths.root / "data"
    # Remove any existing raw output that could interfere.
    for p in data_root.rglob("*"):
        if p.is_file():
            p.unlink()
    # Run the simulation.
    simulate_study()

    # Expected raw output locations.
    participants = paths.data("raw", "participants.csv")
    sart_trials = paths.data("raw", "trial_level", "sart_trials.csv")
    ospan_trials = paths.data("raw", "trial_level", "ospan_trials.csv")
    measurements = paths.data("raw", "simulated_measurements.csv")
    compliance_dir = paths.data("raw", "compliance_logs")
    smoke_results = paths.data("results", "smoke_results.json")
    checksum_file = paths.data("checksums.sha256")

    for expected in [
        participants,
        sart_trials,
        ospan_trials,
        measurements,
        smoke_results,
        checksum_file,
    ]:
        assert expected.exists(), f"Expected file {expected} does not exist."

    # At least one compliance log file should exist.
    compliance_files = list(compliance_dir.glob("*.csv"))
    assert compliance_files, "No compliance log CSV files were generated."

def test_participant_id_pattern():
    """Participant IDs must match the ``P\\d{3}`` regex."""
    participants = pd.read_csv(paths.data("raw", "participants.csv"))
    pattern = re.compile(r"^P\d{3}$")
    assert participants["participant_id"].apply(lambda x: bool(pattern.match(str(x)))).all()

def test_trial_level_columns():
    """SART and O‑Span trial files must contain the required columns."""
    sart = pd.read_csv(paths.data("raw", "trial_level", "sart_trials.csv"))
    ospan = pd.read_csv(paths.data("raw", "trial_level", "ospan_trials.csv"))

    expected_sart = {"participant_id", "phase", "trial_index", "rt_ms", "is_target", "response", "accuracy"}
    expected_ospan = {"participant_id", "phase", "trial_index", "item", "response", "correct"}

    assert expected_sart.issubset(set(sart.columns)), "Missing columns in SART trial file."
    assert expected_ospan.issubset(set(ospan.columns)), "Missing columns in O‑Span trial file."

def test_measurements_schema():
    """The scored measurements file must conform to ``contracts/dataset.schema.yaml``."""
    schema_path = paths.root / "contracts" / "dataset.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # The schema defines a root object with a ``measurements`` array.
    # For simplicity we validate each measurement record individually.
    measurement_schema = schema["definitions"]["MeasurementRecord"]
    validator = jsonschema.Draft7Validator(measurement_schema)

    measurements = pd.read_csv(paths.data("raw", "simulated_measurements.csv"))
    for idx, row in measurements.iterrows():
        record = {
            "participant_id": row["participant_id"],
            "metric_type": row["metric_type"],
            "value": row["value"],
            "timestamp": row["timestamp"],
            "session_type": row["session_type"],
        }
        errors = sorted(validator.iter_errors(record), key=lambda e: e.path)
        assert not errors, f"Schema validation errors in row {idx}: {errors}"

def test_determinism():
    """
    Running the simulation twice with the same configuration must produce
    identical checksum entries, proving deterministic output.
    """
    # First run
    simulate_study()
    checksum_path = paths.data("checksums.sha256")
    with open(checksum_path, "r", encoding="utf-8") as f:
        first_hashes = f.read()

    # Clean up generated raw files (but keep the checksum file for comparison)
    for p in paths.root.glob("data/raw/**"):
        if p.is_file():
            p.unlink()
    # Remove the checksum file then recreate it empty for the second run
    checksum_path.unlink()
    checksum_path.touch()

    # Second run
    simulate_study()
    with open(checksum_path, "r", encoding="utf-8") as f:
        second_hashes = f.read()

    assert first_hashes == second_hashes, "Checksums differ between runs; simulation is not deterministic."