"""
Contract Test for T014: Counterbalancing

Verifies that code/02_counterbalance.py produces the correct output file
with the expected row counts and structure.
"""
import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Import project paths
from config import get_processed_data_dir, get_raw_data_dir, get_code_dir

OUTPUT_FILE = "counterbalanced_trials.csv"
EXPECTED_RELATIONSHIPS = ["friend", "acquaintance"]

@pytest.fixture(scope="module")
def ensure_counterbalanced_exists():
    """
    Fixture to ensure the counterbalancing script has been run.
    If the output file does not exist, it attempts to run the script.
    """
    output_path = get_processed_data_dir() / OUTPUT_FILE
    if not output_path.exists():
        code_dir = get_code_dir()
        script_path = code_dir / "02_counterbalance.py"
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(code_dir.parent),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            pytest.fail(f"Counterbalancing script failed to run: {result.stderr}")
    
    return output_path

def test_counterbalanced_file_exists(ensure_counterbalanced_exists):
    """Test that the output file exists."""
    assert ensure_counterbalanced_exists.exists(), f"Output file {ensure_counterbalanced_exists} not found."

def test_counterbalanced_row_counts(ensure_counterbalanced_exists):
    """
    Test that the row count matches the expected formula:
    N_participants * N_stimuli * 2 (relationships)
    """
    # Load stimuli to get N_stimuli
    raw_data_dir = get_raw_data_dir()
    stimuli_path = raw_data_dir / "stimuli.csv"
    
    if not stimuli_path.exists():
        pytest.skip("Stimuli file not found, cannot verify row counts.")

    with open(stimuli_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        stimuli_count = sum(1 for _ in reader)

    # Load counterbalanced trials
    with open(ensure_counterbalanced_exists, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    actual_count = len(rows)
    
    # We assume N_participants = 60 based on power analysis
    expected_count = 60 * stimuli_count * 2

    assert actual_count == expected_count, (
        f"Row count mismatch: Expected {expected_count} (60 * {stimuli_count} * 2), "
        f"got {actual_count}"
    )

def test_counterbalanced_schema(ensure_counterbalanced_exists):
    """Test that the CSV has the required columns."""
    required_columns = {
        "trial_id",
        "participant_id",
        "stimulus_id",
        "relationship_type",
        "stimulus_text",
        "emoji_count",
        "punctuation_type",
        "length_category",
        "scenario_id",
        "cue_intensity",
    }

    with open(ensure_counterbalanced_exists, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        actual_columns = set(reader.fieldnames)

    missing = required_columns - actual_columns
    assert not missing, f"Missing required columns: {missing}"

def test_relationship_values(ensure_counterbalanced_exists):
    """Test that relationship_type only contains valid values."""
    with open(ensure_counterbalanced_exists, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert row["relationship_type"] in EXPECTED_RELATIONSHIPS, (
                f"Invalid relationship type: {row['relationship_type']}"
            )

def test_unique_trial_ids(ensure_counterbalanced_exists):
    """Test that every trial_id is unique."""
    with open(ensure_counterbalanced_exists, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        trial_ids = [row["trial_id"] for row in reader]
    
    assert len(trial_ids) == len(set(trial_ids)), "Duplicate trial_ids found."

def test_complete_counterbalancing_coverage(ensure_counterbalanced_exists):
    """
    Test that every participant has every stimulus in both relationship contexts.
    """
    with open(ensure_counterbalanced_exists, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group by (participant_id, stimulus_id)
    pairs = {}
    for row in rows:
        key = (row["participant_id"], row["stimulus_id"])
        if key not in pairs:
            pairs[key] = set()
        pairs[key].add(row["relationship_type"])

    # Verify every pair has both relationships
    for key, rels in pairs.items():
        assert set(EXPECTED_RELATIONSHIPS) == rels, (
            f"Pair {key} is missing relationship contexts. Found: {rels}"
        )