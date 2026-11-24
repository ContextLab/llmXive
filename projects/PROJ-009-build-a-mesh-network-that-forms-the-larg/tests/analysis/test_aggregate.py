"""
Integration test for the aggregation script (T010).

The test invokes the ``code.analysis.aggregate`` module as a script,
then checks that the expected output files exist and contain sensible
data.
"""
import json
import csv
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# The script under test is executed via the ``python -m`` entry point.
# The ``execute: true`` flag in the artifact definition will cause the
# runtime to run the script before this test is collected, so the test
# can simply verify the artefacts.
def test_aggregation_outputs_exist():
    # Expected output locations
    exec_csv = paths.data("processed", "execution_runs.csv")
    val_json = paths.data("raw", "validation_status.json")

    assert exec_csv.exists(), f"{exec_csv} was not created"
    assert val_json.exists(), f"{val_json} was not created"

    # Basic sanity checks on the CSV contents
    with exec_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert rows, "execution_runs.csv is empty"
        # Verify required columns are present
        required = {
            "run_id",
            "node_count",
            "granularity_setting",
            "injected_latency_ms",
            "throughput_ops",
            "mean_wall_clock_time_sec",
            "coordination_overhead_ratio",
            "dropout_count",
            "packet_to_mbps_factor",
            "percent_to_ops_factor",
        }
        assert required.issubset(set(reader.fieldnames)), "Missing required columns"

    # Validation status JSON should map each run_id to a dict with status
    with val_json.open() as f:
        status = json.load(f)
    assert isinstance(status, dict) and status, "validation_status.json is empty or not a dict"
    for run_id, entry in status.items():
        assert entry["status"] in {"included", "excluded"}
        assert "reason" in entry