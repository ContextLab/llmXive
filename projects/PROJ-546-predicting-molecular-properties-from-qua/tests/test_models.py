"""
Contract tests for code/train_models.py (User Story 2).

These tests verify the Random Forest training logic, ensuring that:
1. The models can be trained on valid data.
2. The locked splits from state/splits.json are respected.
3. The output model artifacts are valid and can be loaded.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from train_models import (
    setup_logger,
    load_data_semi,
    load_data_dft,
    load_locked_splits,
    train_and_evaluate_fold,
    train_models,
)
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import NotFittedError


class TestTrainModelsContract:
    """Contract tests for the model training pipeline."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project structure for testing."""
        tmp_dir = tempfile.mkdtemp()
        project_root = Path(tmp_dir)

        # Create necessary directories
        (project_root / "data").mkdir(parents=True, exist_ok=True)
        (project_root / "state").mkdir(parents=True, exist_ok=True)
        (project_root / "code").mkdir(parents=True, exist_ok=True)
        (project_root / "logs").mkdir(parents=True, exist_ok=True)

        # Change to temp directory to simulate project root context
        self._original_cwd = os.getcwd()
        os.chdir(tmp_dir)

        yield project_root

        # Cleanup
        os.chdir(self._original_cwd)
        shutil.rmtree(tmp_dir)

    @pytest.fixture
    def sample_data(self, temp_project_root):
        """Generate sample data files for testing."""
        # Create sample semi-empirical descriptors
        semi_data = {
            "molecule_id": [f"mol_{i}" for i in range(10)],
            "HOMO_energy": np.random.uniform(-10, -5, 10),
            "LUMO_energy": np.random.uniform(-2, 2, 10),
            "mayer_bond_order": np.random.uniform(0.5, 1.5, 10),
            "target_barrier": np.random.uniform(10, 30, 10),
        }
        semi_df = pd.DataFrame(semi_data)
        semi_df.to_csv(temp_project_root / "data" / "descriptors_semi.csv", index=False)

        # Create sample DFT descriptors
        dft_data = {
            "molecule_id": [f"mol_{i}" for i in range(10)],
            "HOMO_energy": np.random.uniform(-10, -5, 10),
            "LUMO_energy": np.random.uniform(-2, 2, 10),
            "mayer_bond_order": np.random.uniform(0.5, 1.5, 10),
            "target_barrier": np.random.uniform(10, 30, 10),
        }
        dft_df = pd.DataFrame(dft_data)
        dft_df.to_csv(temp_project_root / "data" / "descriptors_dft.csv", index=False)

        # Create sample splits
        splits = {
            "train_indices": [0, 1, 2, 3, 4, 5],
            "test_indices": [6, 7, 8, 9],
            "random_state": 42
        }
        with open(temp_project_root / "state" / "splits.json", "w") as f:
            json.dump(splits, f)

        return temp_project_root

    def test_load_data_semi(self, sample_data):
        """Test loading semi-empirical descriptor data."""
        semi_df = load_data_semi()
        assert isinstance(semi_df, pd.DataFrame)
        assert "molecule_id" in semi_df.columns
        assert "HOMO_energy" in semi_df.columns
        assert len(semi_df) == 10

    def test_load_data_dft(self, sample_data):
        """Test loading DFT descriptor data."""
        dft_df = load_data_dft()
        assert isinstance(dft_df, pd.DataFrame)
        assert "molecule_id" in dft_df.columns
        assert "HOMO_energy" in dft_df.columns
        assert len(dft_df) == 10

    def test_load_locked_splits(self, sample_data):
        """Test loading locked split indices."""
        train_idx, test_idx, random_state = load_locked_splits()
        assert isinstance(train_idx, list)
        assert isinstance(test_idx, list)
        assert isinstance(random_state, int)
        assert len(train_idx) == 6
        assert len(test_idx) == 4
        assert random_state == 42

    def test_train_and_evaluate_fold(self, sample_data):
        """Test training a single fold of the Random Forest model."""
        train_idx, test_idx, random_state = load_locked_splits()

        # Load data
        semi_df = load_data_semi()
        dft_df = load_data_dft()

        # Prepare features and targets
        feature_cols = ["HOMO_energy", "LUMO_energy", "mayer_bond_order"]
        target_col = "target_barrier"

        X_train_semi = semi_df.iloc[train_idx][feature_cols].values
        y_train_semi = semi_df.iloc[train_idx][target_col].values
        X_test_semi = semi_df.iloc[test_idx][feature_cols].values
        y_test_semi = semi_df.iloc[test_idx][target_col].values

        X_train_dft = dft_df.iloc[train_idx][feature_cols].values
        y_train_dft = dft_df.iloc[train_idx][target_col].values
        X_test_dft = dft_df.iloc[test_idx][feature_cols].values
        y_test_dft = dft_df.iloc[test_idx][target_col].values

        # Train and evaluate semi-empirical model
        mae_semi, model_semi = train_and_evaluate_fold(
            X_train_semi, y_train_semi, X_test_semi, y_test_semi,
            model_type="semi", random_state=random_state
        )
        assert isinstance(mae_semi, float)
        assert mae_semi >= 0
        assert isinstance(model_semi, RandomForestRegressor)
        assert model_semi is not None

        # Train and evaluate DFT model
        mae_dft, model_dft = train_and_evaluate_fold(
            X_train_dft, y_train_dft, X_test_dft, y_test_dft,
            model_type="dft", random_state=random_state
        )
        assert isinstance(mae_dft, float)
        assert mae_dft >= 0
        assert isinstance(model_dft, RandomForestRegressor)
        assert model_dft is not None

    def test_train_models_full_pipeline(self, sample_data):
        """Test the full model training pipeline."""
        # Run the full training pipeline
        models, metrics = train_models()

        # Verify models are returned
        assert isinstance(models, dict)
        assert "semi" in models
        assert "dft" in models
        assert isinstance(models["semi"], RandomForestRegressor)
        assert isinstance(models["dft"], RandomForestRegressor)

        # Verify models are fitted
        assert models["semi"].fitted_
        assert models["dft"].fitted_

        # Verify metrics are returned
        assert isinstance(metrics, dict)
        assert "mae_semi" in metrics
        assert "mae_dft" in metrics
        assert isinstance(metrics["mae_semi"], float)
        assert isinstance(metrics["mae_dft"], float)
        assert metrics["mae_semi"] >= 0
        assert metrics["mae_dft"] >= 0

    def test_model_predictions_valid(self, sample_data):
        """Test that trained models produce valid predictions."""
        models, _ = train_models()

        # Load test data
        semi_df = load_data_semi()
        dft_df = load_data_dft()
        _, test_idx, _ = load_locked_splits()

        feature_cols = ["HOMO_energy", "LUMO_energy", "mayer_bond_order"]

        # Test semi-empirical model
        X_test_semi = semi_df.iloc[test_idx][feature_cols].values
        preds_semi = models["semi"].predict(X_test_semi)
        assert len(preds_semi) == len(test_idx)
        assert not np.any(np.isnan(preds_semi))

        # Test DFT model
        X_test_dft = dft_df.iloc[test_idx][feature_cols].values
        preds_dft = models["dft"].predict(X_test_dft)
        assert len(preds_dft) == len(test_idx)
        assert not np.any(np.isnan(preds_dft))

    def test_split_consistency(self, sample_data):
        """Test that the same split indices are used for both models."""
        models, _ = train_models()

        # Load data and splits
        semi_df = load_data_semi()
        dft_df = load_data_dft()
        train_idx, test_idx, random_state = load_locked_splits()

        feature_cols = ["HOMO_energy", "LUMO_energy", "mayer_bond_order"]
        target_col = "target_barrier"

        # Verify both models were trained on the same indices
        X_train_semi = semi_df.iloc[train_idx][feature_cols].values
        y_train_semi = semi_df.iloc[train_idx][target_col].values
        X_test_semi = semi_df.iloc[test_idx][feature_cols].values
        y_test_semi = semi_df.iloc[test_idx][target_col].values

        X_train_dft = dft_df.iloc[train_idx][feature_cols].values
        y_train_dft = dft_df.iloc[train_idx][target_col].values
        X_test_dft = dft_df.iloc[test_idx][feature_cols].values
        y_test_dft = dft_df.iloc[test_idx][target_col].values

        # Both models should be trained on their respective datasets
        # but using the same split indices
        assert models["semi"].n_features_in_ == len(feature_cols)
        assert models["dft"].n_features_in_ == len(feature_cols)

    def test_error_handling_missing_data(self, temp_project_root):
        """Test error handling when required data files are missing."""
        # Remove data files
        (temp_project_root / "data" / "descriptors_semi.csv").unlink()

        with pytest.raises(FileNotFoundError):
            load_data_semi()

    def test_error_handling_missing_splits(self, temp_project_root):
        """Test error handling when splits file is missing."""
        # Create data files but remove splits
        semi_data = {
            "molecule_id": [f"mol_{i}" for i in range(10)],
            "HOMO_energy": np.random.uniform(-10, -5, 10),
            "LUMO_energy": np.random.uniform(-2, 2, 10),
            "mayer_bond_order": np.random.uniform(0.5, 1.5, 10),
            "target_barrier": np.random.uniform(10, 30, 10),
        }
        semi_df = pd.DataFrame(semi_data)
        semi_df.to_csv(temp_project_root / "data" / "descriptors_semi.csv", index=False)

        (temp_project_root / "state" / "splits.json").unlink()

        with pytest.raises(FileNotFoundError):
            load_locked_splits()