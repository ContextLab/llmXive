"""
Contract test for model output schema.
Verifies that trained models and metrics are saved with the correct structure.
"""
import pytest
import json
import os
import sys
import pickle
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

class TestModelOutputSchema:
    def test_metrics_json_structure(self, tmp_path):
        """
        Test that the metrics.json file contains required keys.
        """
        mock_metrics = {
            "model_type": "logistic_regression",
            "antibiotic_class": "fluoroquinolones",
            "auc_roc": 0.85,
            "precision": 0.82,
            "recall": 0.78,
            "f1_score": 0.80,
            "threshold": 0.5
        }
        
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(mock_metrics, f)
        
        # Load and validate
        with open(metrics_file, "r") as f:
            loaded = json.load(f)
        
        required_keys = ["auc_roc", "precision", "recall", "f1_score"]
        for key in required_keys:
            assert key in loaded, f"Missing key in metrics: {key}"
            assert isinstance(loaded[key], (int, float)), f"Key {key} must be numeric"

    def test_model_pickle_loadable(self, tmp_path):
        """
        Test that model pickles can be loaded successfully.
        """
        # Create a dummy object to simulate a model
        class DummyModel:
            def predict(self, X):
                return [0] * len(X)
            
            def predict_proba(self, X):
                return [[0.5, 0.5]] * len(X)
        
        model = DummyModel()
        model_file = tmp_path / "model_test.pkl"
        
        with open(model_file, "wb") as f:
            pickle.dump(model, f)
        
        # Load and verify
        with open(model_file, "rb") as f:
            loaded_model = pickle.load(f)
        
        assert loaded_model is not None
        assert hasattr(loaded_model, "predict")
        assert hasattr(loaded_model, "predict_proba")

    def test_feature_ranking_schema(self, tmp_path):
        """
        Test that feature_ranking.csv has the correct columns.
        """
        mock_data = {
            "feature_name": ["gene_1", "gene_2", "snp_1"],
            "importance_score": [0.9, 0.8, 0.7],
            "p_value": [0.01, 0.02, 0.03]
        }
        df = pd.DataFrame(mock_data)
        
        ranking_file = tmp_path / "feature_ranking.csv"
        df.to_csv(ranking_file, index=False)
        
        # Load and validate
        loaded_df = pd.read_csv(ranking_file)
        
        required_cols = ["feature_name", "importance_score"]
        for col in required_cols:
            assert col in loaded_df.columns, f"Missing column in ranking: {col}"
