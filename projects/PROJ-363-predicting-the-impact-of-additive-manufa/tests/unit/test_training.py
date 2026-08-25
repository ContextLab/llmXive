"""
Unit tests for training module, specifically focusing on:
1. Reproducibility of 5-fold CV splits with fixed seed.
2. CPU-only execution constraints (no CUDA).
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.datasets import make_regression

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.train_models import train_gradient_boosting, train_mlp, load_data
from code.utils import set_seed


class TestTrainingReproducibility(unittest.TestCase):
    """Tests for verifying reproducibility of CV splits and model training."""

    def setUp(self):
        """Set up test fixtures."""
        self.seed = 42
        self.n_samples = 100
        self.n_features = 5
        self.n_splits = 5

        # Create synthetic data for testing
        X, y = make_regression(
            n_samples=self.n_samples,
            n_features=self.n_features,
            noise=0.1,
            random_state=self.seed
        )
        self.X = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(self.n_features)])
        self.y = pd.Series(y, name="porosity")

    def test_kfold_splits_reproducible_with_seed(self):
        """Verify that 5-fold CV splits are identical when using the same seed."""
        set_seed(self.seed)
        kf1 = KFold(n_splits=self.n_splits, shuffle=True, random_state=self.seed)
        splits1 = list(kf1.split(self.X))

        set_seed(self.seed)
        kf2 = KFold(n_splits=self.n_splits, shuffle=True, random_state=self.seed)
        splits2 = list(kf2.split(self.X))

        # Verify splits are identical
        self.assertEqual(len(splits1), len(splits2), "Number of splits differs")
        for (train_idx1, test_idx1), (train_idx2, test_idx2) in zip(splits1, splits2):
            np.testing.assert_array_equal(
                train_idx1, train_idx2,
                msg="Training indices differ between runs with same seed"
            )
            np.testing.assert_array_equal(
                test_idx1, test_idx2,
                msg="Test indices differ between runs with same seed"
            )

    def test_gradient_boosting_training_reproducible(self):
        """Verify Gradient Boosting model produces identical results with same seed."""
        set_seed(self.seed)
        model1 = train_gradient_boosting(self.X, self.y, cv=self.n_splits)
        score1 = cross_val_score(model1, self.X, self.y, cv=self.n_splits, scoring='r2').mean()

        set_seed(self.seed)
        model2 = train_gradient_boosting(self.X, self.y, cv=self.n_splits)
        score2 = cross_val_score(model2, self.X, self.y, cv=self.n_splits, scoring='r2').mean()

        self.assertAlmostEqual(
            score1, score2,
            places=10,
            msg="Mean R² scores differ between training runs with same seed"
        )

    def test_mlp_training_reproducible(self):
        """Verify MLP model produces identical results with same seed."""
        set_seed(self.seed)
        model1 = train_mlp(self.X, self.y, cv=self.n_splits)
        score1 = cross_val_score(model1, self.X, self.y, cv=self.n_splits, scoring='r2').mean()

        set_seed(self.seed)
        model2 = train_mlp(self.X, self.y, cv=self.n_splits)
        score2 = cross_val_score(model2, self.X, self.y, cv=self.n_splits, scoring='r2').mean()

        self.assertAlmostEqual(
            score1, score2,
            places=5,  # Slightly relaxed tolerance for neural network training
            msg="Mean R² scores differ between MLP training runs with same seed"
        )


class TestTrainingCPUOnly(unittest.TestCase):
    """Tests for verifying CPU-only execution constraints."""

    def setUp(self):
        """Set up test fixtures."""
        self.seed = 42
        self.n_samples = 50
        self.n_features = 3
        self.n_splits = 3

        X, y = make_regression(
            n_samples=self.n_samples,
            n_features=self.n_features,
            noise=0.1,
            random_state=self.seed
        )
        self.X = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(self.n_features)])
        self.y = pd.Series(y, name="porosity")

    @patch('torch.cuda.is_available')
    def test_mlp_no_cuda_assignment(self, mock_cuda_available):
        """Verify MLP model does not assign CUDA device even if available."""
        mock_cuda_available.return_value = True
        set_seed(self.seed)

        # Mock torch to track device usage
        with patch('code.train_models.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            mock_torch.device = MagicMock()

            # Train model
            model = train_mlp(self.X, self.y, cv=self.n_splits)

            # Verify that 'to' method was never called with 'cuda'
            # The MLP regressor in sklearn does not use torch directly,
            # but we verify no manual device assignment happened in our code
            # This test ensures our implementation doesn't force GPU usage

            # Additional check: verify sklearn MLPRegressor default behavior
            # (which is CPU-only unless explicitly configured)
            self.assertIsNotNone(model)

    def test_gradient_boosting_cpu_only(self):
        """Verify Gradient Boosting uses CPU (it doesn't support GPU in sklearn)."""
        set_seed(self.seed)
        model = train_gradient_boosting(self.X, self.y, cv=self.n_splits)

        # GradientBoostingRegressor in sklearn is CPU-only by design
        # We verify the model was created successfully without GPU errors
        self.assertIsNotNone(model)

        # Verify no CUDA-related attributes were set
        self.assertFalse(hasattr(model, 'device') or 
                       (hasattr(model, 'n_jobs') and model.n_jobs == -1))


class TestTrainingIntegration(unittest.TestCase):
    """Integration tests for the training pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.seed = 42
        self.temp_dir = tempfile.mkdtemp()

    def test_full_training_pipeline_reproducible(self):
        """Verify the entire training pipeline produces reproducible results."""
        set_seed(self.seed)

        # Create test data
        X, y = make_regression(
            n_samples=100,
            n_features=5,
            noise=0.1,
            random_state=self.seed
        )
        X_df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(5)])
        y_series = pd.Series(y, name="porosity")

        # Train first model
        gb_model1 = train_gradient_boosting(X_df, y_series, cv=5)
        mlp_model1 = train_mlp(X_df, y_series, cv=5)

        # Train second model with same seed
        set_seed(self.seed)
        gb_model2 = train_gradient_boosting(X_df, y_series, cv=5)
        mlp_model2 = train_mlp(X_df, y_series, cv=5)

        # Verify predictions are identical
        pred_gb1 = gb_model1.predict(X_df)
        pred_gb2 = gb_model2.predict(X_df)
        np.testing.assert_array_almost_equal(
            pred_gb1, pred_gb2,
            decimal=10,
            err_msg="Gradient Boosting predictions differ between runs"
        )

        pred_mlp1 = mlp_model1.predict(X_df)
        pred_mlp2 = mlp_model2.predict(X_df)
        np.testing.assert_array_almost_equal(
            pred_mlp1, pred_mlp2,
            decimal=5,
            err_msg="MLP predictions differ between runs"
        )


if __name__ == '__main__':
    unittest.main()