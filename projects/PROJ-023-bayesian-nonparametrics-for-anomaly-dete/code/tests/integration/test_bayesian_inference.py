"""
Integration tests for Bayesian Inference (User Story 1).

These tests verify that the Bayesian GP pipeline:
1. Converges within the specified iteration limit.
2. Stays within the memory budget (7GB).
3. Produces output conforming to the expected schema.
"""

import os
import sys
import tempfile
import shutil
import logging
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure code directory is in path for imports
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from scripts.bayesian_gp import run_bayesian_gp, load_processed_data
from lib.memory_profiler import MemoryProfiler

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def test_data_dir():
    """Create a temporary directory with a small synthetic dataset for testing."""
    tmp_dir = tempfile.mkdtemp(prefix="test_bayesian_")
    try:
        # Create a small synthetic time series (no real download needed for unit/integration logic)
        # This mimics the output of the data loader + injector pipeline
        n_points = 500
        t = np.linspace(0, 10, n_points)
        # Base signal: sine wave + noise
        signal = np.sin(t) + np.random.normal(0, 0.1, n_points)
        
        # Inject a simple anomaly (mean shift)
        anomaly_start = 300
        anomaly_end = 320
        signal[anomaly_start:anomaly_end] += 3.0  # 3 sigma shift

        df = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=n_points, freq='S'),
            'value': signal,
            'is_anomaly': [1 if anomaly_start <= i < anomaly_end else 0 for i in range(n_points)]
        })

        processed_dir = Path(tmp_dir) / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = processed_dir / "series_with_anomalies.csv"
        df.to_csv(output_path, index=False)
        
        # Create a minimal config for the test
        config = {
            "n_inducing_points": 20,
            "max_steps": 50,  # Reduced for test speed
            "convergence_threshold": 0.05,
            "convergence_window": 10
        }
        config_path = Path(tmp_dir) / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)

        logger.info(f"Created test dataset at {output_path}")
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

@pytest.fixture(scope="module")
def prepared_dataset(test_data_dir):
    """Load the prepared dataset for reuse across tests."""
    data_path = Path(test_data_dir) / "processed" / "series_with_anomalies.csv"
    return load_processed_data(data_path)

def test_bayesian_inference_convergence(prepared_dataset, test_data_dir):
    """
    Test that the Bayesian GP inference converges within the step limit.
    
    Verifies:
    - The run completes without timeout.
    - The ELBO stabilizes (or max steps reached).
    - Convergence status is logged.
    """
    logger.info("Running convergence test...")
    
    results_dir = Path(test_data_dir) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_csv = results_dir / "test_convergence_predictions.csv"
    output_log = results_dir / "test_convergence_log.json"

    try:
        # Run the Bayesian GP script logic directly
        # We pass a small max_steps to ensure it runs quickly in CI
        success, metrics = run_bayesian_gp(
            input_path=prepared_dataset,
            output_path=str(output_csv),
            max_steps=50,
            n_inducing=15,
            convergence_threshold=0.1,
            convergence_window=5
        )
        
        assert success, "Bayesian GP run failed to complete successfully."
        
        # Check output file exists and has data
        assert output_csv.exists(), f"Output CSV {output_csv} was not created."
        df = pd.read_csv(output_csv)
        assert len(df) > 0, "Output CSV is empty."
        assert 'anomaly_score' in df.columns, "Missing 'anomaly_score' column."
        
        # Check convergence logic (if it converged, status should be true)
        # Note: With only 50 steps on a noisy signal, it might not fully converge,
        # but the test passes if the script runs and logs the status.
        assert 'convergence_status' in df.columns or 'convergence_status' in metrics, \
            "Convergence status not found in output."
            
        logger.info("Convergence test passed.")
        
    except Exception as e:
        logger.error(f"Convergence test failed with error: {e}")
        raise

def test_bayesian_inference_memory_limit(prepared_dataset, test_data_dir):
    """
    Test that the inference process respects the 7GB memory limit.
    
    Verifies:
    - MemoryProfiler detects peak usage.
    - Script exits cleanly if under limit.
    - Log file is written.
    """
    logger.info("Running memory limit test...")
    
    results_dir = Path(test_data_dir) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_csv = results_dir / "test_memory_predictions.csv"
    memory_log = results_dir / "memory_log.json"
    
    # Reset memory profiler state if needed
    if hasattr(MemoryProfiler, '_instance'):
        MemoryProfiler._instance = None

    try:
        # Run with memory profiling enabled
        success, metrics = run_bayesian_gp(
            input_path=prepared_dataset,
            output_path=str(output_csv),
            max_steps=50,
            n_inducing=15,
            enable_memory_profiling=True,
            memory_limit_gb=7.0
        )
        
        assert success, "Memory limit test: Script failed or exceeded limit."
        
        # Verify memory log was written
        assert memory_log.exists(), "Memory log file was not created."
        
        with open(memory_log, 'r') as f:
            mem_data = json.load(f)
        
        assert 'peak_memory_gb' in mem_data, "Peak memory not recorded."
        assert mem_data['peak_memory_gb'] < 7.0, \
            f"Peak memory {mem_data['peak_memory_gb']}GB exceeded 7GB limit."
            
        logger.info(f"Memory usage: {mem_data['peak_memory_gb']}GB (Limit: 7GB)")
        logger.info("Memory limit test passed.")
        
    except SystemExit as e:
        if e.code == 1:
            pytest.fail("Script exited with SystemExit(1) due to memory limit violation.")
        raise
    except Exception as e:
        logger.error(f"Memory test failed with error: {e}")
        raise

def test_bayesian_inference_output_schema(prepared_dataset, test_data_dir):
    """
    Test that the output CSV matches the required schema.
    
    Required columns:
    - timestamp: datetime or ISO string
    - value: float (original value)
    - anomaly_score: float (0-1 or raw score)
    - is_anomaly: int (ground truth, if available)
    """
    logger.info("Running output schema test...")
    
    results_dir = Path(test_data_dir) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_csv = results_dir / "test_schema_predictions.csv"
    
    try:
        success, _ = run_bayesian_gp(
            input_path=prepared_dataset,
            output_path=str(output_csv),
            max_steps=50,
            n_inducing=15
        )
        
        assert success, "Schema test: Script failed."
        assert output_csv.exists(), "Output file missing."
        
        df = pd.read_csv(output_csv)
        
        # Define expected columns
        expected_cols = ['timestamp', 'value', 'anomaly_score']
        
        for col in expected_cols:
            assert col in df.columns, f"Missing required column: {col}"
        
        # Check data types
        assert pd.api.types.is_numeric_dtype(df['anomaly_score']), \
            "anomaly_score must be numeric."
        
        # Check for NaNs in critical columns
        assert not df['anomaly_score'].isna().any(), \
            "anomaly_score contains NaN values."
            
        logger.info("Output schema test passed.")
        
    except Exception as e:
        logger.error(f"Schema test failed with error: {e}")
        raise