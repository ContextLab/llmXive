"""
Contract test for data validation schema (User Story 1).

This test verifies that the validated dataset produced by the ingestion pipeline
adheres to the strict schema requirements defined in the project specifications.

It checks:
1. Required columns exist (alloy_id, hardness_vickers, and elemental compositions).
2. No null values in critical columns (hardness, elemental sums).
3. Elemental composition sums fall within the configured threshold (default 0.95-1.05).
4. Data types are correct (numeric for hardness and compositions).
5. Minimum sample count requirements are met (>= 100 for success, warning for 50-99).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from config import (
    get_data_processed_dir,
    get_composition_sum_threshold,
    get_min_samples_warning,
    get_min_samples_target
)
from utils.error_handlers import DataValidationError


class TestDataSchemaContract:
    """
    Contract tests for the solder hardness dataset schema.
    
    These tests ensure that any dataset passing through the ingestion pipeline
    meets the strict structural and validation requirements before being used
    for model training.
    """

    @pytest.fixture
    def expected_columns(self):
        """Define the mandatory columns for the validated dataset."""
        # Based on data-model.md and ingestion requirements
        return [
            'alloy_id',
            'hardness_vickers',
            'element_count',
            'composition_sum'
            # Note: Specific elemental columns (e.g., 'Sn', 'Ag', 'Cu') are dynamic
            # but must be present if the alloy contains them. We test for the base schema here.
        ]

    @pytest.fixture
    def processed_data_path(self):
        """Return the path to the processed validated dataset."""
        return get_data_processed_dir() / "solder_hardness_validated.csv"

    def test_file_exists(self, processed_data_path):
        """Contract: The validated dataset file must exist."""
        assert processed_data_path.exists(), (
            f"Processed dataset not found at {processed_data_path}. "
            "Ensure T012-T016 (ingestion pipeline) have been executed."
        )

    def test_required_columns_present(self, processed_data_path, expected_columns):
        """Contract: All mandatory schema columns must be present."""
        df = pd.read_csv(processed_data_path)
        
        missing = set(expected_columns) - set(df.columns)
        assert not missing, (
            f"Schema violation: Missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    def test_hardness_not_null(self, processed_data_path):
        """Contract: Vickers hardness values must be non-null."""
        df = pd.read_csv(processed_data_path)
        
        null_count = df['hardness_vickers'].isnull().sum()
        assert null_count == 0, (
            f"Schema violation: Found {null_count} null values in 'hardness_vickers'. "
            "All entries must have a measured hardness value."
        )

    def test_hardness_positive(self, processed_data_path):
        """Contract: Vickers hardness must be positive."""
        df = pd.read_csv(processed_data_path)
        
        negative_count = (df['hardness_vickers'] <= 0).sum()
        assert negative_count == 0, (
            f"Schema violation: Found {negative_count} non-positive hardness values. "
            "Hardness must be > 0."
        )

    def test_composition_sum_within_threshold(self, processed_data_path):
        """Contract: Elemental composition sums must be within configured threshold."""
        df = pd.read_csv(processed_data_path)
        threshold = get_composition_sum_threshold()
        
        # The cleaner ensures sum is close to 1.0, but we verify the stored column
        # against the config threshold (e.g., 0.95 to 1.05)
        # Note: The column 'composition_sum' is expected to be created by the cleaner/validator
        
        if 'composition_sum' not in df.columns:
            # If the column doesn't exist, we might need to calculate it dynamically
            # based on numeric columns, but the contract assumes the cleaner wrote it.
            # For this test, we assume the pipeline produced the column.
            pytest.fail("Column 'composition_sum' not found. Ingestion pipeline may be incomplete.")

        lower_bound = threshold.get('min', 0.95)
        upper_bound = threshold.get('max', 1.05)
        
        invalid_sums = df[
            (df['composition_sum'] < lower_bound) | 
            (df['composition_sum'] > upper_bound)
        ]
        
        assert len(invalid_sums) == 0, (
            f"Schema violation: Found {len(invalid_sums)} alloys with composition sums "
            f"outside [{lower_bound}, {upper_bound}]. Values: {invalid_sums['composition_sum'].tolist()}"
        )

    def test_element_count_valid(self, processed_data_path):
        """Contract: Element count must be <= max allowed (typically 5)."""
        df = pd.read_csv(processed_data_path)
        
        # Default max is 5 per spec (FR-002)
        # We read from config if available, otherwise default to 5
        max_elements = 5
        try:
            from config import get_max_elements
            max_elements = get_max_elements()
        except ImportError:
            pass

        invalid_count = (df['element_count'] > max_elements).sum()
        assert invalid_count == 0, (
            f"Schema violation: Found {invalid_count} alloys with > {max_elements} elements. "
            "Alloys must have <= 5 elements per project constraints."
        )

    def test_minimum_sample_size(self, processed_data_path):
        """Contract: Dataset must meet minimum sample size requirements."""
        df = pd.read_csv(processed_data_path)
        n = len(df)
        
        min_target = get_min_samples_target()  # Expected: 100
        min_warning = get_min_samples_warning()  # Expected: 50
        
        if n < min_warning:
            pytest.fail(
                f"Critical Failure: Dataset size ({n}) is below minimum warning threshold ({min_warning}). "
                "Cannot proceed with model training. Data source aggregation failed."
            )
        elif n < min_target:
            # This is a warning state, but strictly speaking the schema is valid.
            # However, for the "MVP" contract, we usually expect >= 100.
            # We mark this as a warning assertion that doesn't fail the test but logs.
            pytest.warns(
                UserWarning,
                match=f"Dataset size ({n}) is below target ({min_target}) but above warning threshold."
            )
            # For strict contract testing in CI, we might fail here if 100 is the hard requirement.
            # Given the task description: "verify output dataset contains >= 100 unique compositions"
            # We will assert >= 100 for the "completed" status.
            assert n >= min_target, (
                f"Schema violation: Dataset size ({n}) is below the target of {min_target}. "
                "The MVP requires >= 100 unique compositions."
            )

    def test_data_types_correct(self, processed_data_path):
        """Contract: Numeric columns must be numeric types."""
        df = pd.read_csv(processed_data_path)
        
        numeric_cols = ['hardness_vickers', 'element_count', 'composition_sum']
        
        for col in numeric_cols:
            if col in df.columns:
                assert pd.api.types.is_numeric_dtype(df[col]), (
                    f"Schema violation: Column '{col}' is not numeric. "
                    f"Found type: {df[col].dtype}"
                )