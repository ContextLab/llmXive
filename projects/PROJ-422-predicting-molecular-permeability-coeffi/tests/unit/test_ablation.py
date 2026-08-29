import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.ablation import load_graph_features_only, train_ablation_model, evaluate_ablation_model

# Mock data for unit tests
def create_mock_graph_features():
    """Create a mock graph_features.csv for testing."""
    data = {
        'mean_degree': [2.5, 3.0, 1.5, 4.0],
        'connectivity': [0.8, 0.9, 0.5, 0.95],
        'substructure_count': [10, 15, 5, 20],
        'target': [2.1, 3.2, 1.1, 4.5]
    }
    df = pd.DataFrame(data)
    return df

class TestAblation:
    @pytest.fixture
    def mock_graph_features_file(self, tmp_path):
        """Create a temporary graph_features.csv file."""
        mock_df = create_mock_graph_features()
        file_path = tmp_path / "graph_features.csv"
        mock_df.to_csv(file_path, index=False)
        return file_path

    def test_load_graph_features_only(self, mock_graph_features_file, monkeypatch):
        """Test that load_graph_features_only correctly loads and splits data."""
        # Monkeypatch the global path
        import analysis.ablation as ablation_module
        original_path = ablation_module.GRAPH_FEATURES_PATH
        ablation_module.GRAPH_FEATURES_PATH = mock_graph_features_file

        try:
            X, y = load_graph_features_only()
            
            assert isinstance(X, np.ndarray)
            assert isinstance(y, np.ndarray)
            assert X.shape[0] == 4  # 4 rows
            assert X.shape[1] == 3  # 3 features (mean_degree, connectivity, substructure_count)
            assert y.shape[0] == 4
            
            # Check values
            assert np.allclose(X[0], [2.5, 0.8, 10])
            assert y[0] == 2.1
        finally:
            ablation_module.GRAPH_FEATURES_PATH = original_path

    def test_load_graph_features_only_missing_file(self, monkeypatch):
        """Test that FileNotFoundError is raised if file is missing."""
        import analysis.ablation as ablation_module
        original_path = ablation_module.GRAPH_FEATURES_PATH
        ablation_module.GRAPH_FEATURES_PATH = Path("/nonexistent/path.csv")

        try:
            with pytest.raises(FileNotFoundError):
                load_graph_features_only()
        finally:
            ablation_module.GRAPH_FEATURES_PATH = original_path

    def test_train_ablation_model(self):
        """Test that train_ablation_model returns a model and metrics."""
        X = np.random.rand(100, 5)
        y = np.random.rand(100)
        
        model, metrics = train_ablation_model(X, y, random_state=42)
        
        assert model is not None
        assert isinstance(metrics, dict)
        assert "training_time_seconds" in metrics
        assert "validation_rmse" in metrics
        assert "validation_r2" in metrics
        assert metrics["n_estimators"] == 200
        assert metrics["max_depth"] == 15

    def test_evaluate_ablation_model(self):
        """Test that evaluate_ablation_model returns correct metrics."""
        # Create a simple model
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X_train = np.random.rand(50, 5)
        y_train = np.random.rand(50)
        model.fit(X_train, y_train)
        
        X_test = np.random.rand(20, 5)
        y_test = np.random.rand(20)
        
        metrics = evaluate_ablation_model(model, X_test, y_test)
        
        assert isinstance(metrics, dict)
        assert metrics["model_type"] == "RandomForest_Ablation_GraphFeatures"
        assert "rmse" in metrics
        assert "mae" in metrics
        assert "r2" in metrics
        assert "n_test_samples" in metrics
        assert metrics["n_test_samples"] == 20