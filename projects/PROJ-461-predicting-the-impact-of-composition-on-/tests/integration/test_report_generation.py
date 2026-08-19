"""
Integration test for report generation with a mock model.

This test verifies that the report generation pipeline in code/analysis/report.py
functions correctly end-to-end when provided with a mock model and data.
It ensures that all required artifacts (plots and JSON files) are generated
and saved to the correct locations.

Prerequisites:
- A trained model (mocked via a pre-trained LightGBM or sklearn model)
- Processed data (mocked or loaded from data/clean_data.csv if available)
- The code/analysis/report.py module must be implemented and runnable.
"""
import json
import os
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingRegressor

# Ensure the project root is in the path for imports
import sys
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from code.analysis import report
from code.config import Config, load_config
from code.utils.logger import get_logger

logger = get_logger(__name__)


def create_mock_model_and_data():
    """
    Creates a mock trained model and a synthetic dataset for integration testing.
    This is used because the real model might not be trained yet or we want
    a deterministic test environment.
    """
    # Create a simple mock model using sklearn to ensure it's a real estimator
    mock_model = GradientBoostingRegressor(
        n_estimators=10,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )
    
    # Generate synthetic data that mimics the expected structure
    # Columns: mean_atomic_mass, mean_atomic_radius, electronegativity_variance,
    #          atomic_radius_mismatch, packing_efficiency, density_residual
    n_samples = 100
    X = np.random.rand(n_samples, 5)
    y = np.random.rand(n_samples)
    
    mock_model.fit(X, y)
    
    # Create a DataFrame with the expected column names for the report
    data_dict = {
        'mean_atomic_mass': X[:, 0],
        'mean_atomic_radius': X[:, 1],
        'electronegativity_variance': X[:, 2],
        'atomic_radius_mismatch': X[:, 3],
        'packing_efficiency': X[:, 4],
        'density_residual': y,
        'predicted_residual': mock_model.predict(X)
    }
    df = pd.DataFrame(data_dict)
    
    return mock_model, df


@pytest.fixture
def temp_test_dir():
    """Creates a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_report_generation_full_pipeline(temp_test_dir):
    """
    Integration test: Runs the full report generation pipeline with a mock model.
    
    Verifies:
    1. The report module can be imported and functions called without error.
    2. All expected output files are created in the reports directory.
    3. The generated files are non-empty and valid (e.g., JSON is parseable).
    """
    # Setup paths
    reports_dir = temp_test_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    mock_model, mock_data = create_mock_model_and_data()
    
    # Save mock model
    model_path = temp_test_dir / "models"
    model_path.mkdir(parents=True, exist_ok=True)
    model_file = model_path / "mock_model.pkl"
    with open(model_file, "wb") as f:
        pickle.dump(mock_model, f)
    
    # Save mock data (simulating the processed data that would be loaded)
    data_path = temp_test_dir / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    data_file = data_path / "clean_data.csv"
    mock_data.to_csv(data_file, index=False)
    
    # Create a mock config
    config = Config(
        seed=42,
        data_dir=data_path,
        model_dir=model_path,
        report_dir=reports_dir
    )
    
    # Mock the load_config function to return our test config
    with patch.object(report, 'load_config', return_value=config):
        # Mock the load_model function to return our mock model
        with patch.object(report, 'load_model', return_value=mock_model):
            # Mock the load_processed_data function to return our mock data
            with patch.object(report, 'load_processed_data', return_value=mock_data):
                # Mock the calculate_model_metrics to return fixed metrics
                mock_metrics = {
                    'mae': 0.15,
                    'r2': 0.85,
                    'rmse': 0.18
                }
                with patch.object(report, 'calculate_model_metrics', return_value=mock_metrics):
                    # Mock the calculate_baseline_metrics for completeness
                    mock_baseline = {
                        'mae': 0.25,
                        'r2': 0.60,
                        'rmse': 0.30
                    }
                    with patch.object(report, 'calculate_baseline_metrics', return_value=mock_baseline):
                        # Execute the main report generation function
                        try:
                            report.main()
                        except Exception as e:
                            logger.error(f"Report generation failed: {e}")
                            raise
    
    # Verify outputs exist
    expected_files = [
        reports_dir / "predicted_vs_actual.png",
        reports_dir / "shap_summary.png",
        reports_dir / "sensitivity_analysis.json",
        reports_dir / "metrics.json",
        reports_dir / "analysis_report.html"
    ]
    
    # Check for PDP if MAE > 0.1 (our mock MAE is 0.15)
    if mock_metrics['mae'] > 0.1:
        expected_files.append(reports_dir / "pdp_radius_mismatch.png")
    
    for file_path in expected_files:
        assert file_path.exists(), f"Expected output file not found: {file_path}"
        assert file_path.stat().st_size > 0, f"Output file is empty: {file_path}"
    
    # Validate JSON content
    metrics_file = reports_dir / "metrics.json"
    with open(metrics_file, "r") as f:
        metrics_data = json.load(f)
        assert "mae" in metrics_data
        assert "r2" in metrics_data
    
    sensitivity_file = reports_dir / "sensitivity_analysis.json"
    with open(sensitivity_file, "r") as f:
        sensitivity_data = json.load(f)
        assert isinstance(sensitivity_data, dict)
    
    logger.info("Integration test for report generation passed successfully.")