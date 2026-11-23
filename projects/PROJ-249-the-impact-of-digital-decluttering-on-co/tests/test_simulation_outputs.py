import csv
import json
from pathlib import Path

import pytest
from llmxive_toolkit import paths

# Helper to read a CSV into a list of dicts
def _read_csv(file_path: Path):
    with open(file_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_simulated_files_exist():
    """All simulated output files must exist after running the generator."""
    expected_files = [
        paths.data("raw", "participants_simulated.csv"),
        paths.data("raw", "trial_level", "sart_trials_sim.csv"),
        paths.data("raw", "trial_level", "ospan_trials_sim.csv"),
        paths.data("raw", "measurement_records_sim.csv"),
        paths.data("results", "smoke_results.json"),
        paths.data("checksums.sha256"),
    ]
    for f in expected_files:
        assert f.is_file(), f"Missing expected file: {f}"

def test_measurement_records_schema():
    """
    Verify that each measurement record contains the required fields
    and that ``quality_flag`` is one of the allowed enum values.
    """
    csv_path = paths.data("raw", "measurement_records_sim.csv")
    rows = _read_csv(csv_path)

    required_fields = {
        "id",
        "participant_id",
        "phase",
        "metric_type",
        "value",
        "timestamp",
        "quality_flag",
    }
    allowed_phases = {"baseline", "post"}
    allowed_quality = {"valid", "low_attention", "missing"}

    for row in rows:
        assert required_fields.issubset(row.keys()), "Missing required column"
        assert row["phase"] in allowed_phases, f"Invalid phase: {row['phase']}"
        assert row["quality_flag"] in allowed_quality, f"Invalid flag: {row['quality_flag']}"

def test_checksum_manifest_contains_all_files():
    """
    Ensure that the SHA‑256 manifest lists every generated raw file.
    """
    manifest_path = paths.data("checksums.sha256")
    with open(manifest_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Build a set of relative paths that should be present
    expected_paths = {
        str(paths.data("raw", "participants_simulated.csv").relative_to(paths.root)),
        str(paths.data("raw", "trial_level", "sart_trials_sim.csv").relative_to(paths.root)),
        str(paths.data("raw", "trial_level", "ospan_trials_sim.csv").relative_to(paths.root)),
        str(paths.data("raw", "measurement_records_sim.csv").relative_to(paths.root)),
    }
    # Include each compliance log file
    compliance_dir = paths.data("raw", "compliance_logs_sim")
    for log_file in compliance_dir.glob("*.csv"):
        expected_paths.add(str(log_file.relative_to(paths.root)))

    manifest_paths = {line.split("  ", 1)[1] for line in lines}
    missing = expected_paths - manifest_paths
    assert not missing, f"Checksum manifest missing entries for: {missing}"