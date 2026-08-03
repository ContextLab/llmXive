"""
Contract test for results CSV schema.
Validates that the paired comparison results file adheres to the expected schema.
"""
import csv
import os
import pytest
from typing import List, Dict, Any

# Expected schema based on T025 requirements
# Columns: task_id, task_type, success_flag, wall_clock_time_ms, agent_type
EXPECTED_COLUMNS = [
    "task_id",
    "task_type",
    "success_flag",
    "wall_clock_time_ms",
    "agent_type"
]

RESULTS_FILE_PATH = "results/analysis/paired_comparison.csv"


def _load_csv_if_exists(path: str) -> List[Dict[str, Any]]:
    """Helper to load CSV if it exists, returns empty list if not."""
    if not os.path.exists(path):
        return []
    with open(path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_results_file_exists():
    """Contract: The results file must exist after a successful run."""
    assert os.path.exists(RESULTS_FILE_PATH), (
        f"Contract failed: Results file '{RESULTS_FILE_PATH}' does not exist. "
        "Ensure T025 (Generate summary CSV) has been executed."
    )


def test_results_schema_columns():
    """Contract: The results file must contain exactly the expected columns."""
    rows = _load_csv_if_exists(RESULTS_FILE_PATH)
    assert len(rows) > 0, (
        "Contract failed: Results file exists but is empty. "
        "Ensure T025 has generated data."
    )

    with open(RESULTS_FILE_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        actual_columns = reader.fieldnames

    missing_columns = set(EXPECTED_COLUMNS) - set(actual_columns)
    extra_columns = set(actual_columns) - set(EXPECTED_COLUMNS)

    error_msg = []
    if missing_columns:
        error_msg.append(f"Missing required columns: {missing_columns}")
    if extra_columns:
        error_msg.append(f"Unexpected extra columns: {extra_columns}")

    assert not error_msg, "Schema contract failed:\n" + "\n".join(error_msg)


def test_results_schema_types():
    """Contract: Validate data types for each column."""
    rows = _load_csv_if_exists(RESULTS_FILE_PATH)
    assert len(rows) > 0, "No rows to validate types."

    for i, row in enumerate(rows):
        # task_id: string
        assert isinstance(row["task_id"], str), f"Row {i}: task_id must be string"
        assert len(row["task_id"]) > 0, f"Row {i}: task_id cannot be empty"

        # task_type: string (occlusion, depth, relative)
        assert isinstance(row["task_type"], str), f"Row {i}: task_type must be string"
        valid_types = {"occlusion", "depth", "relative"}
        assert row["task_type"] in valid_types, (
            f"Row {i}: task_type '{row['task_type']}' not in {valid_types}"
        )

        # success_flag: string representation of boolean or int (0/1)
        # We accept string 'True'/'False' or '1'/'0' or actual bool/int if csv.DictReader converts
        sf = row["success_flag"]
        valid_success = {"True", "False", "1", "0", True, False, 1, 0}
        assert sf in valid_success, f"Row {i}: success_flag '{sf}' is not a valid boolean representation"

        # wall_clock_time_ms: numeric (float or int)
        try:
            float(row["wall_clock_time_ms"])
        except ValueError:
            pytest.fail(f"Row {i}: wall_clock_time_ms '{row['wall_clock_time_ms']}' is not numeric")

        # agent_type: string (2d, 3d)
        assert isinstance(row["agent_type"], str), f"Row {i}: agent_type must be string"
        valid_agents = {"2d", "3d"}
        assert row["agent_type"] in valid_agents, (
            f"Row {i}: agent_type '{row['agent_type']}' not in {valid_agents}"
        )


def test_results_no_null_success_flags():
    """Contract: Rows with null success_flag must be excluded (per T025)."""
    rows = _load_csv_if_exists(RESULTS_FILE_PATH)
    for i, row in enumerate(rows):
        assert row["success_flag"] is not None, f"Row {i}: success_flag is null"
        assert row["success_flag"] != "" and row["success_flag"] != "None", (
            f"Row {i}: success_flag is empty or 'None'"
        )