"""Basic sanity test that the ``code/main.py`` entry point runs without crashing.

The test invokes the script with a very small artificial catalog (two dummy
tasks) and checks that the expected JSON report files are created.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

@pytest.fixture(scope="module")
def temp_catalog(tmp_path_factory):
    """Create a minimal catalog JSON file with two dummy tasks."""
    catalog = [
        {"task_id": "dummy/Task1", "prompt": "print(1)", "human_solution": "print(1)", "test_suite_path": "data/benchmarks/processed/tests/dummy_Task1_test.py"},
        {"task_id": "dummy/Task2", "prompt": "print(2)", "human_solution": "print(2)", "test_suite_path": "data/benchmarks/processed/tests/dummy_Task2_test.py"},
    ]
    catalog_path = tmp_path_factory.mktemp("data") / "catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f)
    return str(catalog_path)

def test_main_runs_and_creates_reports(temp_catalog, tmp_path):
    """Run ``code/main.py`` against the temporary catalog and verify output."""
    # Ensure the output directory is empty before the run
    reports_dir = Path("data/coverage_reports")
    if reports_dir.exists():
        for p in reports_dir.iterdir():
            p.unlink()

    # Execute the script
    result = subprocess.run(
        [sys.executable, "code/main.py", "--dataset", temp_catalog, "--batch-size", "1"],
        capture_output=True,
        text=True,
    )

    # The script should exit with code 0
    assert result.returncode == 0, f"STDOUT: {result.stdout}\\nSTDERR: {result.stderr}"

    # Expected JSON report files should exist (even if they contain failure records)
    for task_id in ["dummy/Task1", "dummy/Task2"]:
        report_path = reports_dir / f"{task_id}.json"
        assert report_path.exists(), f"Missing report for {task_id}"
        # Load and ensure the JSON has the required keys
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "task_id" in data
        assert "status" in data
        assert "timestamp" in data