"""
Integration tests for baseline anomaly detection methods (Shewhart, CUSUM, VAE).

This module verifies that the baseline scripts correctly execute, consume the
unified data format, and produce outputs compatible with the evaluation schema.

Tests:
    test_shewhart_detection: Validates Shewhart baseline execution and output schema.
    test_cusum_detection: Validates CUSUM baseline execution and output schema.
    test_vae_reconstruction: Validates VAE baseline execution and output schema.
"""

import os
import sys
import tempfile
import shutil
import logging
import subprocess
import pandas as pd
import pytest
from pathlib import Path

# Configure logging for test visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is two levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"

# Ensure results directory exists for test artifacts
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def test_data_dir():
    """
    Ensure the test data directory exists and contains necessary processed files.
    This fixture assumes T004 (data_loader) and T006 (anomaly_injector) have run.
    """
    data_dir = DATA_DIR / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for expected files from previous tasks (T004, T006)
    # If they don't exist, the test suite assumes the pipeline hasn't run yet.
    # In a CI/CD context, this fixture would ensure setup is run first.
    series_file = data_dir / "series_with_anomalies.csv"
    ground_truth_file = data_dir / "ground_truth.csv"
    
    if not series_file.exists() or not ground_truth_file.exists():
        logger.warning(
            "Processed data files not found. "
            "Ensure T004 (data_loader) and T006 (anomaly_injector) have been executed."
        )
    
    return data_dir


@pytest.fixture(scope="module")
def prepared_dataset(test_data_dir):
    """
    Fixture to verify that a prepared dataset exists.
    Returns the path to the processed time series file.
    """
    series_file = test_data_dir / "series_with_anomalies.csv"
    if not series_file.exists():
        pytest.skip(
            f"Required data file {series_file} not found. "
            "Run T004 and T006 to generate processed data."
        )
    return series_file


def run_baseline_script(script_name: str, output_file: Path) -> bool:
    """
    Helper function to run a baseline script via subprocess.
    
    Args:
        script_name: Name of the script in code/scripts/ (e.g., 'baseline_shewhart.py')
        output_file: Expected output file path to verify after execution.
        
    Returns:
        True if script executed successfully and output file exists, False otherwise.
    """
    script_path = CODE_DIR / "scripts" / script_name
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Running {script_name}...")
    
    try:
        # Run the script using the project's Python environment
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for heavy models like VAE
        )
        
        if result.returncode != 0:
            logger.error(f"Script {script_name} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        if not output_file.exists():
            logger.error(f"Output file {output_file} was not created by {script_name}")
            return False
        
        logger.info(f"Successfully ran {script_name} and created {output_file}")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_name} timed out")
        return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False


class TestBaselineComparisonIntegration:
    """
    Integration tests for User Story 2: Baseline Comparison Engine.
    
    These tests verify that the baseline scripts (Shewhart, CUSUM, VAE)
    can be executed, produce valid output files, and that the output
    conforms to the expected schema (columns, types).
    """

    def test_shewhart_detection(self, prepared_dataset):
        """
        Test Shewhart baseline detection.
        
        Verifies:
            1. baseline_shewhart.py runs without error.
            2. data/results/shewhart_predictions.csv is created.
            3. Output contains required columns: 'timestamp', 'score', 'anomaly_flag'.
        """
        output_file = RESULTS_DIR / "shewhart_predictions.csv"
        
        # Clean up previous run if exists
        if output_file.exists():
            output_file.unlink()
        
        success = run_baseline_script("baseline_shewhart.py", output_file)
        assert success, "Shewhart baseline script failed to execute or produce output"
        
        # Validate output schema
        df = pd.read_csv(output_file)
        required_columns = {'timestamp', 'score', 'anomaly_flag'}
        assert required_columns.issubset(df.columns), \
            f"Shewhart output missing required columns. Found: {df.columns.tolist()}"
        
        # Validate data types
        assert df['score'].dtype in ['float64', 'float32', 'int64', 'int32'], \
            f"Score column must be numeric. Found: {df['score'].dtype}"
        assert df['anomaly_flag'].dtype in ['bool', 'int64', 'int32', 'float64'], \
            f"Anomaly flag must be boolean-like. Found: {df['anomaly_flag'].dtype}"
        
        logger.info(f"Shewhart test passed. Output shape: {df.shape}")


    def test_cusum_detection(self, prepared_dataset):
        """
        Test CUSUM baseline detection.
        
        Verifies:
            1. baseline_cusum.py runs without error.
            2. data/results/cusum_predictions.csv is created.
            3. Output contains required columns: 'timestamp', 'score', 'anomaly_flag'.
        """
        output_file = RESULTS_DIR / "cusum_predictions.csv"
        
        # Clean up previous run if exists
        if output_file.exists():
            output_file.unlink()
        
        success = run_baseline_script("baseline_cusum.py", output_file)
        assert success, "CUSUM baseline script failed to execute or produce output"
        
        # Validate output schema
        df = pd.read_csv(output_file)
        required_columns = {'timestamp', 'score', 'anomaly_flag'}
        assert required_columns.issubset(df.columns), \
            f"CUSUM output missing required columns. Found: {df.columns.tolist()}"
        
        # Validate data types
        assert df['score'].dtype in ['float64', 'float32', 'int64', 'int32'], \
            f"Score column must be numeric. Found: {df['score'].dtype}"
        assert df['anomaly_flag'].dtype in ['bool', 'int64', 'int32', 'float64'], \
            f"Anomaly flag must be boolean-like. Found: {df['anomaly_flag'].dtype}"
        
        logger.info(f"CUSUM test passed. Output shape: {df.shape}")


    def test_vae_reconstruction(self, prepared_dataset):
        """
        Test VAE baseline reconstruction error detection.
        
        Verifies:
            1. baseline_vae.py runs without error.
            2. data/results/vae_predictions.csv is created.
            3. Output contains required columns: 'timestamp', 'score', 'anomaly_flag'.
        
        Note: VAE training is computationally intensive. This test includes a timeout.
        """
        output_file = RESULTS_DIR / "vae_predictions.csv"
        
        # Clean up previous run if exists
        if output_file.exists():
            output_file.unlink()
        
        success = run_baseline_script("baseline_vae.py", output_file)
        assert success, "VAE baseline script failed to execute or produce output"
        
        # Validate output schema
        df = pd.read_csv(output_file)
        required_columns = {'timestamp', 'score', 'anomaly_flag'}
        assert required_columns.issubset(df.columns), \
            f"VAE output missing required columns. Found: {df.columns.tolist()}"
        
        # Validate data types
        assert df['score'].dtype in ['float64', 'float32', 'int64', 'int32'], \
            f"Score column must be numeric. Found: {df['score'].dtype}"
        assert df['anomaly_flag'].dtype in ['bool', 'int64', 'int32', 'float64'], \
            f"Anomaly flag must be boolean-like. Found: {df['anomaly_flag'].dtype}"
        
        # VAE scores are typically reconstruction errors (MSE), so they should be non-negative
        assert (df['score'] >= 0).all(), "VAE reconstruction scores should be non-negative"
        
        logger.info(f"VAE test passed. Output shape: {df.shape}")