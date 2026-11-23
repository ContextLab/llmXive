import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.ablation import load_graph_features_only, train_ablation_model, evaluate_ablation_model

class TestAblation:
    @pytest.fixture
    def mock_graph_features(self, tmp_path):
        """Create a mock graph_features.csv with topology features only."""
        data = {
            'id': [1, 2, 3, 4, 5],
            'mean_degree': [2.5, 3.0, 2.8, 3.2, 2.9],
            'max_degree': [4, 5, 4, 5, 4],
            'num_rings': [1, 2, 1, 3, 2],
            'aromatic_rings': [1, 1, 0, 2, 1],
            'logP': [2.1, 3.4, 1.2, 4.5, 2.8], # Standard descriptor to be excluded
            'MW': [150, 200, 180, 250, 210],   # Standard descriptor to be excluded
            'target': [1.2, 2.3, 0.8, 3.1, 1.9]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "graph_features.csv"
        df.to_csv(file_path, index=False)
        return file_path, data

    def test_load_graph_features_excludes_descriptors(self, mock_graph_features):
        """Test that load_graph_features_only excludes standard descriptors like MW and logP."""
        path, _ = mock_graph_features
        df, X, y = load_graph_features_only(str(path), target_col='target')
        
        # Check that MW and logP are NOT in the feature columns used for X
        # We can infer this by checking the shape or content if we had column names,
        # but here we just ensure the function runs and returns data.
        # A more robust check would require returning column names.
        assert X.shape[0] == 5
        assert y.shape[0] == 5
        # The number of features should be less than total columns minus target and ID
        # Total cols: 8. Exclude: id, logP, MW, target -> 4 features expected.
        assert X.shape[1] == 4

    def test_train_ablation_model(self, mock_graph_features, tmp_path):
        """Test training the ablation model."""
        path, _ = mock_graph_features
        df, X, y = load_graph_features_only(str(path), target_col='target')
        
        # Split manually for test
        split_idx = 3
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_test, y_test = X[split_idx:], y[split_idx:]
        
        model_path = tmp_path / "ablation_model.pkl"
        model = train_ablation_model(X_train, y_train, X_test, y_test, str(model_path))
        
        assert model is not None
        assert model_path.exists()

    def test_evaluate_ablation_model(self, mock_graph_features, tmp_path):
        """Test evaluating the ablation model."""
        path, _ = mock_graph_features
        df, X, y = load_graph_features_only(str(path), target_col='target')
        
        split_idx = 3
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_test, y_test = X[split_idx:], y[split_idx:]
        
        model_path = tmp_path / "ablation_model.pkl"
        model = train_ablation_model(X_train, y_train, X_test, y_test, str(model_path))
        
        metrics = evaluate_ablation_model(model, X_test, y_test)
        
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert metrics['model_type'] == 'RandomForest_Ablation'
