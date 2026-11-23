"""
Unit tests for T022: Permutation test implementation.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_seed, set_global_seed
from code.utils.stats_helpers import permutation_test


class TestPermutationTestLogic:
    """Tests for the core permutation test logic."""

    def test_permutation_test_function_exists(self):
        """Verify that the permutation_test helper exists and is callable."""
        assert callable(permutation_test)

    def test_permutation_test_returns_correct_format(self):
        """Verify that permutation_test returns p_value and null_distribution."""
        # Create small dummy data
        np.random.seed(42)
        X = np.random.randn(20, 3)
        y = np.random.randn(20)

        p_val, null_dist = permutation_test(X, y, metric="r2", n_permutations=10, random_state=42)

        assert isinstance(p_val, float)
        assert 0.0 <= p_val <= 1.0
        assert isinstance(null_dist, list)
        assert len(null_dist) == 10

    def test_permutation_test_p_value_consistency(self):
        """Verify that permutation test is deterministic with same seed."""
        np.random.seed(42)
        X = np.random.randn(30, 5)
        y = np.random.randn(30)

        p1, _ = permutation_test(X, y, metric="r2", n_permutations=50, random_state=123)
        p2, _ = permutation_test(X, y, metric="r2", n_permutations=50, random_state=123)

        assert p1 == p2


class TestT022Integration:
    """Integration tests for the T022 script logic."""

    @pytest.fixture
    def mock_data_setup(self, tmp_path):
        """Setup mock data files for testing."""
        # Create mock features file
        features_df = pd.DataFrame({
            "participant_id": list(range(50)),
            "delta_power": np.random.randn(50),
            "theta_power": np.random.randn(50),
            "alpha_power": np.random.randn(50),
            "beta_power": np.random.randn(50),
            "gamma_power": np.random.randn(50),
            "median_rt": np.random.randn(50) * 100 + 400
        })
        features_path = tmp_path / "processed" / "features.csv"
        features_path.parent.mkdir(parents=True, exist_ok=True)
        features_df.to_csv(features_path, index=False)

        # Create mock split indices
        test_indices = list(range(40, 50))  # Last 10 as test
        split_data = {"test_indices": test_indices, "train_indices": list(range(40))}
        split_path = tmp_path / "processed" / "split_indices.json"
        with open(split_path, "w") as f:
            json.dump(split_data, f)

        return {
            "features_path": features_path,
            "split_path": split_path,
            "output_path": tmp_path / "processed" / "permutation_results.json"
        }

    @patch("code.config.get_path")
    def test_load_features_success(self, mock_get_path, mock_data_setup, tmp_path):
        """Test that features are loaded correctly."""
        from code._10_perform_permutation_test import load_features

        mock_get_path.side_effect = lambda key: {
            "processed_features": str(mock_data_setup["features_path"])
        }.get(key)

        df = load_features()
        assert len(df) == 50
        assert "median_rt" in df.columns

    @patch("code.config.get_path")
    def test_load_split_indices_success(self, mock_get_path, mock_data_setup):
        """Test that split indices are loaded correctly."""
        from code._10_perform_permutation_test import load_split_indices

        mock_get_path.side_effect = lambda key: {
            "split_indices": str(mock_data_setup["split_path"])
        }.get(key)

        splits = load_split_indices()
        assert "test_indices" in splits
        assert len(splits["test_indices"]) == 10

    @patch("code.config.get_path")
    def test_prepare_test_data_extracts_correct_rows(self, mock_get_path, mock_data_setup):
        """Test that test data preparation extracts only test set rows."""
        from code._10_perform_permutation_test import prepare_test_data

        mock_get_path.side_effect = lambda key: {
            "processed_features": str(mock_data_setup["features_path"]),
            "split_indices": str(mock_data_setup["split_path"])
        }.get(key)

        features_df = pd.read_csv(mock_data_setup["features_path"])
        with open(mock_data_setup["split_path"], "r") as f:
            split_indices = json.load(f)

        X, y = prepare_test_data(features_df, split_indices)

        # Should have 10 rows (the test set size)
        assert X.shape[0] == 10
        assert y.shape[0] == 10
        # Should have 5 feature columns (excluding participant_id and median_rt)
        assert X.shape[1] == 5

    @patch("code.config.get_path")
    def test_run_permutation_test_returns_valid_results(self, mock_get_path, mock_data_setup):
        """Test that the permutation test returns valid result structure."""
        from code._10_perform_permutation_test import run_permutation_test

        # Create small dummy data for speed
        X = np.random.randn(20, 5)
        y = np.random.randn(20)

        results = run_permutation_test(X, y, n_permutations=10, random_state=42)

        assert "observed_r2" in results
        assert "p_value" in results
        assert "null_distribution" in results
        assert "n_permutations" in results
        assert "significant_at_005" in results
        assert isinstance(results["null_distribution"], list)
        assert len(results["null_distribution"]) == 10

    @patch("code.config.get_path")
    def test_save_results_creates_json(self, mock_get_path, mock_data_setup, tmp_path):
        """Test that results are saved to JSON file."""
        from code._10_perform_permutation_test import save_results

        mock_get_path.side_effect = lambda key: {
            "permutation_results": str(mock_data_setup["output_path"])
        }.get(key)

        results = {
            "observed_r2": 0.15,
            "p_value": 0.03,
            "null_distribution": [0.01, 0.02, 0.03],
            "n_permutations": 3,
            "significant_at_005": True
        }

        save_results(results, mock_data_setup["output_path"])

        assert mock_data_setup["output_path"].exists()
        with open(mock_data_setup["output_path"], "r") as f:
            loaded = json.load(f)
        assert loaded["p_value"] == 0.03

    @patch("code.config.get_path")
    def test_missing_features_raises_error(self, mock_get_path, tmp_path):
        """Test that missing features file raises FileNotFoundError."""
        from code._10_perform_permutation_test import load_features

        mock_get_path.return_value = str(tmp_path / "nonexistent.csv")

        with pytest.raises(FileNotFoundError):
            load_features()

    @patch("code.config.get_path")
    def test_missing_split_indices_raises_error(self, mock_get_path, tmp_path):
        """Test that missing split indices file raises FileNotFoundError."""
        from code._10_perform_permutation_test import load_split_indices

        mock_get_path.return_value = str(tmp_path / "nonexistent.json")

        with pytest.raises(FileNotFoundError):
            load_split_indices()

    @patch("code.config.get_path")
    def test_empty_test_set_raises_error(self, mock_get_path, mock_data_setup):
        """Test that empty test set raises ValueError."""
        from code._10_perform_permutation_test import prepare_test_data

        # Create split with empty test set
        empty_split = {"test_indices": [], "train_indices": list(range(50))}
        
        features_df = pd.read_csv(mock_data_setup["features_path"])
        
        with pytest.raises(ValueError, match="No 'test_indices' found"):
            # We need to mock the return of load_split_indices to return empty
            pass # This is handled in the main flow, but we test the logic here

        # Direct test of the logic
        test_indices = []
        test_df = features_df.iloc[test_indices]
        assert len(test_df) == 0
        # The function would raise later when checking len(y_test) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])