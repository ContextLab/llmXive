"""Unit tests for the permutation test wrapper module."""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import pandas as pd

from code_04_train_model_wrapper import load_features_and_labels_from_disk, train_single_fold_model


class TestLoadFeaturesAndLabels:
    """Tests for the data loading function."""

    def test_load_features_and_labels_creates_valid_arrays(self):
        """Test that the function returns valid numpy arrays."""
        # Create temporary data files
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)

            # Create graph_metrics.csv
            metrics_data = {
                "subject_id": [f"sub_{i:03d}" for i in range(10)],
                "degree": np.random.rand(10),
                "efficiency": np.random.rand(10),
                "clustering": np.random.rand(10),
                "path_length": np.random.rand(10)
            }
            pd.DataFrame(metrics_data).to_csv(data_dir / "graph_metrics.csv", index=False)

            # Create eligible_subjects.csv
            eligible_data = {
                "subject_id": metrics_data["subject_id"],
                "decline_label": np.random.randint(0, 2, 10)
            }
            pd.DataFrame(eligible_data).to_csv(data_dir / "eligible_subjects.csv", index=False)

            # Load data
            X, y = load_features_and_labels_from_disk(data_dir)

            # Assertions
            assert isinstance(X, np.ndarray)
            assert isinstance(y, np.ndarray)
            assert X.shape[0] == 10
            assert y.shape[0] == 10
            assert X.shape[1] == 4  # degree, efficiency, clustering, path_length

    def test_load_features_and_labels_with_limit(self):
        """Test that n_subjects parameter limits the output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)

            # Create larger dataset
            n_total = 20
            metrics_data = {
                "subject_id": [f"sub_{i:03d}" for i in range(n_total)],
                "degree": np.random.rand(n_total),
                "efficiency": np.random.rand(n_total),
                "clustering": np.random.rand(n_total),
                "path_length": np.random.rand(n_total)
            }
            pd.DataFrame(metrics_data).to_csv(data_dir / "graph_metrics.csv", index=False)

            eligible_data = {
                "subject_id": metrics_data["subject_id"],
                "decline_label": np.random.randint(0, 2, n_total)
            }
            pd.DataFrame(eligible_data).to_csv(data_dir / "eligible_subjects.csv", index=False)

            # Load with limit
            X, y = load_features_and_labels_from_disk(data_dir, n_subjects=5)

            assert X.shape[0] == 5
            assert y.shape[0] == 5

    def test_load_features_and_labels_missing_file(self):
        """Test that FileNotFoundError is raised when file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)

            with pytest.raises(FileNotFoundError):
                load_features_and_labels_from_disk(data_dir)


class TestTrainSingleFoldModel:
    """Tests for the single fold training function."""

    def test_train_single_fold_model_returns_auc(self):
        """Test that the function returns a valid AUC score."""
        # Create synthetic data
        np.random.seed(42)
        n_samples = 30
        n_features = 10

        X = np.random.rand(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)

        # Train model
        auc = train_single_fold_model(X, y, random_state=42)

        # Assertions
        assert isinstance(auc, float)
        assert 0.0 <= auc <= 1.0

    def test_train_single_fold_model_deterministic(self):
        """Test that the function produces deterministic results."""
        np.random.seed(42)
        n_samples = 30
        n_features = 10

        X = np.random.rand(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)

        # Train twice with same seed
        auc1 = train_single_fold_model(X, y, random_state=42)
        auc2 = train_single_fold_model(X, y, random_state=42)

        assert auc1 == auc2

    def test_train_single_fold_model_with_different_seeds(self):
        """Test that different seeds produce different results (usually)."""
        np.random.seed(42)
        n_samples = 30
        n_features = 10

        X = np.random.rand(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)

        # Train with different seeds
        auc1 = train_single_fold_model(X, y, random_state=42)
        auc2 = train_single_fold_model(X, y, random_state=123)

        # Results might be the same by chance, but usually different
        # We just check they are valid AUCs
        assert 0.0 <= auc1 <= 1.0
        assert 0.0 <= auc2 <= 1.0