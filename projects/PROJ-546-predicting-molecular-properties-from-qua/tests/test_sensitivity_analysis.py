"""
Unit tests for sensitivity_analysis.py (T029)
"""

import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sensitivity_analysis import (
    extract_feature_importance,
    write_sensitivity_csv,
    prepare_features_target
)


class TestExtractFeatureImportance:
    def test_extract_and_sort(self):
        """Test that importances are extracted and sorted correctly."""
        # Create a mock model
        mock_model = MagicMock(spec=RandomForestRegressor)
        mock_model.feature_importances_ = np.array([0.1, 0.5, 0.2, 0.2])

        feature_names = ["feat_A", "feat_B", "feat_C", "feat_D"]

        result = extract_feature_importance(mock_model, feature_names)

        # Check sorting (descending)
        assert result[0]['descriptor'] == "feat_B"
        assert result[0]['importance'] == 0.5

        assert result[1]['descriptor'] == "feat_C" or result[1]['descriptor'] == "feat_D"
        assert result[1]['importance'] == 0.2

        # Check cumulative
        assert abs(result[0]['cumulative_importance'] - 0.5) < 1e-6
        # The second cumulative depends on which one is picked first between C and D, but sum should be 0.7
        assert abs(result[1]['cumulative_importance'] - 0.7) < 1e-6

    def test_mismatched_lengths(self):
        """Test error when feature names count != importance count."""
        mock_model = MagicMock()
        mock_model.feature_importances_ = np.array([0.1, 0.2])
        feature_names = ["feat_A", "feat_B", "feat_C"]

        with pytest.raises(ValueError):
            extract_feature_importance(mock_model, feature_names)

    def test_no_feature_importances_attr(self):
        """Test error when model lacks feature_importances_."""
        mock_model = MagicMock()
        del mock_model.feature_importances_
        feature_names = ["feat_A"]

        with pytest.raises(AttributeError):
            extract_feature_importance(mock_model, feature_names)


class TestPrepareFeaturesTarget:
    def test_split_data(self):
        """Test correct separation of X, y, and feature names."""
        df = pd.DataFrame({
            "feat_1": [1.0, 2.0],
            "feat_2": [3.0, 4.0],
            "target": [10.0, 20.0]
        })

        X, y, names = prepare_features_target(df, target_col="target")

        assert X.shape == (2, 2)
        assert y.shape == (2,)
        assert sorted(names) == ["feat_1", "feat_2"]
        assert np.allclose(y, [10.0, 20.0])

    def test_missing_target(self):
        """Test error when target column is missing."""
        df = pd.DataFrame({"feat_1": [1.0]})
        with pytest.raises(KeyError):
            prepare_features_target(df, target_col="missing_target")

    def test_no_features(self):
        """Test error when no feature columns exist."""
        df = pd.DataFrame({"target": [1.0]})
        with pytest.raises(ValueError):
            prepare_features_target(df, target_col="target")


class TestWriteSensitivityCsv:
    def test_write_file(self):
        """Test that the CSV is written correctly with headers."""
        results = [
            {"rank": 1, "descriptor": "A", "importance": 0.9, "cumulative_importance": 0.9},
            {"rank": 2, "descriptor": "B", "importance": 0.1, "cumulative_importance": 1.0}
        ]

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            write_sensitivity_csv(results, Path(temp_path))

            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert rows[0]['rank'] == '1'
            assert rows[0]['descriptor'] == 'A'
            assert float(rows[0]['importance']) == 0.9
            assert float(rows[0]['cumulative_importance']) == 0.9
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_empty_results(self):
        """Test error when results list is empty."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
            temp_path = f.name
        try:
            with pytest.raises(ValueError):
                write_sensitivity_csv([], Path(temp_path))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)