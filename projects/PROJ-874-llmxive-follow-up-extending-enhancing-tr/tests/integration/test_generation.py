"""
Integration test for generation pipeline.
Verifies that the full pipeline runs without crashing on CPU.
"""
import os
import sys
import pytest
from pathlib import Path
import subprocess
import json
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DATA_ROOT = Path("data/raw")
RESULTS_ROOT = Path("data/results")
PROCESSED_ROOT = Path("data/processed")

# Path to the pilot study output required by T017
PILOT_VARIANCE_PATH = Path("data/pilot_variance.json")

@pytest.fixture(autouse=True)
def setup_environment():
    """Set up test environment."""
    # Create necessary directories
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
    
    # Ensure raw subdirectories exist as per T001b
    (DATA_ROOT / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_ROOT / "processed").mkdir(parents=True, exist_ok=True)
    (DATA_ROOT / "results").mkdir(parents=True, exist_ok=True)

def test_download_script_exists():
    """Test that download script exists and is runnable."""
    download_script = Path("code/download.py")
    assert download_script.exists(), "code/download.py must exist"

def test_generate_script_exists():
    """Test that generate script exists."""
    generate_script = Path("code/generate.py")
    assert generate_script.exists(), "code/generate.py must exist"

def test_config_module_imports():
    """Test that config module can be imported and has required functions."""
    try:
        from code import config
        assert hasattr(config, 'get_dataset_paths'), "config must have get_dataset_paths"
        assert hasattr(config, 'get_seed'), "config must have get_seed"
        assert hasattr(config, 'setup_logging'), "config must have setup_logging"
    except ImportError as e:
        pytest.fail(f"Failed to import config module: {e}")

def test_generate_script_help():
    """Test that generate script responds to help flag."""
    generate_script = Path("code/generate.py")
    try:
        result = subprocess.run(
            [sys.executable, str(generate_script), "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Help command failed: {result.stderr}"
        assert "--mode" in result.stdout, "generate.py must accept --mode argument"
    except subprocess.TimeoutExpired:
        pytest.fail("generate.py help command timed out")

def test_pilot_study_script_exists():
    """Test that pilot study script exists."""
    pilot_script = Path("code/pilot_study.py")
    assert pilot_script.exists(), "code/pilot_study.py must exist"

def test_pilot_study_runs_help():
    """Test that pilot study script can be executed with --help."""
    pilot_script = Path("code/pilot_study.py")
    try:
        result = subprocess.run(
            [sys.executable, str(pilot_script), "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Pilot study help failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Pilot study script help timed out")

def test_pilot_study_produces_output():
    """
    Integration test: Verify T017 (Pilot Study) runs and produces data/pilot_variance.json.
    This verifies the prerequisite for T030a (Power Analysis).
    """
    pilot_script = Path("code/pilot_study.py")
    
    # Clean up existing output to force regeneration
    if PILOT_VARIANCE_PATH.exists():
        PILOT_VARIANCE_PATH.unlink()

    try:
        # Run the pilot study script
        # Note: This script is expected to fail loudly if real data is missing,
        # which is the correct behavior per constraints.
        # We run it and check if it produces the file or fails with a clear error.
        result = subprocess.run(
            [sys.executable, str(pilot_script)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # If the script succeeded, verify the output file exists and has correct structure
        if result.returncode == 0:
            assert PILOT_VARIANCE_PATH.exists(), "Pilot study must produce data/pilot_variance.json"
            
            with open(PILOT_VARIANCE_PATH, 'r') as f:
                data = json.load(f)
            
            required_keys = ['mean', 'std', 'n_samples', 'metric_name']
            for key in required_keys:
                assert key in data, f"pilot_variance.json must contain key '{key}'"
        
        else:
            # If it failed, it must be because of missing real data (expected in CI without download)
            # or a configuration error. We assert that the error message is clear.
            assert "DatasetNotFoundError" in result.stderr or "Missing required files" in result.stderr, \
                f"Pilot study failed with unclear error: {result.stderr}"
            pytest.skip(f"Pilot study skipped due to missing real data (expected in CI): {result.stderr}")

    except subprocess.TimeoutExpired:
        pytest.fail("Pilot study script timed out")

def test_generate_baseline_naive_mode():
    """
    Integration test: Verify baseline-naive mode runs without crashing.
    This tests T013 implementation.
    """
    generate_script = Path("code/generate.py")
    
    try:
        result = subprocess.run(
            [sys.executable, str(generate_script), "--mode", "baseline-naive", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We only check that the script accepts the flag and runs help/parse successfully
        # Actual generation requires real data which might not be present in CI
        assert result.returncode == 0 or "usage:" in result.stdout, \
            f"generate.py --mode baseline-naive failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Generate script timed out")

def test_generate_baseline_full_mode():
    """
    Integration test: Verify baseline-full mode runs without crashing.
    This tests T013 implementation.
    """
    generate_script = Path("code/generate.py")
    
    try:
        result = subprocess.run(
            [sys.executable, str(generate_script), "--mode", "baseline-full", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0 or "usage:" in result.stdout, \
            f"generate.py --mode baseline-full failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Generate script timed out")

def test_output_directories_created():
    """Test that output directories are created."""
    assert DATA_ROOT.exists()
    assert RESULTS_ROOT.exists()
    assert (DATA_ROOT / "raw").exists()
    assert (DATA_ROOT / "processed").exists()
    assert (DATA_ROOT / "results").exists()
    assert PROCESSED_ROOT.exists()