"""
Unit tests for generate_synthetic_test_data.py.
Verifies that the script runs with --test-mode and produces expected artifacts.
"""
import os
import sys
import subprocess
import tempfile
import shutil
import yaml
from pathlib import Path
import pandas as pd
import pytest

# Add code directory to path for imports if needed, though we test via CLI
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
STATE_DIR = PROJECT_ROOT / "state"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_script_requires_test_mode_flag():
    """Test that the script exits if --test-mode is not provided."""
    result = subprocess.run(
        [sys.executable, str(CODE_DIR / "generate_synthetic_test_data.py")],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert "test-mode" in result.stderr or "test-mode" in result.stdout

def test_script_generates_artifacts(temp_output_dir):
    """Test that the script generates the CSV and the manifest."""
    manifest_path = STATE_DIR / "test_artifacts.yaml"
    # Remove existing manifest if present to ensure fresh test
    if manifest_path.exists():
        manifest_path.unlink()

    output_file = Path(temp_output_dir) / "test_data.csv"

    result = subprocess.run(
        [
            sys.executable,
            str(CODE_DIR / "generate_synthetic_test_data.py"),
            "--test-mode",
            "--output-dir",
            str(temp_output_dir),
            "--n-subjects", "1",
            "--n-trials", "1"
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Check CSV exists
    assert output_file.exists(), "Synthetic CSV file was not created."

    # Check manifest exists
    assert manifest_path.exists(), "Test artifacts manifest was not created."

    # Verify CSV content structure
    df = pd.read_csv(output_file)
    required_columns = [
        "subject_id", "trial_id", "timestamp", "pupil_diameter", 
        "x", "y", "search_time", "target_salience", "fixation_count"
    ]
    assert all(col in df.columns for col in required_columns), "CSV missing required columns."

    # Verify manifest content
    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)
    
    assert manifest["mode"] == "TEST_ONLY", "Manifest mode is not TEST_ONLY."
    assert len(manifest["artifacts"]) > 0, "Manifest has no artifacts listed."
    
    # Verify hash is present
    assert "hash" in manifest["artifacts"][0], "Artifact hash is missing."

def test_synthetic_data_contains_nan():
    """Verify that the synthetic data generation includes NaN values (simulating blinks)."""
    # Run generation to a temp location
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "nan_test.csv"
        subprocess.run(
            [
                sys.executable,
                str(CODE_DIR / "generate_synthetic_test_data.py"),
                "--test-mode",
                "--output-dir",
                str(tmpdir),
                "--n-subjects", "1",
                "--n-trials", "1"
            ],
            check=True,
            capture_output=True
        )
        
        df = pd.read_csv(output_file)
        # The generator explicitly inserts NaNs for blinks
        assert df["pupil_diameter"].isna().any(), "Synthetic data should contain NaNs for blinks."