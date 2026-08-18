"""
Tests for the saver module (T017).
Verifies FR-005 (saving predictions) and FR-007 (logging structure).
"""
import os
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path

from code.models.saver import (
    save_predictions,
    save_new_predictions,
    save_pipeline_log,
    save_model_artifact
)


class TestSavePredictions:
    def test_save_predictions_creates_file(self, tmp_path):
        """Test that save_predictions creates a valid CSV file."""
        data = {
            'sample_id': [1, 2, 3],
            'predicted_texture': [0.5, 0.6, 0.7],
            'confidence': [0.9, 0.85, 0.92]
        }
        df = pd.DataFrame(data)
        output_path = str(tmp_path / "predictions.csv")

        result_path = save_predictions(df, output_path, "Test Predictions")

        assert os.path.exists(result_path)
        loaded_df = pd.read_csv(result_path)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['sample_id', 'predicted_texture', 'confidence']

    def test_save_predictions_empty_dataframe(self, tmp_path, caplog):
        """Test behavior with an empty DataFrame."""
        df = pd.DataFrame(columns=['col1', 'col2'])
        output_path = str(tmp_path / "empty.csv")

        result_path = save_predictions(df, output_path, "Empty Test")

        assert os.path.exists(result_path)
        loaded_df = pd.read_csv(result_path)
        assert len(loaded_df) == 0
        assert "empty" in caplog.text.lower()

    def test_save_predictions_nonexistent_directory(self, tmp_path):
        """Test that missing directories are created automatically."""
        df = pd.DataFrame({'a': [1]})
        nested_path = str(tmp_path / "sub" / "deep" / "out.csv")

        result_path = save_predictions(df, nested_path, "Nested Test")

        assert os.path.exists(result_path)

    def test_save_predictions_invalid_type(self, tmp_path):
        """Test that non-DataFrame input raises ValueError."""
        output_path = str(tmp_path / "fail.csv")
        with pytest.raises(ValueError, match="must be a pandas DataFrame"):
            save_predictions("not a dataframe", output_path)


class TestSaveNewPredictions:
    def test_save_new_predictions_alias(self, tmp_path):
        """Test that save_new_predictions functions as a specific wrapper."""
        data = {'new_sample': [10], 'pred': [0.88]}
        df = pd.DataFrame(data)
        output_path = str(tmp_path / "new_predictions.csv")

        result = save_new_predictions(df, output_path)

        assert os.path.exists(result)
        assert pd.read_csv(result).equals(df)


class TestSavePipelineLog:
    def test_save_pipeline_log_structure(self, tmp_path):
        """Test that the log summary contains required keys."""
        log_path = str(tmp_path / "pipeline_log.json")
        hyperparams = {'n_estimators': 100, 'max_depth': 10}
        warnings_list = ["Warning 1", "Warning 2"]
        metrics = {'r2': 0.85}

        save_pipeline_log(log_path, hyperparams, warnings_list, metrics)

        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            content = json.load(f)

        assert content['hyperparameters'] == hyperparams
        assert content['warnings'] == warnings_list
        assert content['metrics'] == metrics
        assert content['status'] == 'completed'

    def test_save_pipeline_log_defaults(self, tmp_path):
        """Test that optional arguments default correctly."""
        log_path = str(tmp_path / "default_log.json")
        
        save_pipeline_log(log_path, {})

        with open(log_path, 'r') as f:
            content = json.load(f)

        assert content['warnings'] == []
        assert content['metrics'] == {}


class TestSaveModelArtifact:
    def test_save_model_creates_file(self, tmp_path):
        """Test saving a simple sklearn model."""
        from sklearn.ensemble import RandomForestRegressor
        
        model = RandomForestRegressor(n_estimators=10)
        # Fit with dummy data to ensure it's ready
        model.fit([[1], [2]], [1, 2])
        
        model_path = str(tmp_path / "model.joblib")
        
        result = save_model_artifact(model, model_path, {"test": True})
        
        assert os.path.exists(result)
        
        # Verify it can be loaded
        import joblib
        loaded_model = joblib.load(result)
        assert isinstance(loaded_model, RandomForestRegressor)
        assert loaded_model.n_estimators == 10