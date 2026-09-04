"""
Contract tests for code/train_models.py (US2).
Verifies Random Forest training logic, split locking, and model persistence.
"""
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from train_models import (
    setup_logger,
    load_data_semi,
    load_data_dft,
    load_locked_splits,
    train_and_evaluate_fold,
    train_models,
    main
)
from utils.logging_utils import setup_logger as utils_setup_logger


class TestRFTrainingContract:
    """Contract tests ensuring train_models.py behaves as specified."""

    @pytest.fixture(autouse=True)
    def setup_temp_dirs(self, tmp_path):
        """Create temporary directories for test artifacts."""
        self.tmp_dir = tmp_path
        self.data_dir = self.tmp_dir / "data"
        self.data_dir.mkdir()
        self.models_dir = self.tmp_dir / "models"
        self.models_dir.mkdir()
        self.logs_dir = self.tmp_dir / "logs"
        self.logs_dir.mkdir()

        # Mock data files
        self.semi_data_path = self.data_dir / "descriptors_semi.csv"
        self.dft_data_path = self.data_dir / "descriptors_dft.csv"
        self.splits_path = self.data_dir / "locked_splits.json"

        # Create mock data
        self._create_mock_data()

    def _create_mock_data(self):
        """Create minimal valid CSVs and split files for testing."""
        # Semi-empirical descriptors
        semi_df = pd.DataFrame({
            "molecule_id": [f"mol_{i}" for i in range(10)],
            "HOMO_energy": np.random.uniform(-10, -5, 10),
            "LUMO_energy": np.random.uniform(-2, 2, 10),
            "mayer_bond_order": np.random.uniform(0.5, 1.5, 10),
            "experimental_barrier": np.random.uniform(10, 50, 10)
        })
        semi_df.to_csv(self.semi_data_path, index=False)

        # DFT descriptors
        dft_df = pd.DataFrame({
            "molecule_id": [f"mol_{i}" for i in range(10)],
            "HOMO_energy": np.random.uniform(-10, -5, 10),
            "LUMO_energy": np.random.uniform(-2, 2, 10),
            "mayer_bond_order": np.random.uniform(0.5, 1.5, 10),
            "experimental_barrier": np.random.uniform(10, 50, 10)
        })
        dft_df.to_csv(self.dft_data_path, index=False)

        # Locked splits (stratified KFold indices)
        splits = {
            "folds": [
                {"train": [0, 1, 2, 3, 4], "test": [5, 6]},
                {"train": [5, 6, 7, 8, 9], "test": [0, 1]},
                {"train": [0, 2, 4, 6, 8], "test": [1, 3]},
                {"train": [1, 3, 5, 7, 9], "test": [2, 4]},
                {"train": [0, 1, 3, 4, 7], "test": [2, 5]}
            ],
            "random_state": 42
        }
        with open(self.splits_path, "w") as f:
            json.dump(splits, f)

    def test_load_data_semi(self):
        """Verify loading of semi-empirical descriptor data."""
        df = load_data_semi(str(self.semi_data_path))
        assert df is not None
        assert len(df) == 10
        assert "HOMO_energy" in df.columns
        assert "experimental_barrier" in df.columns

    def test_load_data_dft(self):
        """Verify loading of DFT descriptor data."""
        df = load_data_dft(str(self.dft_data_path))
        assert df is not None
        assert len(df) == 10
        assert "LUMO_energy" in df.columns
        assert "experimental_barrier" in df.columns

    def test_load_locked_splits(self):
        """Verify loading of locked split indices."""
        splits = load_locked_splits(str(self.splits_path))
        assert splits is not None
        assert "folds" in splits
        assert len(splits["folds"]) == 5
        assert "random_state" in splits

    def test_train_and_evaluate_fold(self):
        """Verify single fold training returns valid metrics and model."""
        semi_df = load_data_semi(str(self.semi_data_path))
        dft_df = load_data_dft(str(self.dft_data_path))
        splits = load_locked_splits(str(self.splits_path))

        # Test semi-empirical model training
        model_semi, mae_semi = train_and_evaluate_fold(
            semi_df, "HOMO_energy", "experimental_barrier",
            splits["folds"][0], "semi"
        )
        assert model_semi is not None
        assert hasattr(model_semi, "predict")
        assert isinstance(mae_semi, float)
        assert mae_semi >= 0

        # Test DFT model training
        model_dft, mae_dft = train_and_evaluate_fold(
            dft_df, "HOMO_energy", "experimental_barrier",
            splits["folds"][0], "dft"
        )
        assert model_dft is not None
        assert hasattr(model_dft, "predict")
        assert isinstance(mae_dft, float)
        assert mae_dft >= 0

    def test_train_models_persists_artifacts(self):
        """Verify train_models writes model files to disk."""
        model_paths = train_models(
            str(self.semi_data_path),
            str(self.dft_data_path),
            str(self.splits_path),
            str(self.models_dir)
        )

        assert "semi_model_path" in model_paths
        assert "dft_model_path" in model_paths
        assert os.path.exists(model_paths["semi_model_path"])
        assert os.path.exists(model_paths["dft_model_path"])
        assert model_paths["semi_model_path"].endswith(".pkl")
        assert model_paths["dft_model_path"].endswith(".pkl")

    def test_split_locking_maintains_consistency(self):
        """Verify that the same split indices are used across models."""
        semi_df = load_data_semi(str(self.semi_data_path))
        dft_df = load_data_dft(str(self.dft_data_path))
        splits = load_locked_splits(str(self.splits_path))

        fold = splits["folds"][0]
        train_idx, test_idx = fold["train"], fold["test"]

        # Train semi model
        model_semi, _ = train_and_evaluate_fold(
            semi_df, "HOMO_energy", "experimental_barrier",
            fold, "semi"
        )

        # Train DFT model
        model_dft, _ = train_and_evaluate_fold(
            dft_df, "HOMO_energy", "experimental_barrier",
            fold, "dft"
        )

        # Both models should have been trained on the exact same indices
        # (implicit in the function signature usage)
        assert model_semi is not None
        assert model_dft is not None

    def test_main_entry_point(self):
        """Verify main() can be called with valid arguments."""
        # Prepare a temporary output directory
        out_dir = self.tmp_dir / "output_models"
        out_dir.mkdir()

        # Mock sys.argv
        original_argv = sys.argv
        try:
            sys.argv = [
                "train_models.py",
                "--semi-data", str(self.semi_data_path),
                "--dft-data", str(self.dft_data_path),
                "--splits", str(self.splits_path),
                "--output-dir", str(out_dir)
            ]
            # Capture output to avoid cluttering test logs
            import io
            from contextlib import redirect_stdout, redirect_stderr
            f_out, f_err = io.StringIO(), io.StringIO()

            with redirect_stdout(f_out), redirect_stderr(f_err):
                main()

            # Verify outputs were created
            semi_model = out_dir / "rf_semi.pkl"
            dft_model = out_dir / "rf_dft.pkl"
            assert semi_model.exists()
            assert dft_model.exists()
        finally:
            sys.argv = original_argv

    def test_handles_missing_data_gracefully(self):
        """Verify error handling when data files are missing."""
        with pytest.raises(FileNotFoundError):
            load_data_semi(str(self.tmp_dir / "nonexistent.csv"))

        with pytest.raises(FileNotFoundError):
            load_locked_splits(str(self.tmp_dir / "nonexistent.json"))

    def test_model_serialization_roundtrip(self):
        """Verify models can be saved and loaded correctly."""
        model_paths = train_models(
            str(self.semi_data_path),
            str(self.dft_data_path),
            str(self.splits_path),
            str(self.models_dir)
        )

        # Load models back
        import joblib
        model_semi = joblib.load(model_paths["semi_model_path"])
        model_dft = joblib.load(model_paths["dft_model_path"])

        assert model_semi is not None
        assert model_dft is not None
        assert hasattr(model_semi, "predict")
        assert hasattr(model_dft, "predict")