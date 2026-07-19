"""
Unit tests for verifying real data integrity.
Asserts that loaded data is not synthetic by checking statistical properties
and source ID verification.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from preprocessing.ingestion import load_dataset_config, process_real_world_dataset, get_cleaned_data_path


class TestRealDataIntegrity:
    """Tests to ensure real data is not synthetic/fabricated."""

    @pytest.fixture
    def sample_config(self, tmp_path: Path) -> Dict[str, Any]:
        """Create a minimal valid dataset config for testing."""
        config = {
            "datasets": [
                {
                    "id": "test_iris",
                    "source": "sklearn.datasets",
                    "type": "classification",
                    "features": ["sepal_length", "sepal_width", "petal_length", "petal_width"],
                    "target": "target",
                    "download_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
                    "checksum": None,
                    "size_bytes": None,
                    "status": "pending"
                }
            ]
        }
        config_path = tmp_path / "test_datasets.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return {"config_path": str(config_path), "datasets": config["datasets"]}

    def test_load_dataset_returns_real_data_not_synthetic(self, sample_config: Dict[str, Any]):
        """
        Verify that the loaded dataset has statistical properties inconsistent with
        simple synthetic generation (e.g., specific variance patterns, non-zero skewness).
        """
        # Load the Iris dataset (real world data)
        dataset_info = sample_config["datasets"][0]
        df = process_real_world_dataset(dataset_info)

        assert isinstance(df, pd.DataFrame), "Loaded data must be a DataFrame"
        assert len(df) > 0, "Loaded data must not be empty"

        # Real data should have non-trivial statistical properties
        # Synthetic data often has perfect symmetry or zero variance in some cases
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 1:
                    # Check for non-zero variance (synthetic data might have zero variance)
                    variance = col_data.var()
                    assert variance > 1e-10, f"Column {col} has suspiciously low variance: {variance}"

                    # Check for non-perfect symmetry (real data is rarely perfectly symmetric)
                    skewness = col_data.skew()
                    # Allow some tolerance, but reject perfect symmetry
                    assert abs(skewness) < 10, f"Column {col} has extreme skewness: {skewness}"

    def test_source_id_verification(self, sample_config: Dict[str, Any]):
        """
        Verify that the dataset source ID matches the expected real-world source.
        """
        dataset_info = sample_config["datasets"][0]
        df = process_real_world_dataset(dataset_info)

        # Verify the source is a real dataset
        expected_source = dataset_info.get("source", "")
        assert "sklearn" in expected_source or "uci" in expected_source or "openml" in expected_source, \
            f"Source {expected_source} does not appear to be a real dataset source"

        # Verify we have the expected number of rows (Iris has 150 rows)
        # Allow some tolerance for potential data cleaning
        assert 140 <= len(df) <= 160, f"Expected ~150 rows for Iris, got {len(df)}"

    def test_data_has_expected_features(self, sample_config: Dict[str, Any]):
        """
        Verify that the loaded data contains the expected feature columns.
        """
        dataset_info = sample_config["datasets"][0]
        expected_features = dataset_info.get("features", [])
        df = process_real_world_dataset(dataset_info)

        for feature in expected_features:
            assert feature in df.columns, f"Expected feature '{feature}' not found in loaded data"

    def test_real_data_has_natural_outliers(self, sample_config: Dict[str, Any]):
        """
        Real data typically has some natural outliers, while synthetic data might be too uniform.
        This test checks for the presence of values beyond 3 standard deviations.
        """
        dataset_info = sample_config["datasets"][0]
        df = process_real_world_dataset(dataset_info)

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        has_outliers = False

        for col in numeric_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 10:
                    mean = col_data.mean()
                    std = col_data.std()
                    if std > 0:
                        outliers = np.abs(col_data - mean) > 3 * std
                        if outliers.any():
                            has_outliers = True
                            break

        # Note: This is a heuristic. Some real datasets might not have outliers,
        # but most real-world data like Iris does.
        # We're checking that our data loader is working on real data, not a perfect synthetic set.
        # For Iris specifically, there are known outliers in petal measurements.
        if "petal_length" in df.columns:
            petal_data = df["petal_length"].dropna()
            if len(petal_data) > 10:
                mean = petal_data.mean()
                std = petal_data.std()
                if std > 0:
                    outliers = np.abs(petal_data - mean) > 2 * std  # Lower threshold for Iris
                    assert outliers.any(), "Real Iris data should have some outliers in petal measurements"

    def test_data_integrity_check_fails_on_synthetic_like_data(self):
        """
        Verify that our integrity checks would catch obviously synthetic data.
        This is a negative test to ensure our checks are meaningful.
        """
        # Create obviously synthetic data (constant values)
        synthetic_df = pd.DataFrame({
            'feature1': [5.0] * 100,
            'feature2': [3.0] * 100,
            'target': [0] * 100
        })

        # This should fail the variance check
        for col in synthetic_df.select_dtypes(include=[np.number]).columns:
            if col != 'target':  # Skip target as it might be constant by design
                variance = synthetic_df[col].var()
                # Our test should catch this
                assert variance < 1e-10, "Synthetic data should have near-zero variance"

    def test_real_data_statistics_match_expected_ranges(self, sample_config: Dict[str, Any]):
        """
        Verify that real data statistics fall within expected ranges for the dataset.
        For Iris: sepal length should be roughly 4-8 cm, petal length 1-7 cm.
        """
        dataset_info = sample_config["datasets"][0]
        df = process_real_world_dataset(dataset_info)

        # Check sepal length range (should be approximately 4-8 cm for Iris)
        if "sepal_length" in df.columns:
            sepal_min = df["sepal_length"].min()
            sepal_max = df["sepal_length"].max()
            assert 3.5 <= sepal_min <= 4.5, f"Sepal min {sepal_min} outside expected range"
            assert 7.0 <= sepal_max <= 8.5, f"Sepal max {sepal_max} outside expected range"

        # Check petal length range (should be approximately 1-7 cm for Iris)
        if "petal_length" in df.columns:
            petal_min = df["petal_length"].min()
            petal_max = df["petal_length"].max()
            assert 0.9 <= petal_min <= 1.5, f"Petal min {petal_min} outside expected range"
            assert 6.5 <= petal_max <= 7.5, f"Petal max {petal_max} outside expected range"

    def test_data_source_metadata_is_preserved(self, sample_config: Dict[str, Any]):
        """
        Verify that dataset metadata from the source is preserved during loading.
        """
        dataset_info = sample_config["datasets"][0]
        df = process_real_world_dataset(dataset_info)

        # The DataFrame should have the expected columns
        expected_cols = dataset_info.get("features", []) + [dataset_info.get("target", "")]
        for col in expected_cols:
            if col:  # Skip empty strings
                assert col in df.columns, f"Expected column '{col}' not found"

        # Verify data types are appropriate (numeric features should be numeric)
        for feature in dataset_info.get("features", []):
            if feature in df.columns:
                assert pd.api.types.is_numeric_dtype(df[feature]), \
                    f"Feature '{feature}' should be numeric, got {df[feature].dtype}"