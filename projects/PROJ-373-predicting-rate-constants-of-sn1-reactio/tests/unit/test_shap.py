"""
Unit test for SHAP value generation in the interpretability module.

This test verifies that the SHAP analysis pipeline correctly:
1. Loads the trained model and processed data
2. Computes SHAP values for the test set
3. Generates a summary plot
4. Produces a feature importance ranking

Dependencies:
- T026: Implementation of code/analysis/interpret.py
- T022: Availability of model artifacts (best_model.pt, metrics.json)
- T016: Availability of processed dataset (cleaned_sn1.csv)
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.interpret import (
    load_model_and_weights,
    load_processed_data,
    prepare_graph_features,
    run_inference,
    calculate_r2,
    run_interpretability_analysis
)
from models.mpnn import MPNN, MPNNConfig
import torch


class TestSHAPGeneration:
    """Test suite for SHAP value generation functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test fixtures and clean up after tests."""
        # Create temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.test_dir) / "artifacts"
        self.artifacts_dir.mkdir()
        self.data_dir = Path(self.test_dir) / "data" / "processed"
        self.data_dir.mkdir(parents=True)
        
        # Save original paths for restoration
        self.original_artifacts_path = os.environ.get("ARTIFACTS_PATH")
        self.original_data_path = os.environ.get("DATA_PATH")
        
        # Set test paths
        os.environ["ARTIFACTS_PATH"] = str(self.artifacts_dir)
        os.environ["DATA_PATH"] = str(self.data_dir.parent)
        
        yield
        
        # Restore original paths
        if self.original_artifacts_path:
            os.environ["ARTIFACTS_PATH"] = self.original_artifacts_path
        elif "ARTIFACTS_PATH" in os.environ:
            del os.environ["ARTIFACTS_PATH"]
            
        if self.original_data_path:
            os.environ["DATA_PATH"] = self.original_data_path
        elif "DATA_PATH" in os.environ:
            del os.environ["DATA_PATH"]
        
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def _create_mock_model_and_data(self):
        """Create mock model and data for testing."""
        # Create mock processed data
        n_samples = 50
        n_features = 10
        
        data = {
            'smiles': [f"CC(C)(C)Br{i}" for i in range(n_samples)],
            'rate_constant': np.random.uniform(0.1, 10.0, n_samples),
            'substrate_class': np.random.choice(['secondary', 'tertiary'], n_samples),
            'gasteiger_charges': [np.random.uniform(-1, 1, 5).tolist() for _ in range(n_samples)],
            'topological_indices': [np.random.uniform(0, 5, 5).tolist() for _ in range(n_samples)]
        }
        
        df = pd.DataFrame(data)
        test_df = df.iloc[:20]  # Use subset for test
        
        # Save test data
        test_path = self.data_dir / "test.csv"
        test_df.to_csv(test_path, index=False)
        
        # Create mock model
        config = MPNNConfig(
            node_features=5,
            edge_features=0,
            hidden_dim=16,
            num_layers=2,
            output_dim=1
        )
        model = MPNN(config)
        
        # Save model
        model_path = self.artifacts_dir / "best_model.pt"
        torch.save({
            'model_state_dict': model.state_dict(),
            'config': {
                'node_features': config.node_features,
                'edge_features': config.edge_features,
                'hidden_dim': config.hidden_dim,
                'num_layers': config.num_layers,
                'output_dim': config.output_dim
            }
        }, model_path)
        
        # Create mock metrics
        metrics = {
            'r2': 0.75,
            'mae': 0.5,
            'model_id': 'test_model'
        }
        metrics_path = self.artifacts_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)
        
        return model, test_path, metrics

    def test_load_model_and_weights(self):
        """Test that model loading works correctly."""
        model, _, _ = self._create_mock_model_and_data()
        
        loaded_model, loaded_config = load_model_and_weights()
        
        assert loaded_model is not None
        assert loaded_config is not None
        assert isinstance(loaded_config, dict)
        assert 'node_features' in loaded_config

    def test_load_processed_data(self):
        """Test that data loading works correctly."""
        _, test_path, _ = self._create_mock_model_and_data()
        
        test_data = load_processed_data(test_path)
        
        assert test_data is not None
        assert isinstance(test_data, pd.DataFrame)
        assert len(test_data) > 0
        assert 'smiles' in test_data.columns
        assert 'rate_constant' in test_data.columns

    def test_prepare_graph_features(self):
        """Test graph feature preparation."""
        model, test_path, _ = self._create_mock_model_and_data()
        test_data = load_processed_data(test_path)
        
        # Prepare features for a subset
        subset_data = test_data.head(5)
        features, edge_indices, batch = prepare_graph_features(subset_data)
        
        assert features is not None
        assert edge_indices is not None
        assert batch is not None
        assert isinstance(features, torch.Tensor)
        assert isinstance(edge_indices, torch.Tensor)
        assert isinstance(batch, torch.Tensor)

    def test_run_inference(self):
        """Test model inference."""
        model, test_path, _ = self._create_mock_model_and_data()
        test_data = load_processed_data(test_path)
        
        # Prepare features
        features, edge_indices, batch = prepare_graph_features(test_data.head(5))
        
        # Run inference
        predictions = run_inference(model, features, edge_indices, batch)
        
        assert predictions is not None
        assert isinstance(predictions, torch.Tensor)
        assert len(predictions) == 5

    def test_calculate_r2(self):
        """Test R2 calculation."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])
        
        r2 = calculate_r2(y_true, y_pred)
        
        assert 0 <= r2 <= 1
        assert isinstance(r2, float)

    def test_run_interpretability_analysis(self):
        """Test full interpretability analysis pipeline."""
        model, test_path, metrics = self._create_mock_model_and_data()
        
        # Run interpretability analysis
        results = run_interpretability_analysis(
            test_path,
            shap_samples=10,
            output_dir=str(self.artifacts_dir)
        )
        
        assert results is not None
        assert 'shap_values' in results
        assert 'feature_importance' in results
        assert 'r2_score' in results
        
        # Verify SHAP values are computed
        assert len(results['shap_values']) > 0
        assert isinstance(results['shap_values'][0], (list, np.ndarray))
        
        # Verify feature importance is computed
        assert len(results['feature_importance']) > 0
        assert isinstance(results['feature_importance'], dict)
        
        # Verify R2 score is reasonable
        assert 0 <= results['r2_score'] <= 1

    def test_shap_values_shape(self):
        """Test that SHAP values have correct shape."""
        model, test_path, _ = self._create_mock_model_and_data()
        test_data = load_processed_data(test_path)
        
        # Run interpretability with small sample
        results = run_interpretability_analysis(
            test_path,
            shap_samples=5,
            output_dir=str(self.artifacts_dir)
        )
        
        shap_values = results['shap_values']
        
        # Each sample should have SHAP values for each feature
        assert len(shap_values) == 5
        for sample_values in shap_values:
            assert len(sample_values) > 0

    def test_feature_importance_ranking(self):
        """Test that feature importance ranking is generated."""
        model, test_path, _ = self._create_mock_model_and_data()
        
        results = run_interpretability_analysis(
            test_path,
            shap_samples=10,
            output_dir=str(self.artifacts_dir)
        )
        
        feature_importance = results['feature_importance']
        
        # Should have at least one feature with importance
        assert len(feature_importance) > 0
        
        # Should be a dictionary with feature names as keys
        for feature_name, importance in feature_importance.items():
            assert isinstance(feature_name, str)
            assert isinstance(importance, (int, float))
            assert importance >= 0

    def test_output_files_created(self):
        """Test that output files are created in the specified directory."""
        model, test_path, _ = self._create_mock_model_and_data()
        
        results = run_interpretability_analysis(
            test_path,
            shap_samples=5,
            output_dir=str(self.artifacts_dir)
        )
        
        # Check that output files exist
        importance_file = self.artifacts_dir / "feature_importance.csv"
        summary_file = self.artifacts_dir / "shap_summary.json"
        
        # Note: The actual implementation should create these files
        # This test documents the expected behavior
        assert importance_file.exists() or summary_file.exists(), \
            "At least one output file should be created"

    def test_error_handling_invalid_data(self):
        """Test error handling for invalid data."""
        # Create invalid test file
        invalid_path = self.data_dir / "invalid.csv"
        with open(invalid_path, 'w') as f:
            f.write("invalid,data\n")
        
        with pytest.raises((KeyError, ValueError, FileNotFoundError)):
            load_processed_data(invalid_path)

    def test_error_handling_missing_model(self):
        """Test error handling for missing model."""
        # Remove model file
        model_path = self.artifacts_dir / "best_model.pt"
        if model_path.exists():
            model_path.unlink()
        
        with pytest.raises(FileNotFoundError):
            load_model_and_weights()

    def test_consistency_across_runs(self):
        """Test that results are consistent across multiple runs (with fixed seed)."""
        model, test_path, _ = self._create_mock_model_and_data()
        
        # Run twice
        results1 = run_interpretability_analysis(
            test_path,
            shap_samples=5,
            output_dir=str(self.artifacts_dir)
        )
        
        results2 = run_interpretability_analysis(
            test_path,
            shap_samples=5,
            output_dir=str(self.artifacts_dir)
        )
        
        # Feature importance should be similar (not identical due to SHAP sampling)
        # But the top features should be the same
        top_features1 = sorted(results1['feature_importance'].items(), 
                             key=lambda x: x[1], reverse=True)[:3]
        top_features2 = sorted(results2['feature_importance'].items(), 
                             key=lambda x: x[1], reverse=True)[:3]
        
        # At least 2 out of 3 top features should match
        overlap = len(set([f[0] for f in top_features1]) & 
                     set([f[0] for f in top_features2]))
        assert overlap >= 2, "Top features should be consistent across runs"