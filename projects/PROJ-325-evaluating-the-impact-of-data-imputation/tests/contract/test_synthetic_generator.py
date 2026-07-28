"""
Contract test for synthetic data generation (US2).

This test verifies that the synthetic data generator produces data
where the calculated variance matches the declared `true_variance`
within a small tolerance, satisfying the contract requirements.
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

# Ensure code directory is in path for imports
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from synthetic_generator import generate_synthetic_data


class TestSyntheticGeneratorContract:
    """Contract tests for the synthetic data generator."""

    @pytest.mark.parametrize(
        "true_mean,true_variance,n_samples,mechanism",
        [
            (0.0, 1.0, 1000, "MCAR"),
            (10.0, 25.0, 2000, "MAR"),
            (-5.0, 100.0, 5000, "MCAR"),
            (50.0, 400.0, 10000, "MAR"),
        ],
        ids=["std_normal", "shifted_scaled", "negative_mean", "large_variance"],
    )
    def test_synthetic_produces_known_variance(
        self, true_mean, true_variance, n_samples, mechanism
    ):
        """
        Test that the generated synthetic data has a variance matching
        the `true_variance` parameter within a small tolerance.

        This validates the generator's ability to create data with
        known super-population parameters as required by FR-002b and SC-001.
        """
        # Generate synthetic data
        data, metadata = generate_synthetic_data(
            n_samples=n_samples,
            true_mean=true_mean,
            true_variance=true_variance,
            missingness_mechanism=mechanism,
            random_seed=42,  # Fixed seed for reproducibility
        )

        # Validate that data is returned as a DataFrame
        assert isinstance(data, pd.DataFrame), "Data must be a pandas DataFrame"
        assert "value" in data.columns, "Data must contain a 'value' column"

        # Extract the complete cases (non-missing values) to calculate variance
        # Note: We compare the variance of the non-missing values against the
        # true variance. With a large enough sample, this should be close.
        complete_cases = data["value"].dropna()

        # Calculate observed variance
        observed_variance = complete_cases.var(ddof=1)

        # Define tolerance (relative error)
        # Allow 5% relative error due to sampling noise
        tolerance = 0.05 * true_variance

        # Assert that observed variance is within tolerance of true variance
        assert np.isclose(
            observed_variance, true_variance, atol=tolerance
        ), (
            f"Observed variance ({observed_variance:.4f}) does not match "
            f"true variance ({true_variance:.4f}) within tolerance ({tolerance:.4f}). "
            f"Relative error: {abs(observed_variance - true_variance) / true_variance:.2%}"
        )

        # Validate metadata contains required fields
        assert "true_mean" in metadata, "Metadata must contain 'true_mean'"
        assert "true_variance" in metadata, "Metadata must contain 'true_variance'"
        assert "missingness_mechanism" in metadata, "Metadata must contain 'missingness_mechanism'"

        # Validate metadata matches generation parameters
        assert metadata["true_mean"] == true_mean
        assert metadata["true_variance"] == true_variance
        assert metadata["missingness_mechanism"] == mechanism

        # Validate data shape
        assert len(data) == n_samples, f"Data length ({len(data)}) must match n_samples ({n_samples})"

    def test_synthetic_metadata_schema(self):
        """
        Test that the metadata JSON schema matches the contract requirements.
        """
        data, metadata = generate_synthetic_data(
            n_samples=1000,
            true_mean=0.0,
            true_variance=1.0,
            missingness_mechanism="MAR",
            random_seed=123,
        )

        # Check required keys
        required_keys = ["true_mean", "true_variance", "missingness_mechanism"]
        for key in required_keys:
            assert key in metadata, f"Metadata must contain '{key}'"

        # Check types
        assert isinstance(metadata["true_mean"], (int, float))
        assert isinstance(metadata["true_variance"], (int, float))
        assert isinstance(metadata["missingness_mechanism"], str)
        assert metadata["missingness_mechanism"] in ["MCAR", "MAR", "MNAR"]

    def test_synthetic_data_schema(self):
        """
        Test that the generated data conforms to the dataset schema.
        """
        data, metadata = generate_synthetic_data(
            n_samples=500,
            true_mean=10.0,
            true_variance=5.0,
            missingness_mechanism="MCAR",
            random_seed=456,
        )

        # Check DataFrame structure
        assert isinstance(data, pd.DataFrame)
        assert "value" in data.columns

        # Check data types
        assert data["value"].dtype in [np.float64, np.float32, object]

        # Check for NaN values (expected with missingness)
        assert data["value"].isna().any(), "Expected some missing values in generated data"

        # Check missingness rate is reasonable (not 0% or 100%)
        missing_rate = data["value"].isna().sum() / len(data)
        assert 0 < missing_rate < 1, f"Missingness rate ({missing_rate}) should be between 0 and 1"