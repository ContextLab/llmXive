"""
Integration tests for the full training pipeline.
This file contains tests for T020a, T020b, and T020c.
"""
import os
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np

# Add the code directory to the path so we can import project modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.train import main as train_main
from utils.logging_config import initialize_logging

@pytest.fixture
def sample_data_dir():
    """Create a temporary directory with sample data for testing."""
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data", "processed")
    results_dir = os.path.join(temp_dir, "results")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # Generate a sample dataset (200 rows) as per T020a
    np.random.seed(42)
    n_samples = 200

    data = {
        'tolerance_factor': np.random.uniform(0.8, 1.1, n_samples),
        'octahedral_factor': np.random.uniform(0.4, 0.9, n_samples),
        'ionic_radius_mismatch': np.random.uniform(0.0, 0.2, n_samples),
        'electronegativity_diff': np.random.uniform(0.0, 1.5, n_samples),
        'decomposition_energy': np.random.uniform(-0.5, 0.5, n_samples)
    }

    df = pd.DataFrame(data)
    features_path = os.path.join(data_dir, "features.csv")
    df.to_csv(features_path, index=False)

    yield {
        "temp_dir": temp_dir,
        "data_dir": data_dir,
        "results_dir": results_dir,
        "features_path": features_path
    }

    # Cleanup
    shutil.rmtree(temp_dir)

def test_full_training_pipeline_with_sample_data(sample_data_dir):
    """
    T020a + T020b + T020c:
    1. Fixture generates sample dataset (T020a)
    2. Run training pipeline against sample data (T020b)
    3. Assert results/metrics.json exists and contains test_rmse (T020c)
    """
    # Save original environment
    original_cwd = os.getcwd()
    original_data_path = os.environ.get("DATA_PATH", None)
    original_results_path = os.environ.get("RESULTS_PATH", None)

    try:
        # Change to temp directory to simulate project root
        os.chdir(sample_data_dir["temp_dir"])

        # Set environment variables for paths
        os.environ["DATA_PATH"] = sample_data_dir["data_dir"]
        os.environ["RESULTS_PATH"] = sample_data_dir["results_dir"]

        # Initialize logging
        initialize_logging()

        # Run the training pipeline (T020b)
        # The main function should load data, train model, and save artifacts
        train_main()

        # T020c: Assert that results/metrics.json exists and contains test_rmse
        metrics_path = os.path.join(sample_data_dir["results_dir"], "metrics.json")

        assert os.path.exists(metrics_path), f"metrics.json not found at {metrics_path}"

        with open(metrics_path, 'r') as f:
            metrics = json.load(f)

        assert "test_rmse" in metrics, "test_rmse key missing from metrics.json"
        assert isinstance(metrics["test_rmse"], (int, float)), "test_rmse must be numeric"
        assert metrics["test_rmse"] >= 0, "test_rmse must be non-negative"

        # Also verify model.pkl was created (T020b verification)
        model_path = os.path.join(sample_data_dir["results_dir"], "model.pkl")
        assert os.path.exists(model_path), f"model.pkl not found at {model_path}"

    finally:
        # Restore original environment
        os.chdir(original_cwd)
        if original_data_path is not None:
            os.environ["DATA_PATH"] = original_data_path
        elif "DATA_PATH" in os.environ:
            del os.environ["DATA_PATH"]

        if original_results_path is not None:
            os.environ["RESULTS_PATH"] = original_results_path
        elif "RESULTS_PATH" in os.environ:
            del os.environ["RESULTS_PATH"]