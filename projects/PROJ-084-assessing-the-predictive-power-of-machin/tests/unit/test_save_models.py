import json
import pickle
from pathlib import Path
import tempfile

import pytest
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from modeling.save_models import ensure_dir, save_model_artifacts


class TestSaveModels:
    def test_ensure_dir_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_path = Path(tmp_dir) / "new_dir" / "subdir"
            ensure_dir(test_path)
            assert test_path.exists()
            assert test_path.is_dir()

    def test_save_model_artifacts_creates_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            model = RandomForestRegressor(n_estimators=10, random_state=42)
            hyperparams = {"n_estimators": 10, "max_depth": 5}
            metrics = {"R2": 0.85, "RMSE": 5.2, "MAE": 4.1}
            model_name = "test_model"

            save_model_artifacts(model, model_name, hyperparams, metrics, output_dir)

            model_path = output_dir / f"{model_name}_model.pkl"
            params_path = output_dir / f"{model_name}_params.json"
            metrics_path = output_dir / f"{model_name}_metrics.json"

            assert model_path.exists(), f"Model file {model_path} not created"
            assert params_path.exists(), f"Params file {params_path} not created"
            assert metrics_path.exists(), f"Metrics file {metrics_path} not created"

            # Verify content
            with open(model_path, "rb") as f:
                loaded_model = pickle.load(f)
                assert isinstance(loaded_model, RandomForestRegressor)

            with open(params_path, "r") as f:
                loaded_params = json.load(f)
                assert loaded_params == hyperparams

            with open(metrics_path, "r") as f:
                loaded_metrics = json.load(f)
                assert loaded_metrics == metrics
