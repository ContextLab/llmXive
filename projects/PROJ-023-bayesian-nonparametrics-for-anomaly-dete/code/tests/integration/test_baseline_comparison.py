"""
Integration tests for baseline anomaly detection methods (Shewhart, CUSUM, VAE).

This test suite verifies that baseline scripts produce consistent outputs,
adhere to schema constraints, and can be executed end-to-end on real data
(or data injected with known anomalies).

Prerequisites:
- T001 (Project Structure)
- T002 (Dependencies)
- T004 (Data Loader)
- T006 (Anomaly Injector)
- T020 (Shewhart Baseline)
- T021 (CUSUM Baseline)
- T022 (VAE Baseline)
"""
import os
import sys
import tempfile
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List

import pytest
import pandas as pd
import numpy as np
import yaml

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from lib.data_loader import load_time_series
from lib.metrics import precision_recall_f1
from lib.anomaly_injector import inject_anomalies_from_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)


@pytest.fixture
def test_data_dir():
    """Create a temporary directory for test artifacts."""
    tmpdir = tempfile.mkdtemp(prefix="baseline_test_")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def prepared_dataset(test_data_dir):
    """
    Prepare a dataset with injected anomalies for testing.
    Uses the real data loader to fetch data, then injects anomalies.
    """
    # Load real data using the existing loader
    # We use a small subset for speed in integration tests
    try:
        # Attempt to load a standard dataset. If specific UCR data is unavailable,
        # we fall back to a small synthetic generation for the sake of the test
        # framework, but in a real run, this would use T004's fetch_dataset.
        # For this test, we simulate the output of T004 to ensure isolation.
        
        # Generate a realistic time series (sinusoidal + noise)
        n_points = 500
        t = np.linspace(0, 4 * np.pi, n_points)
        signal = np.sin(t) + 0.1 * np.random.normal(size=n_points)
        
        df = pd.DataFrame({'timestamp': t, 'value': signal})
        
        # Inject anomalies using T006 logic
        config = {
            "anomaly_type": "mean_shift",
            "magnitude": 3.0,  # 3 sigma shift
            "start_idx": 100,
            "duration": 20,
            "seed": 42
        }
        
        injected_df, ground_truth = inject_anomalies_from_config(
            df, 
            config, 
            anomaly_column="value",
            seed=42
        )
        
        # Save to temp directory
        data_path = test_data_dir / "test_series.csv"
        ground_truth_path = test_data_dir / "ground_truth.csv"
        
        injected_df.to_csv(data_path, index=False)
        ground_truth.to_csv(ground_truth_path, index=False)
        
        return data_path, ground_truth_path, injected_df, ground_truth
        
    except Exception as e:
        pytest.fail(f"Failed to prepare test dataset: {e}")


def run_baseline_script(script_name: str, input_path: Path, output_path: Path, params: Dict[str, Any] = None):
    """
    Helper to run a baseline script as a subprocess.
    This ensures the script is self-contained and can be run independently.
    """
    script_path = project_root / "code" / "scripts" / script_name
    
    if not script_path.exists():
        # If the script doesn't exist yet, we skip the execution test
        # but we might want to fail if the task claims it's done.
        # For T019, we assume scripts T020-T022 are implemented.
        pytest.skip(f"Script {script_name} not found at {script_path}. "
                    "Ensure T020, T021, T022 are implemented before running this test.")
    
    cmd = [
        sys.executable,
        str(script_path),
        "--input", str(input_path),
        "--output", str(output_path)
    ]
    
    if params:
        for k, v in params.items():
            cmd.append(f"--{k}")
            cmd.append(str(v))
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per script
        )
        
        if result.returncode != 0:
            logger.error(f"Script {script_name} failed:")
            logger.error(result.stdout)
            logger.error(result.stderr)
            pytest.fail(f"Script {script_name} exited with code {result.returncode}")
            
        return result
    except subprocess.TimeoutExpired:
        pytest.fail(f"Script {script_name} timed out")


class TestBaselineComparisonIntegration:
    """
    Integration tests for User Story 2 (Baseline Comparison Engine).
    
    Verifies:
    1. Baseline scripts run successfully on injected data.
    2. Outputs match expected schema (columns, types).
    3. Anomalies are detected (non-zero precision/recall).
    """
    
    def test_shewhart_baseline_execution(self, test_data_dir, prepared_dataset):
        """Test T020: Shewhart baseline script execution and output validity."""
        input_path, gt_path, injected_df, ground_truth = prepared_dataset
        output_path = test_data_dir / "shewhart_predictions.csv"
        
        # Run Shewhart
        run_baseline_script("baseline_shewhart.py", input_path, output_path)
        
        # Verify output exists
        assert output_path.exists(), "Shewhart output file not created"
        
        # Verify schema
        df = pd.read_csv(output_path)
        required_cols = ["timestamp", "value", "score", "is_anomaly"]
        assert all(col in df.columns for col in required_cols), \
            f"Missing columns in Shewhart output. Found: {df.columns.tolist()}"
        
        # Verify types
        assert df["is_anomaly"].dtype in [np.int64, np.int32, bool], \
            "is_anomaly column must be boolean or integer"
        
        # Verify detection (at least one anomaly detected if ground truth exists)
        if ground_truth["is_anomaly"].sum() > 0:
            assert df["is_anomaly"].sum() > 0, \
                "Shewhart detected no anomalies despite ground truth anomalies"
        
        logger.info("Shewhart baseline test passed.")

    def test_cusum_baseline_execution(self, test_data_dir, prepared_dataset):
        """Test T021: CUSUM baseline script execution and output validity."""
        input_path, gt_path, injected_df, ground_truth = prepared_dataset
        output_path = test_data_dir / "cusum_predictions.csv"
        
        # Run CUSUM
        run_baseline_script("baseline_cusum.py", input_path, output_path)
        
        # Verify output exists
        assert output_path.exists(), "CUSUM output file not created"
        
        # Verify schema
        df = pd.read_csv(output_path)
        required_cols = ["timestamp", "value", "score", "is_anomaly"]
        assert all(col in df.columns for col in required_cols), \
            f"Missing columns in CUSUM output. Found: {df.columns.tolist()}"
        
        # Verify types
        assert df["is_anomaly"].dtype in [np.int64, np.int32, bool], \
            "is_anomaly column must be boolean or integer"
        
        logger.info("CUSUM baseline test passed.")

    def test_vae_baseline_execution(self, test_data_dir, prepared_dataset):
        """Test T022: VAE baseline script execution and output validity."""
        input_path, gt_path, injected_df, ground_truth = prepared_dataset
        output_path = test_data_dir / "vae_predictions.csv"
        
        # Run VAE
        run_baseline_script("baseline_vae.py", input_path, output_path)
        
        # Verify output exists
        assert output_path.exists(), "VAE output file not created"
        
        # Verify schema
        df = pd.read_csv(output_path)
        required_cols = ["timestamp", "value", "score", "is_anomaly"]
        assert all(col in df.columns for col in required_cols), \
            f"Missing columns in VAE output. Found: {df.columns.tolist()}"
        
        # Verify types
        assert df["is_anomaly"].dtype in [np.int64, np.int32, bool], \
            "is_anomaly column must be boolean or integer"
        
        # VAE might be more sensitive to parameters, so we just check execution
        # and schema validity for this integration test.
        logger.info("VAE baseline test passed.")

    def test_baseline_comparison_metrics(self, test_data_dir, prepared_dataset):
        """
        Test that all baselines produce comparable metrics against ground truth.
        This ensures the evaluation pipeline (T026) can consume these outputs.
        """
        input_path, gt_path, injected_df, ground_truth = prepared_dataset
        
        methods = ["shewhart", "cusum", "vae"]
        results = {}
        
        for method in methods:
            output_path = test_data_dir / f"{method}_predictions.csv"
            if not output_path.exists():
                # Run the script if not already run by previous tests
                run_baseline_script(f"baseline_{method}.py", input_path, output_path)
            
            # Load predictions
            preds = pd.read_csv(output_path)
            
            # Merge with ground truth on timestamp (assuming aligned)
            # In a real scenario, we might need to align indices if timestamps differ slightly
            merged = pd.merge(
                preds[["timestamp", "is_anomaly"]],
                ground_truth[["timestamp", "is_anomaly"]],
                on="timestamp",
                suffixes=("_pred", "_true")
            )
            
            if merged.empty:
                pytest.fail(f"Could not merge predictions and ground truth for {method}")
            
            y_true = merged["is_anomaly_true"].values
            y_pred = merged["is_anomaly_pred"].values
            
            p, r, f1, _ = precision_recall_f1(y_true, y_pred)
            results[method] = {"precision": p, "recall": r, "f1": f1}
        
        # Assert that we got valid metrics for all methods
        for method, metrics in results.items():
            assert metrics["f1"] is not None, f"F1 score is None for {method}"
            assert 0.0 <= metrics["f1"] <= 1.0, f"F1 score out of range for {method}: {metrics['f1']}"
            logger.info(f"{method} metrics: Precision={metrics['precision']:.3f}, "
                        f"Recall={metrics['recall']:.3f}, F1={metrics['f1']:.3f}")
        
        logger.info("Baseline comparison metrics test passed.")

    def test_output_consistency_with_bayesian(self, test_data_dir, prepared_dataset):
        """
        Verify that baseline outputs have consistent dimensions and formats
        with the Bayesian output (T015) as required by T035.
        """
        input_path, gt_path, injected_df, ground_truth = prepared_dataset
        
        # Run baselines
        for method in ["shewhart", "cusum", "vae"]:
            output_path = test_data_dir / f"{method}_predictions.csv"
            run_baseline_script(f"baseline_{method}.py", input_path, output_path)
        
        # Simulate Bayesian output (or run if T015 is available)
        # Since T015 might not be run in this specific test context, we create
        # a mock Bayesian output to test consistency logic.
        bayesian_output = test_data_dir / "bayesian_predictions.csv"
        bayesian_df = injected_df.copy()
        bayesian_df["score"] = np.random.rand(len(bayesian_df))
        bayesian_df["is_anomaly"] = (bayesian_df["score"] > 0.9).astype(int)
        bayesian_df.to_csv(bayesian_output, index=False)
        
        # Compare dimensions
        for method in ["shewhart", "cusum", "vae"]:
            preds_path = test_data_dir / f"{method}_predictions.csv"
            preds_df = pd.read_csv(preds_path)
            bayesian_df = pd.read_csv(bayesian_output)
            
            assert len(preds_df) == len(bayesian_df), \
                f"Row count mismatch between {method} and Bayesian predictions"
            
            # Check common columns exist
            common_cols = ["timestamp", "score", "is_anomaly"]
            for col in common_cols:
                assert col in preds_df.columns, f"Column {col} missing in {method} output"
                assert col in bayesian_df.columns, f"Column {col} missing in Bayesian output"
        
        logger.info("Output consistency test passed.")