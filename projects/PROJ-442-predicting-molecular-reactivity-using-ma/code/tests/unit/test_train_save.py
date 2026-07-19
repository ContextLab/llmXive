import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock xgboost to avoid heavy dependencies in unit tests if necessary,
# but we will test the file I/O logic which is the core of T027.
# For this test, we assume xgboost is available or mock the train function.

from src.modeling.train import run_training_pipeline, main

@pytest.fixture
def temp_feature_file():
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        # Create a dummy feature matrix
        data = {
            "yield_pct": [10.0, 20.0, 30.0, 40.0, 50.0],
            "feat_1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feat_2": [2.0, 4.0, 6.0, 8.0, 10.0],
            "mol_id": ["m1", "m2", "m3", "m4", "m5"]
        }
        df = pd.DataFrame(data)
        df.to_parquet(f.name)
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def mock_config():
    return {
        "model_params": {
            "max_depth": 3,
            "eta": 0.3,
            "objective": "reg:squarederror"
        },
        "num_boost_round": 5,
        "target_column": "yield_pct"
    }

def test_run_training_pipeline_saves_artifacts(temp_feature_file, mock_config):
    """
    Test that run_training_pipeline creates the model and log files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "model.json"
        log_path = Path(tmpdir) / "log.json"
        
        # Mock the xgboost.train to return a mock model that has save_model method
        with patch("src.modeling.train.xgb.train") as mock_train:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
            mock_train.return_value = mock_model
            
            result = run_training_pipeline(
                feature_path=temp_feature_file,
                output_model_path=model_path,
                output_log_path=log_path,
                config=mock_config
            )
            
            # Verify files exist
            assert model_path.exists(), "Model file was not created"
            assert log_path.exists(), "Log file was not created"
            
            # Verify log content
            with open(log_path, "r") as f:
                log_data = json.load(f)
            
            assert "timestamp" in log_data
            assert "spearman_correlation" in log_data
            assert "runtime_seconds" in log_data
            assert log_data["samples"] == 5
            
            # Verify mock was called
            mock_train.assert_called_once()
            
            # Verify model save was called
            mock_model.save_model.assert_called_once_with(str(model_path))

def test_main_integration(temp_feature_file, mock_config, tmp_path):
    """
    Test the main entry point with mocked config loading and training.
    """
    model_out = tmp_path / "xgboost_model.json"
    log_out = tmp_path / "training_log.json"
    
    # Patch load_config to return our mock config
    with patch("src.modeling.train.load_config", return_value=mock_config):
        # We need to override the default paths in main() logic or ensure
        # the config passed to run_training_pipeline uses the temp paths.
        # Since main() constructs paths from config, we update the mock config
        # to point to our temp files.
        mock_config["paths"] = {
            "feature_matrix": str(temp_feature_file),
            "model_output": str(model_out),
            "training_log": str(log_out)
        }
        
        with patch("src.modeling.train.load_config", return_value=mock_config):
            with patch("src.modeling.train.xgb.train") as mock_train:
                mock_model = MagicMock()
                mock_model.predict.return_value = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
                mock_train.return_value = mock_model
                
                # Run main
                main()
                
                assert model_out.exists()
                assert log_out.exists()