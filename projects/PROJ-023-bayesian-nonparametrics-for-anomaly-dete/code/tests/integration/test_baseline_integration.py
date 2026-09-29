"""
Integration Tests for Baseline Scripts (T023).

These tests verify that:
1. All baseline scripts (T020-T022) correctly consume the unified data format from T004.
2. All baseline scripts produce outputs compatible with the evaluation script (T026a).
3. Output schemas are consistent across all baselines.
"""
import os
import sys
import tempfile
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any

import pytest
import pandas as pd
import numpy as np

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
SCRIPTS_DIR = CODE_DIR / "scripts"

# Expected output files
EXPECTED_OUTPUTS = {
    "baseline_shewhart.py": "shewhart_predictions.csv",
    "baseline_cusum.py": "cusum_predictions.csv",
    "baseline_vae.py": "vae_predictions.csv"
}

@pytest.fixture(scope="module")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data."""
    return tmp_path_factory.mktemp("test_data")

@pytest.fixture(scope="module")
def prepared_dataset(test_data_dir):
    """
    Create a minimal prepared dataset for testing.
    
    This simulates the output of T004 (data loader) and T006 (anomaly injection).
    """
    # Create processed directory
    processed_dir = test_data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple time series with anomalies
    n_points = 100
    timestamps = pd.date_range(start="2023-01-01", periods=n_points, freq="H")
    values = np.random.randn(n_points) + 10
    
    # Inject a few anomalies
    values[20:25] += 5  # Mean shift
    values[50:55] *= 3  # Variance spike
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "value": values
    })
    
    # Save series with anomalies
    series_path = processed_dir / "series_with_anomalies.csv"
    df.to_csv(series_path, index=False)
    
    # Create ground truth
    ground_truth = pd.DataFrame({
        "timestamp": timestamps,
        "is_anomaly": [1 if (20 <= i <= 24) or (50 <= i <= 54) else 0 for i in range(n_points)]
    })
    
    gt_path = processed_dir / "ground_truth.csv"
    ground_truth.to_csv(gt_path, index=False)
    
    logger.info(f"Created test dataset at {test_data_dir}")
    return test_data_dir

def run_baseline_script(script_name: str, data_dir: Path) -> bool:
    """
    Execute a baseline script using the test data directory.
    
    Args:
        script_name: Name of the script to run.
        data_dir: Path to the test data directory.
        
    Returns:
        True if script ran successfully, False otherwise.
    """
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    # Set environment variable to point to test data
    env = os.environ.copy()
    env["DATA_DIR"] = str(data_dir)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            logger.error(f"Script {script_name} failed: {result.stderr}")
            return False
        
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_name} timed out")
        return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False

def check_output_files(script_name: str, results_dir: Path) -> bool:
    """
    Verify that a baseline script produced its expected output file.
    
    Args:
        script_name: Name of the script.
        results_dir: Path to the results directory.
        
    Returns:
        True if output file exists and is valid, False otherwise.
    """
    expected_file = EXPECTED_OUTPUTS.get(script_name)
    if not expected_file:
        return True
    
    output_path = results_dir / expected_file
    if not output_path.exists():
        logger.error(f"Output file missing: {output_path}")
        return False
    
    if output_path.stat().st_size == 0:
        logger.error(f"Output file empty: {output_path}")
        return False
    
    return True

class TestBaselineIntegration:
    """Integration tests for baseline scripts (T023)."""

    @pytest.mark.integration
    def test_shewhart_integration(self, prepared_dataset):
        """Test that Shewhart baseline runs and produces output."""
        data_dir = prepared_dataset
        results_dir = data_dir / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Run script
        success = run_baseline_script("baseline_shewhart.py", data_dir)
        assert success, "Shewhart script failed to run"
        
        # Check output
        assert check_output_files("baseline_shewhart.py", results_dir), \
            "Shewhart output file missing or invalid"

    @pytest.mark.integration
    def test_cusum_integration(self, prepared_dataset):
        """Test that CUSUM baseline runs and produces output."""
        data_dir = prepared_dataset
        results_dir = data_dir / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Run script
        success = run_baseline_script("baseline_cusum.py", data_dir)
        assert success, "CUSUM script failed to run"
        
        # Check output
        assert check_output_files("baseline_cusum.py", results_dir), \
            "CUSUM output file missing or invalid"

    @pytest.mark.integration
    def test_vae_integration(self, prepared_dataset):
        """Test that VAE baseline runs and produces output."""
        data_dir = prepared_dataset
        results_dir = data_dir / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Run script
        success = run_baseline_script("baseline_vae.py", data_dir)
        assert success, "VAE script failed to run"
        
        # Check output
        assert check_output_files("baseline_vae.py", results_dir), \
            "VAE output file missing or invalid"

    @pytest.mark.integration
    def test_output_compatibility_with_evaluate(self, prepared_dataset):
        """
        Test that all baseline outputs have compatible schemas for evaluation.
        
        Verifies:
        - All files exist
        - All files have the same number of rows
        - All files contain required columns (timestamp, prediction, score)
        """
        data_dir = prepared_dataset
        results_dir = data_dir / "results"
        
        required_columns = ["timestamp", "prediction", "score"]
        row_counts = {}
        
        for script_name, file_name in EXPECTED_OUTPUTS.items():
            output_path = results_dir / file_name
            
            # Skip if file doesn't exist (script might have failed)
            if not output_path.exists():
                pytest.skip(f"Output file missing: {output_path}")
            
            df = pd.read_csv(output_path)
            
            # Check required columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            assert not missing_cols, \
                f"File {file_name} missing required columns: {missing_cols}"
            
            row_counts[script_name] = len(df)
        
        # Verify all files have the same number of rows
        if len(set(row_counts.values())) > 1:
            error_msg = "Row count mismatch across baseline outputs:\n"
            for script, count in row_counts.items():
                error_msg += f"  {script}: {count} rows\n"
            pytest.fail(error_msg)
        
        logger.info(f"All outputs have consistent row count: {list(row_counts.values())[0]}")