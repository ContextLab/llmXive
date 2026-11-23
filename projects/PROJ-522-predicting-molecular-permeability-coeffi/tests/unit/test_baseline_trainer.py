import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
from models.baselines import BaselineTrainer, RandomForestBaseline, LinearRegressionBaseline

class TestBaselineTrainer:
    @pytest.fixture
    def sample_data(self):
        """Generate synthetic sample data for testing the trainer logic."""
        np.random.seed(42)
        n_samples = 100
        X = np.random.rand(n_samples, 4)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.normal(0, 0.1, n_samples)
        return X, y

    @pytest.fixture
    def temp_output_path(self):
        """Create a temporary file path for output."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_trainer_initialization(self):
        trainer = BaselineTrainer(output_path="test.csv")
        assert trainer.output_path == Path("test.csv")
        assert trainer.logger is not None

    def test_train_and_evaluate_basic(self, sample_data, temp_output_path):
        X, y = sample_data
        fold_indices = [([0, 1, 2], [3, 4]), ([3, 4, 5], [6, 7])]
        
        trainer = BaselineTrainer(output_path=temp_output_path)
        df = trainer.train_and_evaluate(X, y, fold_indices)
        
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["fold", "model", "prediction", "target"]
        assert len(df) > 0
        assert df["fold"].nunique() == 2
        assert "RandomForest" in df["model"].values
        assert "LinearRegression" in df["model"].values

    def test_save_predictions(self, sample_data, temp_output_path):
        X, y = sample_data
        fold_indices = [([0, 1], [2, 3])]
        
        trainer = BaselineTrainer(output_path=temp_output_path)
        trainer.train_and_evaluate(X, y, fold_indices)
        
        assert os.path.exists(temp_output_path)
        df_saved = pd.read_csv(temp_output_path)
        assert len(df_saved) > 0

    def test_run_from_dataset(self, sample_data, temp_output_path):
        """Test the full pipeline from a CSV file."""
        X, y = sample_data
        df = pd.DataFrame(X, columns=["f1", "f2", "f3", "f4"])
        df["target"] = y
        
        input_path = temp_output_path.replace(".csv", "_input.csv")
        df.to_csv(input_path, index=False)
        
        trainer = BaselineTrainer(output_path=temp_output_path)
        result = trainer.run_from_dataset(
            input_path=input_path,
            feature_cols=["f1", "f2", "f3", "f4"],
            target_col="target",
            n_splits=2
        )
        
        assert isinstance(result, pd.DataFrame)
        assert "prediction" in result.columns
        assert "target" in result.columns
        
        os.remove(input_path)

    def test_custom_models(self, sample_data, temp_output_path):
        X, y = sample_data
        fold_indices = [([0, 1], [2, 3])]
        
        custom_models = [
            ("CustomRF", RandomForestBaseline(n_estimators=10)),
            ("CustomLR", LinearRegressionBaseline())
        ]
        
        trainer = BaselineTrainer(output_path=temp_output_path)
        df = trainer.train_and_evaluate(X, y, fold_indices, models=custom_models)
        
        assert "CustomRF" in df["model"].values
        assert "CustomLR" in df["model"].values
        assert "RandomForest" not in df["model"].values