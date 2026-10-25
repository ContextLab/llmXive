"""
Test for the feasibility check script (T010).

The test invokes ``code.run_feasibility.run_feasibility`` which executes a
representative subset of the factorial sweep, writes a JSON report to
``data/results/feasibility_report.json`` and returns the same dictionary.
The test asserts that the reported boolean flags are ``True``.
"""

import json
import os

from llmxive_toolkit import paths

# Import the function under test
from code.run_feasibility import run_feasibility

def test_feasibility_report():
    """
    Execute the feasibility routine and verify the JSON output.
    """
    # Run the feasibility check with a modest task sample to keep the test fast.
    report = run_feasibility(task_sample=50, seed=123)

    # The function should return a dict matching the JSON file.
    json_path = paths.results("feasibility_report.json")
    assert json_path.exists(), f"Report file not found at {json_path}"

    with json_path.open("r", encoding="utf-8") as f:
        file_report = json.load(f)

    assert report == file_report, "In‑memory report differs from JSON file"

    # Verify that the limits are respected.
    assert report["within_time_limit"] is True, "Runtime exceeded the 6 h limit"
    assert report["within_memory_limit"] is True, "Peak memory exceeded the 7 GB limit"