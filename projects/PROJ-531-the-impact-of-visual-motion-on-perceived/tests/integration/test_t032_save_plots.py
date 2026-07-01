"""
Integration Test for T032: Save Plots and Generate Interpretation.

This test verifies that the T032 script successfully:
1. Creates the output directory structure.
2. Generates plot files in `data/results/plots/`.
3. Generates `data/results/interpretation.md`.

Prerequisites:
- T017 (cleaned_data.csv) must exist.
- T026 (model_metrics.json) must exist.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Mock data generation for test isolation if real files missing
# In a real CI run, these files should exist from previous tasks.
# We will check existence and skip if not found, or create minimal mocks if allowed.
# However, per constraints, we must test real execution.
# We assume the test environment has the data from previous tasks.

@pytest.fixture
def required_data_files():
    """Ensure required input files exist for the test."""
    cleaned_data = project_root / "data" / "processed" / "cleaned_data.csv"
    metrics_file = project_root / "data" / "results" / "model_metrics.json"
    
    if not cleaned_data.exists():
        pytest.skip(f"Required input {cleaned_data} not found. Run T017 first.")
    if not metrics_file.exists():
        pytest.skip(f"Required input {metrics_file} not found. Run T026 first.")
    
    return cleaned_data, metrics_file

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory to verify file creation without polluting main data."""
    # We actually need to test against the real paths defined in T032, 
    # so we will verify existence in the real data directory after running.
    # But to avoid side effects in a pure unit test, we might mock the paths.
    # For integration testing of the script's behavior, we run it and check the real FS.
    pass

def test_t032_execution_creates_outputs(required_data_files):
    """
    Run the T032 script and verify it creates the expected output files.
    """
    import importlib.util
    
    # Load the T032 script as a module
    script_path = project_root / "code" / "visualization" / "t032_save_plots_and_interpret.py"
    if not script_path.exists():
        pytest.fail(f"T032 script not found at {script_path}")
    
    spec = importlib.util.spec_from_file_location("t032_script", script_path)
    module = importlib.util.module_from_spec(spec)
    
    # Define paths to check
    plots_dir = project_root / "data" / "results" / "plots"
    interpretation_file = project_root / "data" / "results" / "interpretation.md"
    
    # Clean previous outputs if any
    if plots_dir.exists():
        shutil.rmtree(plots_dir)
    if interpretation_file.exists():
        interpretation_file.unlink()
    
    # Execute the script
    try:
        spec.loader.exec_module(module)
        module.main()
    except Exception as e:
        pytest.fail(f"T032 execution failed: {e}")
    
    # Verify outputs exist
    assert plots_dir.exists(), "Plots directory was not created."
    assert len(list(plots_dir.glob("*.png"))) > 0, "No plot files were generated in data/results/plots/."
    assert interpretation_file.exists(), "interpretation.md was not generated."
    
    # Verify interpretation content is not empty
    with open(interpretation_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert len(content) > 50, "Interpretation file is too short."
        assert "Visual Motion" in content or "Agency" in content, "Interpretation does not contain expected keywords."

def test_t032_handles_missing_metrics_gracefully():
    """
    Verify that T032 fails loudly if model_metrics.json is missing.
    """
    import importlib.util
    script_path = project_root / "code" / "visualization" / "t032_save_plots_and_interpret.py"
    
    # Temporarily rename the metrics file to simulate absence
    metrics_file = project_root / "data" / "results" / "model_metrics.json"
    backup_file = project_root / "data" / "results" / "model_metrics.json.bak"
    
    if not metrics_file.exists():
        pytest.skip("Cannot test missing metrics if file doesn't exist to begin with.")
    
    metrics_file.rename(backup_file)
    
    try:
        spec = importlib.util.spec_from_file_location("t032_script", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Expect an exception
        with pytest.raises(FileNotFoundError):
            module.main()
    finally:
        # Restore the file
        if backup_file.exists():
            backup_file.rename(metrics_file)
