"""Integration test for residual analysis (T030).

This test validates the end-to-end execution of the residual analysis pipeline:
1. Loads real cleaned knot data from `data/processed/knots_cleaned.csv`.
2. Calls `code/analysis/residual_analysis.py` to fit models and identify outliers.
3. Verifies that the expected output file `docs/reproducibility/residual_analysis.md` is generated.
4. Verifies that the outlier JSON `data/processed/outlier_knots.json` is generated.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Project root is the parent of 'tests'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs" / "reproducibility"

INPUT_CSV = DATA_DIR / "knots_cleaned.csv"
OUTPUT_MD = DOCS_DIR / "residual_analysis.md"
OUTPUT_JSON = DATA_DIR / "outlier_knots.json"


@pytest.fixture(autouse=True)
def cleanup_outputs():
    """Clean up generated output files before and after the test."""
    # Remove if they exist to ensure we are testing generation
    if OUTPUT_MD.exists():
        OUTPUT_MD.unlink()
    if OUTPUT_JSON.exists():
        OUTPUT_JSON.unlink()
    yield
    # Optional: leave them for inspection if the test passes,
    # but for a strict integration test we verify existence.


def test_residual_analysis_integration():
    """Run the residual analysis script and verify outputs."""

    # Pre-condition: Input data must exist (downloaded by T011/T014)
    if not INPUT_CSV.exists():
        pytest.fail(
            f"Input data file {INPUT_CSV} not found. "
            "Please ensure T011/T014 (download/parsing) have been completed successfully."
        )

    # Ensure output directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Construct the command to run the residual analysis module
    # We use the module path relative to the project root
    script_path = PROJECT_ROOT / "code" / "analysis" / "residual_analysis.py"

    if not script_path.exists():
        pytest.fail(f"Script {script_path} not found.")

    # Run the script via the project's virtual environment python
    # to ensure correct imports and dependencies.
    venv_python = PROJECT_ROOT / "code" / ".venv" / "bin" / "python"
    if not venv_python.exists():
        # Fallback to system python if venv is not standard in this env
        venv_python = sys.executable

    cmd = [
        str(venv_python),
        "-m",
        "analysis.residual_analysis",
        "--input", str(INPUT_CSV),
        "--output-md", str(OUTPUT_MD),
        "--output-json", str(OUTPUT_JSON)
    ]

    # Execute the script
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Residual analysis script timed out.")

    # Check for success
    if result.returncode != 0:
        pytest.fail(
            f"Residual analysis script failed with code {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    # Post-condition 1: Verify Markdown report exists and is non-empty
    assert OUTPUT_MD.exists(), f"Output Markdown report {OUTPUT_MD} was not created."
    assert OUTPUT_MD.stat().st_size > 0, f"Output Markdown report {OUTPUT_MD} is empty."

    # Post-condition 2: Verify JSON outliers file exists and is valid JSON
    assert OUTPUT_JSON.exists(), f"Output JSON file {OUTPUT_JSON} was not created."
    assert OUTPUT_JSON.stat().st_size > 0, f"Output JSON file {OUTPUT_JSON} is empty."

    try:
        with open(OUTPUT_JSON, "r") as f:
            data = json.load(f)
        # Basic schema check: should be a list of entries
        assert isinstance(data, list), "Outlier data must be a list."
        if len(data) > 0:
            assert "knot_id" in data[0], "Outlier entries must contain 'knot_id'."
            assert "residual" in data[0], "Outlier entries must contain 'residual'."
    except json.JSONDecodeError as e:
        pytest.fail(f"Output JSON file {OUTPUT_JSON} is not valid JSON: {e}")

    # Post-condition 3: Verify the report mentions key analysis points
    with open(OUTPUT_MD, "r") as f:
        content = f.read()
    assert "Residual Analysis" in content, "Report must contain the title 'Residual Analysis'."
    assert "Outlier" in content or "outlier" in content, "Report must mention outliers."