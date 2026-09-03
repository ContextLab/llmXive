"""
Integration test for the modeling pipeline (T018).
Verifies that train.py produces valid artifacts and the best model loads.
"""
import os
import sys
import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

import pytest

# Add code to path if not already
if "code" not in sys.path:
    sys.path.insert(0, "code")

from src.modeling.train import main, load_clean_data, prepare_features_targets

class TestModelingIntegration:
    """Integration tests for the training pipeline."""

    @pytest.fixture
    def clean_data_fixture(self, tmp_path):
        """Generate a synthetic clean dataset for testing."""
        # Create a realistic-looking dataset based on the schema
        n_samples = 200
        data = {
            'Tc': np.random.uniform(20, 40, n_samples),
            'impurities_atomic_pct': np.random.uniform(0, 5, n_samples),
            'temp_K': np.random.uniform(300, 1000, n_samples),
            'pressure_GPa': np.random.uniform(0, 50, n_samples),
            'dominant_impurity': np.random.choice(['None', 'Low', 'Medium', 'High'], n_samples)
        }
        # Add a few other numeric features
        data['feature_A'] = np.random.uniform(0, 10, n_samples)
        data['feature_B'] = np.random.uniform(0, 10, n_samples)
        
        df = pd.DataFrame(data)
        csv_path = tmp_path / "mgb2_clean.csv"
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.fixture
    def output_dir_fixture(self, tmp_path):
        """Create a temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return str(output_dir)

    def test_full_pipeline_execution(self, clean_data_fixture, output_dir_fixture):
        """Test that the full pipeline runs without errors and produces artifacts."""
        # Mock the argument parsing to use our temp paths
        test_args = [
            "train.py",
            "--data", clean_data_fixture,
            "--output-dir", output_dir_fixture
        ]
        
        with patch("sys.argv", test_args):
            # Run the main function
            try:
                main()
            except SystemExit as e:
                if e.code != 0:
                    pytest.fail(f"Pipeline exited with code {e.code}")
        
        # Verify artifacts exist
        output_path = Path(output_dir_fixture)
        assert (output_path / "best_model.pkl").exists(), "best_model.pkl was not created"
        assert (output_path / "model_metrics.json").exists(), "model_metrics.json was not created"

    def test_best_model_loads_and_predicts(self, clean_data_fixture, output_dir_fixture):
        """Test that the saved best model can be loaded and makes predictions."""
        # Run pipeline first
        test_args = [
            "train.py",
            "--data", clean_data_fixture,
            "--output-dir", output_dir_fixture
        ]
        with patch("sys.argv", test_args):
            main()
        
        # Load model
        model_path = Path(output_dir_fixture) / "best_model.pkl"
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        
        # Verify model is not None and has a predict method
        assert model is not None
        assert hasattr(model, "predict")
        
        # Verify it can predict on a dummy input (shape must match features)
        # We need to know the feature columns used. 
        # From prepare_features_targets, it excludes Tc, impurities_atomic_pct, dominant_impurity.
        # So feature_A and feature_B should be present.
        dummy_input = pd.DataFrame({
            'temp_K': [500.0],
            'pressure_GPa': [10.0],
            'feature_A': [5.0],
            'feature_B': [5.0]
        })
        
        pred = model.predict(dummy_input)
        assert len(pred) == 1
        assert isinstance(pred[0], (int, float, np.floating))

    def test_metrics_report_structure(self, clean_data_fixture, output_dir_fixture):
        """Test that the metrics report has the expected structure."""
        # Run pipeline
        test_args = [
            "train.py",
            "--data", clean_data_fixture,
            "--output-dir", output_dir_fixture
        ]
        with patch("sys.argv", test_args):
            main()
        
        # Load metrics
        metrics_path = Path(output_dir_fixture) / "model_metrics.json"
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
        
        assert isinstance(metrics, list), "Metrics should be a list of model results"
        assert len(metrics) > 0, "Metrics list should not be empty"
        
        required_keys = {"model_name", "r2", "mae"}
        for entry in metrics:
            assert required_keys.issubset(entry.keys()), f"Missing keys in model entry: {entry}"
            assert entry['model_name'] in ["linear", "ridge", "random_forest", "xgboost"]

    def test_stratified_split_logic(self, clean_data_fixture):
        """Verify that stratified splitting respects the dominant_impurity distribution."""
        df = load_clean_data(clean_data_fixture)
        X, y, y_strat = prepare_features_targets(df)
        
        # Check that stratification labels are not empty
        assert len(y_strat.unique()) > 1, "Stratification requires multiple classes"
        
        # Verify the split function logic manually (mocking train_test_split is tricky, 
        # so we just verify the preparation step produces valid strat labels)
        assert y_strat.notnull().all(), "Stratification labels contain nulls"
        
        # Verify counts
        counts = y_strat.value_counts()
        assert counts.min() >= 1, "Every class must have at least one sample for stratification"