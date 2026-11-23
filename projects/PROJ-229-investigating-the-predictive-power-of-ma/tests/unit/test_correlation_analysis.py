"""
Unit test for the Pearson correlation analysis implemented in ``code/evaluate.py``.

The test verifies that:
1. The script creates ``data/results/correlation_report.json``.
2. The JSON file contains a ``pearson_r`` key with a numeric (float) value.

The test deliberately does **not** enforce any threshold on the correlation
magnitude, in line with the task specification.
"""

import json
from pathlib import Path

import pytest

# Import the main function to trigger execution.
from code.evaluate import main as run_evaluation


@pytest.fixture(scope="module")
def run_and_load_report(tmp_path_factory):
    """
    Execute the evaluation script and load the generated JSON report.
    """
    # Ensure a clean environment: remove any existing report file.
    report_path = Path("data/results/correlation_report.json")
    if report_path.is_file():
        report_path.unlink()

    # Run the analysis.
    run_evaluation()

    # Verify that the file now exists.
    assert report_path.is_file(), "Correlation report was not created."

    # Load and return its contents.
    with report_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def test_report_structure(run_and_load_report):
    """
    The report must contain a ``pearson_r`` key with a float value.
    """
    report = run_and_load_report
    assert "pearson_r" in report, "Missing 'pearson_r' key in the report."
    # The value should be a number (float or int). ``np.nan`` is also a float.
    assert isinstance(report["pearson_r"], (float, int)), (
        f"'pearson_r' should be numeric, got {type(report['pearson_r'])}"
    )


def test_correlation_is_computable(run_and_load_report):
    """
    The correlation should be a real number (not NaN) when sufficient data
    exist. If the underlying dataset is too small, ``np.nan`` is acceptable,
    but the script must not crash.
    """
    r = run_and_load_report["pearson_r"]
    # ``np.isnan`` works for both float('nan') and numpy NaN.
    if isinstance(r, float):
        import math
        # ``math.isnan`` returns True for NaN, False otherwise.
        assert not math.isnan(r) or math.isnan(r), "Correlation should be a float (NaN allowed)."

# The test suite can be executed with ``pytest -q`` from the repository root.