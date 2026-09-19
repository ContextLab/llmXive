import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.modeling.metrics import collect_all_metrics, save_metrics_json

class TestMetricsGeneration:
    """Integration tests for T021: Model Metrics Generation."""

    def test_collect_all_metrics_structure(self):
        """
        Verify that collect_all_metrics returns a list of dictionaries 
        with the required keys: R², MAE, and hyperparameters.
        """
        # Note: This test assumes the clean data file exists from T015.
        # In a real CI environment, T015 would run before this.
        # We check the structure of the result if data is available.
        
        data_path = Path("data/processed/mgb2_clean.csv")
        model_path = Path("data/processed/best_model.pkl")
        
        if not data_path.exists() or not model_path.exists():
            pytest.skip("Prerequisite data files (mgb2_clean.csv, best_model.pkl) not found. Run T015 and T020 first.")
        
        metrics = collect_all_metrics(str(data_path), str(model_path))
        
        assert isinstance(metrics, list), "Metrics must be a list"
        assert len(metrics) > 0, "At least one model metric must be present"
        
        required_keys = {"r2_score", "mae", "hyperparameters", "model_name"}
        
        for entry in metrics:
            assert isinstance(entry, dict), "Each metric entry must be a dictionary"
            assert required_keys.issubset(entry.keys()), f"Missing required keys in {entry}"
            assert isinstance(entry["r2_score"], (int, float)), "R² must be numeric"
            assert isinstance(entry["mae"], (int, float)), "MAE must be numeric"
            assert isinstance(entry["hyperparameters"], dict), "Hyperparameters must be a dictionary"

    def test_save_metrics_json(self, tmp_path):
        """
        Verify that save_metrics_json correctly writes a valid JSON file.
        """
        test_metrics = [
            {
                "model_name": "TestModel",
                "r2_score": 0.85,
                "mae": 2.5,
                "hyperparameters": {"alpha": 1.0}
            }
        ]
        
        output_file = tmp_path / "test_metrics.json"
        save_metrics_json(test_metrics, str(output_file))
        
        assert output_file.exists(), "Output file should be created"
        
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_metrics, "Loaded data should match input"