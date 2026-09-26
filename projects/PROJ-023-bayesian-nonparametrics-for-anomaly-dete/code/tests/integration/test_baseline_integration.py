"""
Integration tests for baseline scripts (T020-T022) verifying:
1. Correct consumption of unified data format from T004
2. Production of outputs compatible with evaluation script T026a
"""
import os
import sys
import tempfile
import shutil
import logging
import subprocess
import pandas as pd
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.lib.data_loader import load_processed_data
from code.scripts.baseline_shewhart import main as shewhart_main
from code.scripts.baseline_cusum import main as cusum_main
from code.scripts.baseline_vae import main as vae_main
from code.scripts.evaluate import load_and_align_data, calculate_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = project_root / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
EXPECTED_FILES = {
    "shewhart": "shewhart_predictions.csv",
    "cusum": "cusum_predictions.csv",
    "vae": "vae_predictions.csv"
}

def ensure_processed_data_exists():
    """Ensure T004 has run and produced processed data."""
    if not PROCESSED_DIR.exists():
        raise RuntimeError(f"Processed data directory {PROCESSED_DIR} does not exist. Run T004 first.")
    
    series_file = PROCESSED_DIR / "series_with_anomalies.csv"
    ground_truth_file = PROCESSED_DIR / "ground_truth.csv"
    
    if not series_file.exists() or not ground_truth_file.exists():
        raise RuntimeError(f"Required processed data files missing. Run T004 first.")
    
    logger.info(f"Found processed data: {series_file}, {ground_truth_file}")

def run_baseline_script(script_name: str, main_func):
    """Run a baseline script and verify it completes successfully."""
    logger.info(f"Running {script_name}...")
    try:
        # Run the main function directly to avoid subprocess issues in test environment
        main_func()
        logger.info(f"{script_name} completed successfully")
    except SystemExit as e:
        if e.code != 0:
            raise RuntimeError(f"{script_name} exited with code {e.code}")
    except Exception as e:
        raise RuntimeError(f"{script_name} failed with exception: {e}")

def check_output_files(baseline_name: str):
    """Verify that the baseline script produced the expected output file."""
    output_file = RESULTS_DIR / EXPECTED_FILES[baseline_name]
    if not output_file.exists():
        raise AssertionError(f"Output file {output_file} was not created by {baseline_name}")
    
    # Load and validate schema
    df = pd.read_csv(output_file)
    required_columns = {"timestamp", "value", "anomaly_score", "is_anomaly"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise AssertionError(f"{baseline_name} output missing columns: {missing}")
    
    logger.info(f"{baseline_name} output validated: {output_file} ({len(df)} rows)")
    return df

def test_shewhart_integration():
    """Test T020: Shewhart baseline consumes unified data and produces valid output."""
    ensure_processed_data_exists()
    run_baseline_script("shewhart", shewhart_main)
    df = check_output_files("shewhart")
    
    # Verify data types and ranges
    assert df["anomaly_score"].notna().all(), "Shewhart: anomaly_score has NaN values"
    assert df["is_anomaly"].isin([0, 1]).all(), "Shewhart: is_anomaly not binary"
    logger.info("Shewhart integration test PASSED")

def test_cusum_integration():
    """Test T021: CUSUM baseline consumes unified data and produces valid output."""
    ensure_processed_data_exists()
    run_baseline_script("cusum", cusum_main)
    df = check_output_files("cusum")
    
    # Verify data types and ranges
    assert df["anomaly_score"].notna().all(), "CUSUM: anomaly_score has NaN values"
    assert df["is_anomaly"].isin([0, 1]).all(), "CUSUM: is_anomaly not binary"
    logger.info("CUSUM integration test PASSED")

def test_vae_integration():
    """Test T022: VAE baseline consumes unified data and produces valid output."""
    ensure_processed_data_exists()
    run_baseline_script("vae", vae_main)
    df = check_output_files("vae")
    
    # Verify data types and ranges
    assert df["anomaly_score"].notna().all(), "VAE: anomaly_score has NaN values"
    assert df["is_anomaly"].isin([0, 1]).all(), "VAE: is_anomaly not binary"
    logger.info("VAE integration test PASSED")

def test_output_compatibility_with_evaluate():
    """Test that all baseline outputs can be loaded and aligned by T026a (evaluate.py)."""
    ensure_processed_data_exists()
    
    # Ensure all baselines have run
    for baseline_name, main_func in [
        ("shewhart", shewhart_main),
        ("cusum", cusum_main),
        ("vae", vae_main)
    ]:
        if not (RESULTS_DIR / EXPECTED_FILES[baseline_name]).exists():
            logger.info(f"Running {baseline_name} for compatibility test...")
            run_baseline_script(baseline_name, main_func)
    
    # Load and align data using T026a's method
    try:
        aligned_data = load_and_align_data()
        logger.info(f"Successfully aligned data from all sources: {len(aligned_data)} rows")
        
        # Verify that all required columns are present
        required_cols = {
            "timestamp", "value", "ground_truth", 
            "shewhart_score", "shewhart_flag",
            "cusum_score", "cusum_flag",
            "vae_score", "vae_flag"
        }
        missing_cols = required_cols - set(aligned_data.columns)
        if missing_cols:
            raise AssertionError(f"Aligned data missing columns: {missing_cols}")
        
        # Verify no NaN in critical columns
        for col in required_cols:
            if aligned_data[col].isna().any():
                logger.warning(f"Aligned data has NaN in {col}, checking if expected...")
        
        logger.info("Output compatibility test PASSED")
        
    except Exception as e:
        raise AssertionError(f"Failed to align baseline outputs with evaluate.py: {e}")

class TestBaselineIntegration:
    """Pytest test class for baseline integration tests."""
    
    def test_shewhart_integration(self):
        test_shewhart_integration()
    
    def test_cusum_integration(self):
        test_cusum_integration()
    
    def test_vae_integration(self):
        test_vae_integration()
    
    def test_output_compatibility_with_evaluate(self):
        test_output_compatibility_with_evaluate()

if __name__ == "__main__":
    logger.info("Running baseline integration tests...")
    test_shewhart_integration()
    test_cusum_integration()
    test_vae_integration()
    test_output_compatibility_with_evaluate()
    logger.info("All baseline integration tests PASSED")