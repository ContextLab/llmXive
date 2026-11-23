"""
Integration test for the full comparative pipeline (US3).
Verifies that running `main.py --compare` produces the required output artifacts:
- data/results/final_report.md
- data/results/deltas.json
"""
import os
import subprocess
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Ensure we can import from the code directory
sys.path.insert(0, str(CODE_DIR))


@pytest.fixture(autouse=True)
def setup_environment():
    """Ensure output directories exist and clean previous results."""
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Clean up potential previous artifacts to ensure fresh run
    final_report = DATA_RESULTS_DIR / "final_report.md"
    deltas_file = DATA_RESULTS_DIR / "deltas.json"
    if final_report.exists():
        final_report.unlink()
    if deltas_file.exists():
        deltas_file.unlink()
    yield
    # No teardown needed for test isolation

def test_full_pipeline():
    """
    Assert that running `main.py --compare` produces `data/results/final_report.md`
    and `data/results/deltas.json`.
    """
    # Construct the command
    main_script = CODE_DIR / "main.py"
    cmd = [sys.executable, str(main_script), "--compare"]

    # Run the command
    # We capture output to inspect if it fails, but we expect success
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for the full pipeline
        )
    except subprocess.TimeoutExpired:
        pytest.fail("The comparative pipeline timed out after 300 seconds.")

    # Assert the command exited successfully
    if result.returncode != 0:
        pytest.fail(
            f"Command failed with return code {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    # Verify artifact existence
    final_report_path = DATA_RESULTS_DIR / "final_report.md"
    deltas_path = DATA_RESULTS_DIR / "deltas.json"

    assert final_report_path.exists(), "data/results/final_report.md was not created."
    assert deltas_path.exists(), "data/results/deltas.json was not created."

    # Verify content validity
    # 1. Check final_report.md is not empty
    report_content = final_report_path.read_text()
    assert len(report_content) > 100, "data/results/final_report.md is unexpectedly empty."
    # Basic check for expected sections (optional but good for integration)
    assert "p-value" in report_content.lower(), "Report missing 'p-value' section."
    assert "deltas" in report_content.lower(), "Report missing 'deltas' section."

    # 2. Check deltas.json is valid JSON and has expected keys
    try:
        deltas_data = json.loads(deltas_path.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(f"data/results/deltas.json is not valid JSON: {e}")

    required_keys = ["success_rate_delta", "memory_reduction_pct"]
    for key in required_keys:
        assert key in deltas_data, f"deltas.json missing required key: {key}"

    # Verify that values are numbers (not just placeholders like "0.0" strings if any)
    # The task requires REAL measurements. If the pipeline ran successfully,
    # it should have computed these.
    # Note: We allow 0.0 if the experiment actually yielded 0 delta, but we ensure it's a float/int.
    for key in required_keys:
        val = deltas_data[key]
        assert isinstance(val, (int, float)), f"deltas[{key}] is not a number: {type(val)}"

    # Final assertion: Ensure the pipeline actually ran the comparative logic
    # by checking if total_traces > 0 in deltas (implies data was processed)
    # This is a strong indicator that the pipeline didn't just create empty files.
    # If the system is designed to handle empty data gracefully, this check might need adjustment,
    # but for a "comparative pipeline", we expect some data.
    if "total_traces" in deltas_data:
        assert deltas_data["total_traces"] > 0, (
            "deltas.json indicates 0 total_traces. "
            "The pipeline may have failed to load or process data."
        )

    # If we reach here, the test passes
    assert True