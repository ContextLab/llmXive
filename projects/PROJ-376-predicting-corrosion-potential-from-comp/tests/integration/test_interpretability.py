"""
Integration test for plot generation in the interpretability module.

This test verifies that the `code/models/interpret.py` script successfully
generates the required partial dependence plots and saves them to the
designated output directory under `data/processed/interpretability/`.

It assumes:
1. The data ingestion and preprocessing pipeline (US1) has completed.
2. The model training and evaluation pipeline (US2) has completed,
   producing `data/processed/model_results.json` and trained model artifacts.
3. The `code/models/interpret.py` script is implemented and executable.

The test runs the script as a subprocess and validates:
- The script exits with code 0.
- The output directory `data/processed/interpretability/` exists.
- At least one plot file (e.g., PNG or PDF) exists in the output directory.
- The files are non-empty.
"""

import os
import subprocess
import sys
from pathlib import Path
import json

import pytest

# Project root is assumed to be the parent of 'code' and 'tests'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
INTERPRETABILITY_DIR = DATA_DIR / "processed" / "interpretability"

# Paths to expected outputs from previous stages
MODEL_RESULTS_PATH = DATA_DIR / "processed" / "model_results.json"
SPLIT_INDICES_PATH = DATA_DIR / "processed" / "split_indices.json"

# The script to run
INTERPRET_SCRIPT = CODE_DIR / "models" / "interpret.py"

# Expected output files (at least one must exist)
EXPECTED_PLOT_EXTENSIONS = {".png", ".pdf", ".svg", ".jpg"}

@pytest.mark.integration
def test_interpretability_plot_generation():
    """
    Test that running the interpretability script generates plot files.
    """
    # Pre-conditions: Ensure required inputs from previous stages exist
    assert MODEL_RESULTS_PATH.exists(), (
        f"Model results file not found at {MODEL_RESULTS_PATH}. "
        "Please complete User Story 2 (T024) before running this test."
    )
    
    # Check if split indices exist (needed for GroupKFold aware interpretation)
    if not SPLIT_INDICES_PATH.exists():
        pytest.skip(
            f"Split indices file not found at {SPLIT_INDICES_PATH}. "
            "GroupKFold indices are required for valid interpretation. "
            "Please complete User Story 1 (T015/T017) first."
        )
    
    # Ensure the output directory exists (script might create it, but let's be safe)
    INTERPRETABILITY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean up any existing plot files in the output directory to ensure
    # we are testing fresh generation
    for existing_file in INTERPRETABILITY_DIR.iterdir():
        if existing_file.suffix.lower() in EXPECTED_PLOT_EXTENSIONS:
            existing_file.unlink()
    
    # Construct the command to run the script
    # We run it as a module or script within the project context
    cmd = [sys.executable, str(INTERPRET_SCRIPT)]
    
    # Run the script
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )
    except subprocess.TimeoutExpired:
        pytest.fail("The interpretability script timed out after 300 seconds.")
    
    # Assert the script exited successfully
    if result.returncode != 0:
        pytest.fail(
            f"Interpretability script failed with return code {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    
    # Post-conditions: Verify output files exist
    plot_files = [
        f for f in INTERPRETABILITY_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in EXPECTED_PLOT_EXTENSIONS
    ]
    
    assert len(plot_files) > 0, (
        f"No plot files found in {INTERPRETABILITY_DIR}. "
        "The script should have generated at least one partial dependence plot "
        "or feature importance visualization."
    )
    
    # Verify that the generated files are not empty
    for plot_file in plot_files:
        assert plot_file.stat().st_size > 0, (
            f"Plot file {plot_file} is empty. "
            "This indicates a failure in the plotting logic."
        )
    
    # Optional: Log which files were generated for debugging
    generated_files = [f.name for f in plot_files]
    print(f"Successfully generated {len(generated_files)} plot(s): {generated_files}")