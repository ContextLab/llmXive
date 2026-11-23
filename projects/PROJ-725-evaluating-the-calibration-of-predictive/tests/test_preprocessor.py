"""
Tests for code/data/preprocessor.py
"""
import pytest
import pandas as pd
import numpy as np

from data.preprocessor import (
    validate_target,
    handle_missing_values,
    split_data,
    preprocess_dataset
)


class TestValidateTarget:
    def test_valid_target(self):
        """Test with a valid target variable."""
        target = pd.Series(np.random.randn(100))
        result = validate_target(target)
        assert result["valid"] is True
        assert result["n_samples"] == 100

    def test_missing_values_raises(self):
        """Test that missing values in target raise an error."""
        target = pd.Series([1.0, 2.0, np.nan, 4.0])
        with pytest.raises(ValueError):
            validate_target(target)

    def test_insufficient_samples_raises(self):
        """Test that too few samples raise an error."""
        target = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="minimum is 10"):
            validate_target(target, min_samples=10)

    def test_zero_variance_raises(self):
        """Test that zero variance raises an error."""
        target = pd.Series([5.0, 5.0, 5.0, 5.0, 5.0])
        with pytest.raises(ValueError, match="variance"):
            validate_target(target, min_variance=1e-6)


class TestHandleMissingValues:
    def test_no_missing_values(self):
        """Test with no missing values."""
        X = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        y = pd.Series([10.0, 20.0, 30.0])
        X_clean, y_clean = handle_missing_values(X, y)
        pd.testing.assert_frame_equal(X_clean, X)
        pd.testing.assert_series_equal(y_clean, y)

    def test_impute_features_mean(self):
        """Test feature imputation with mean strategy."""
        X = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [4.0, 5.0, np.nan]})
        y = pd.Series([10.0, 20.0, 30.0])
        X_clean, y_clean = handle_missing_values(X, y, strategy="mean")

        # Check that no NaN values remain in X
        assert not X_clean.isna().any().any()
        # Mean of [1.0, 3.0] is 2.0
        assert X_clean.loc[1, "a"] == 2.0
        # Mean of [4.0, 5.0] is 4.5
        assert X_clean.loc[2, "b"] == 4.5

    def test_drop_missing_target(self):
        """Test dropping rows with missing target values."""
        X = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [5.0, 6.0, 7.0, 8.0]})
        y = pd.Series([10.0, np.nan, 30.0, 40.0])

        X_clean, y_clean = handle_missing_values(X, y, impute_y=False)

        assert len(y_clean) == 3
        assert not y_clean.isna().any()
        # Original indices should be dropped and reset
        assert list(y_clean.index) == [0, 1, 2]

    def test_impute_target(self):
        """Test imputation of target values."""
        X = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        y = pd.Series([10.0, np.nan, 30.0])

        X_clean, y_clean = handle_missing_values(X, y, impute_y=True, strategy="mean")

        assert len(y_clean) == 3
        # Mean of [10.0, 30.0] is 20.0
        assert y_clean.loc[1] == 20.0


class TestSplitData:
    def test_split_sizes(self):
        """Test that split sizes are correct."""
        X = pd.DataFrame({"a": range(100), "b": range(100, 200)})
        y = pd.Series(range(100))

        X_train, X_test, y_train, y_test = split_data(
            X, y, test_size=0.2, random_state=42
        )

        assert len(X_train) == 80
        assert len(X_test) == 20
        assert len(y_train) == 80
        assert len(y_test) == 20

    def test_split_reproducibility(self):
        """Test that split is reproducible with fixed seed."""
        X = pd.DataFrame({"a": range(50), "b": range(50, 100)})
        y = pd.Series(range(50))

        X_train1, X_test1, y_train1, y_test1 = split_data(
            X, y, test_size=0.2, random_state=123
        )
        X_train2, X_test2, y_train2, y_test2 = split_data(
            X, y, test_size=0.2, random_state=123
        )

        pd.testing.assert_frame_equal(X_train1, X_train2)
        pd.testing.assert_frame_equal(X_test1, X_test2)
        pd.testing.assert_series_equal(y_train1, y_train2)
        pd.testing.assert_series_equal(y_test1, y_test2)

    def test_indices_reset(self):
        """Test that indices are reset after split."""
        X = pd.DataFrame({"a": range(20), "b": range(20, 40)}, index=range(100, 120))
        y = pd.Series(range(20), index=range(100, 120))

        X_train, X_test, y_train, y_test = split_data(
            X, y, test_size=0.2, random_state=42
        )

        assert list(X_train.index) == list(range(len(X_train)))
        assert list(X_test.index) == list(range(len(X_test)))
        assert list(y_train.index) == list(range(len(y_train)))
        assert list(y_test.index) == list(range(len(y_test)))


class TestPreprocessDataset:
    def test_full_pipeline(self):
        """Test the full preprocessing pipeline."""
        data = {
            "name": "test_dataset",
            "X": pd.DataFrame({
                "a": [1.0, 2.0, np.nan, 4.0, 5.0],
                "b": [10.0, np.nan, 30.0, 40.0, 50.0]
            }),
            "y": pd.Series([100.0, 200.0, 300.0, 400.0, 500.0])
        }

        result = preprocess_dataset(
            data, test_size=0.4, random_state=42, impute_strategy="mean"
        )

        assert "X_train" in result
        assert "X_test" in result
        assert "y_train" in result
        assert "y_test" in result
        assert "metadata" in result

        # Check metadata
        meta = result["metadata"]
        assert meta["dataset_name"] == "test_dataset"
        assert meta["original_size"] == 5
        assert meta["random_state"] == 42
        assert meta["impute_strategy"] == "mean"

        # Check no missing values in outputs
        assert not result["X_train"].isna().any().any()
        assert not result["X_test"].isna().any().any()
        assert not result["y_train"].isna().any()
        assert not result["y_test"].isna().any()

    def test_validation_failure(self):
        """Test that invalid target raises an error."""
        data = {
            "name": "bad_dataset",
            "X": pd.DataFrame({"a": [1.0, 2.0, 3.0]}),
            "y": pd.Series([5.0, 5.0, 5.0])  # Zero variance
        }

        with pytest.raises(ValueError, match="variance"):
            preprocess_dataset(data, target_min_variance=1e-6)

    def test_reproducibility(self):
        """Test that preprocessing is reproducible."""
        np.random.seed(42)
        X = pd.DataFrame({
            "a": np.random.randn(50),
            "b": np.random.randn(50)
        })
        y = pd.Series(np.random.randn(50))

        data1 = {"name": "rep_test", "X": X, "y": y}
        data2 = {"name": "rep_test", "X": X, "y": y}

        result1 = preprocess_dataset(data1, random_state=999)
        result2 = preprocess_dataset(data2, random_state=999)

        pd.testing.assert_frame_equal(result1["X_train"], result2["X_train"])
        pd.testing.assert_frame_equal(result1["X_test"], result2["X_test"])
        pd.testing.assert_series_equal(result1["y_train"], result2["y_train"])
        pd.testing.assert_series_equal(result1["y_test"], result2["y_test"])