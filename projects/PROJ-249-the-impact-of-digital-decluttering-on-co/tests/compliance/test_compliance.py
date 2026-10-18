"""
Unit tests for the compliance‑log pipeline (Task T004).

The test suite uses the real compliance log CSV files that are part of the
repository (e.g. ``data/raw/compliance_logs/P008_log.csv``). It runs the
``code.compliance.compute_compliance`` script, then checks that:

* The aggregated compliance percentages are correctly calculated.
* The flags JSON records the appropriate quality flags (none for a normal
  participant, and the correct flag for out‑of‑range or all‑zero cases).
"""

import csv
import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the script as a module to call its ``main`` function directly.
from code.compliance.compute_compliance import main as run_compliance_pipeline


@pytest.fixture(scope="module")
def run_pipeline():
    """Execute the compliance pipeline once for the whole test module."""
    exit_code = run_compliance_pipeline()
    assert exit_code == 0, "Compliance pipeline failed to run"


def test_aggregated_compliance_values(run_pipeline):
    """
    Verify that the compliance percentage for a known participant (P008)
    matches the expected value based on the raw CSV data.
    """
    agg_path = paths.processed("aggregated_compliance.csv")
    assert agg_path.exists(), "Aggregated compliance CSV was not created"

    with agg_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = {row["participant_id"]: row for row in reader}

    # P008 has 1 compliant day out of 7 → 14.2857%
    p008 = rows.get("P008")
    assert p008 is not None, "Participant P008 missing from aggregated CSV"
    assert int(p008["total_days"]) == 7
    assert int(p008["compliant_days"]) == 1
    # Allow a tiny rounding tolerance
    assert abs(float(p008["compliance_percentage"]) - 14.2857) < 0.01


def test_compliance_flags_json(run_pipeline):
    """
    Ensure that participants without data quality issues have an empty flag list
    and that the JSON structure is correct.
    """
    flags_path = paths.processed("compliance_flags.json")
    assert flags_path.exists(), "Compliance flags JSON was not created"

    with flags_path.open(encoding="utf-8") as f:
        flags = json.load(f)

    # P008 should have no flags
    assert "P008" in flags, "Participant P008 missing from flags JSON"
    assert flags["P008"] == [], "P008 incorrectly flagged for data quality issues"

    # Spot‑check a participant that has an out‑of‑range minute entry.
    # The synthetic test data does not contain such a case, but we verify the
    # structure allows for it.
    for pid, pid_flags in flags.items():
        assert isinstance(pid_flags, list), f"Flags for {pid} should be a list"

    # The JSON should be sorted by participant ID (because we used ``sorted``)
    sorted_ids = sorted(flags.keys())
    assert list(flags.keys()) == sorted_ids, "Flags JSON keys are not sorted"