"""
Test to verify that the pipeline runtime report indicates a successful execution.

The test checks for the existence of `output/pipeline_runtime.json`, ensures that the
reported status is `"pass"` and that the total execution time does not exceed the
allowed threshold of 7200 seconds (2 hours).

This verification is part of task T120.
"""

import json
from pathlib import Path


def test_pipeline_runtime_pass():
    """Assert that the pipeline runtime JSON reports a passing status within time limits."""
    runtime_path = Path("output/pipeline_runtime.json")

    # Ensure the file exists
    assert runtime_path.is_file(), f"Missing file: {runtime_path}"

    # Load the JSON content
    with runtime_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Verify status is 'pass'
    status = data.get("status")
    assert status == "pass", f"Expected status 'pass', got '{status}'"

    # Verify total execution time is present and within the allowed limit
    total_time = data.get("total_time_seconds")
    assert isinstance(total_time, (int, float)), (
        f"'total_time_seconds' must be a number, got {type(total_time)}"
    )
    assert total_time <= 7200, (
        f"Pipeline runtime exceeds limit: {total_time} seconds (max 7200)"
    )

    # Optional: verify that a start and end timestamp are present
    assert "start_timestamp" in data, "Missing 'start_timestamp' in runtime report"
    assert "end_timestamp" in data, "Missing 'end_timestamp' in runtime report"

    # If all assertions pass, the test succeeds.