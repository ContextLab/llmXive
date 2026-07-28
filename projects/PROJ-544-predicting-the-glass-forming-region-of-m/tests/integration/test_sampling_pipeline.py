"""
Integration test for the sampling pipeline (T017).
Verifies that the sampling script runs end-to-end and produces valid output.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SAMPLE_SCRIPT = PROJECT_ROOT / "scripts" / "sample_dataset.py"
DATA_DIR = PROJECT_ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"

@pytest.fixture
def setup_temp_data():
    """Setup a temporary dataset for testing."""
    # Ensure data directories exist
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal synthetic dataset for testing if one doesn't exist
    test_csv = SAMPLES_DIR / "test_input.csv"
    
    if not test_csv.exists():
        # Create a small stratified dataset
        data = {
            "composition": [
                "Cu50Zr50", "Cu60Zr40", "Cu40Zr60", "Zr100",
                "Pd40Cu30Ni10P20", "Pd42.5Cu30Ni10P17.5", "Fe80B20", "Fe75B25",
                "La55Al25Ni20", "La60Al10Ni10Co20", "Mg65Cu25Y10", "Mg70Cu20Y10"
            ],
            "phase_label": [
                "glass", "glass", "crystalline", "crystalline",
                "glass", "glass", "crystalline", "crystalline",
                "glass", "glass", "crystalline", "crystalline"
            ]
        }
        df = pd.DataFrame(data)
        df.to_csv(test_csv, index=False)
    
    yield test_csv
    
    # Cleanup
    if test_csv.exists():
        os.remove(test_csv)

def test_sampling_script_runs(setup_temp_data):
    """Test that sample_dataset.py executes without errors."""
    output_file = "test_sample_output.csv"
    output_path = SAMPLES_DIR / output_file
    
    # Remove existing output if any
    if output_path.exists():
        output_path.unlink()
    
    # Run the script
    result = subprocess.run(
        [
            sys.executable, 
            str(SAMPLE_SCRIPT),
            "--input", str(setup_temp_data),
            "--output", output_file,
            "--target-rows", "6" # Sample 6 rows (half of 12)
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # Assert success
    assert result.returncode == 0, f"Script failed with:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    
    # Assert output file exists
    assert output_path.exists(), f"Output file {output_path} was not created."
    
    # Assert output has correct row count
    df = pd.read_csv(output_path)
    assert len(df) == 6, f"Expected 6 rows, got {len(df)}"
    
    # Assert stratification is preserved (approximate check)
    # Original: 6 glass, 6 crystalline. Sample 6. Expect ~3 glass, ~3 crystalline.
    glass_count = (df["phase_label"] == "glass").sum()
    crystal_count = (df["phase_label"] == "crystalline").sum()
    
    # Allow some variance due to random sampling, but should be balanced
    assert glass_count >= 1 and crystal_count >= 1, "Stratification failed: one class is missing."
    
    # Assert metadata log exists
    log_path = PROJECT_ROOT / "logs" / "sampling_log.json"
    assert log_path.exists(), "Sampling log was not created."

def test_sampling_with_synthetic_data(setup_temp_data):
    """Test sampling when using the default synthetic data path."""
    # Create a synthetic file at the expected default location
    synthetic_path = SAMPLES_DIR / "synthetic_alloys.csv"
    if synthetic_path.exists():
        synthetic_path.unlink()
        
    # Copy test data to synthetic path
    shutil.copy(setup_temp_data, synthetic_path)
    
    try:
        output_file = "test_sample_default_input.csv"
        output_path = SAMPLES_DIR / output_file
        
        if output_path.exists():
            output_path.unlink()
        
        result = subprocess.run(
            [
                sys.executable,
                str(SAMPLE_SCRIPT),
                "--output", output_file,
                "--target-rows", "4"
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"
        assert output_path.exists()
        
        df = pd.read_csv(output_path)
        assert len(df) == 4
    finally:
        # Cleanup
        if synthetic_path.exists():
            synthetic_path.unlink()
        output_path = SAMPLES_DIR / "test_sample_default_input.csv"
        if output_path.exists():
            output_path.unlink()