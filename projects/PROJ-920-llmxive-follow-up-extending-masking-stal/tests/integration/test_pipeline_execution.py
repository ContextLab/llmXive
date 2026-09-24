"""
Integration test for T039: Execute the full pipeline using run_pipeline.sh.
Verifies that all expected output files are generated and valid.
"""
import os
import subprocess
import json
import sys
from pathlib import Path
import pytest

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
PIPELINE_SCRIPT = PROJECT_ROOT / "run_pipeline.sh"

# Expected output paths
EXPECTED_FILES = {
    "trajectories": PROJECT_ROOT / "data" / "raw" / "trajectories.json",
    "simulation": PROJECT_ROOT / "data" / "processed" / "simulation_results.csv",
    "regression": PROJECT_ROOT / "output" / "regression_summary.json",
    "hypothesis": PROJECT_ROOT / "output" / "hypothesis_summary.md",
    "plot": PROJECT_ROOT / "output" / "plots" / "regime_map.png"
}

@pytest.fixture(scope="module")
def pipeline_output():
    """Run the pipeline once for the test module."""
    # Ensure we are in the project root
    os.chdir(PROJECT_ROOT)
    
    # Make script executable if not already
    if not os.access(PIPELINE_SCRIPT, os.X_OK):
        os.chmod(PIPELINE_SCRIPT, 0o755)
    
    # Run the pipeline
    result = subprocess.run(
        ["bash", str(PIPELINE_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    
    if result.returncode != 0:
        pytest.fail(f"Pipeline execution failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    
    return result

def test_pipeline_executes_successfully(pipeline_output):
    """Verify the pipeline script runs without errors."""
    assert pipeline_output.returncode == 0, "Pipeline script exited with non-zero status."

def test_all_output_files_exist():
    """Verify all expected output files are generated."""
    missing_files = []
    for name, path in EXPECTED_FILES.items():
        if not path.exists():
            missing_files.append(f"{name}: {path}")
    
    assert not missing_files, f"Missing output files: {', '.join(missing_files)}"

def test_trajectories_json_valid():
    """Verify the trajectory JSON is valid and contains expected structure."""
    path = EXPECTED_FILES["trajectories"]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Trajectory data should be a list."
    assert len(data) > 0, "Trajectory data should not be empty."
    
    # Check for required metadata fields per task T011
    required_fields = ["evidence_turn_index", "density_value", "is_critical"]
    first_item = data[0]
    for field in required_fields:
        assert field in first_item, f"Missing required field '{field}' in trajectory item."

def test_simulation_results_csv_exists_and_valid():
    """Verify the simulation CSV exists and is readable."""
    path = EXPECTED_FILES["simulation"]
    assert path.stat().st_size > 0, "Simulation results CSV is empty."
    
    # Basic CSV validation (header + at least one row)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) >= 2, "Simulation results CSV should have header and at least one data row."
        assert "horizon" in lines[0].lower() or "density" in lines[0].lower(), "CSV header seems invalid."

def test_regression_summary_json_valid():
    """Verify regression summary JSON contains required fields."""
    path = EXPECTED_FILES["regression"]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert "coefficients" in data or "interaction_term" in data, "Regression summary missing key data."
    assert "p_values" in data or "p_value" in data, "Regression summary missing p-values."

def test_hypothesis_summary_md_exists_and_valid():
    """Verify hypothesis summary markdown exists and contains boolean logic."""
    path = EXPECTED_FILES["hypothesis"]
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert len(content) > 50, "Hypothesis summary content is too short."
    assert "hypothesis_supported" in content.lower() or "p-value" in content.lower(), "Hypothesis summary missing key indicators."

def test_plot_png_exists_and_valid_size():
    """Verify the plot PNG exists and is under 5MB."""
    path = EXPECTED_FILES["plot"]
    assert path.stat().st_size > 0, "Plot PNG is empty."
    assert path.stat().st_size <= 5 * 1024 * 1024, f"Plot PNG exceeds 5MB limit ({path.stat().st_size} bytes)."
    
    # Verify it's a valid PNG header
    with open(path, "rb") as f:
        header = f.read(8)
        assert header[:8] == b'\x89PNG\r\n\x1a\n', "File does not appear to be a valid PNG."