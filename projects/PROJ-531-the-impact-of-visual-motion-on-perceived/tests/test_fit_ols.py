"""
Test for T021 – OLS fitting script.

The test runs the `code/fit_ols.py` script and verifies that the
`data/results/ols.json` file is created and contains the required keys.
"""

import json
import subprocess
from pathlib import Path

import pytest

from llmxive_toolkit import paths


@pytest.fixture(scope="module")
def run_script():
    """Execute the OLS fitting script before tests."""
    script_path = Path("code/fit_ols.py")
    result = subprocess.run(
        ["python", str(script_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"


def test_ols_output_exists(run_script):
    """Check that the OLS JSON output file exists."""
    out_path = paths.data("results", "ols.json")
    assert out_path.is_file(), f"{out_path} was not created"


def test_ols_output_structure(run_script):
    """Validate the structure of the OLS result JSON."""
    out_path = paths.data("results", "ols.json")
    with open(out_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Required top‑level keys
    for key in ("coefficients", "standard_errors", "p_values", "cv_metrics"):
        assert key in data, f"Missing key `{key}` in OLS output"

    # Coefficients, standard_errors, and p_values should be dicts with matching keys
    coeff_keys = set(data["coefficients"].keys())
    se_keys = set(data["standard_errors"].keys())
    p_keys = set(data["p_values"].keys())

    assert coeff_keys == se_keys == p_keys, "Mismatch between coefficient, SE, and p‑value keys"

    # cv_metrics should contain the placeholder fields
    cv = data["cv_metrics"]
    for metric in ("r2_mean", "r2_std", "rmse_mean"):
        assert metric in cv, f"cv_metrics missing `{metric}`"
        # Values are placeholders (None) at this stage
        assert cv[metric] is None, f"cv_metrics `{metric}` should be None before cross‑validation"