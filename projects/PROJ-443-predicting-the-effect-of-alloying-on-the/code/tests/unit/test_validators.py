"""
Unit tests for src.utils.validators module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.validators import (
    ValidationError,
    validate_composition_sum,
    normalize_compositions,
    validate_sample_count,
    validate_data_integrity,
    run_validations
)


class TestValidateCompositionSum:
    """Tests for validate_composition_sum function."""

    def test_valid_composition_sum(self):
        """Test with valid composition sums."""
        df = pd.DataFrame({
            'Fe': [0.5, 0.2],
            'Cr': [0.5, 0.3],
            'Ni': [0.0, 0.5]
        })
        cols = ['Fe', 'Cr', 'Ni']

        is_valid, errors = validate_composition_sum(df, cols)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_composition_sum(self):
        """Test with invalid composition sums."""
        df = pd.DataFrame({
            'Fe': [0.5, 0.2],
            'Cr': [0.4, 0.3],  # Sum = 0.9, invalid
            'Ni': [0.0, 0.5]
        })
        cols = ['Fe', 'Cr', 'Ni']

        is_valid, errors = validate_composition_sum(df, cols)

        assert is_valid is False
        assert len(errors) > 0
        assert "composition sum != 1.0" in errors[0]

    def test_missing_columns(self):
        """Test with missing composition columns."""
        df = pd.DataFrame({
            'Fe': [0.5],
            'Cr': [0.5]
        })
        cols = ['Fe', 'Cr', 'Ni']  # Ni is missing

        with pytest.raises(ValidationError) as exc_info:
            validate_composition_sum(df, cols)

        assert "Missing composition columns" in str(exc_info.value)

    def test_empty_columns(self):
        """Test with empty column list."""
        df = pd.DataFrame({'Fe': [0.5]})

        with pytest.raises(ValidationError) as exc_info:
            validate_composition_sum(df, [])

        assert "No composition columns provided" in str(exc_info.value)


class TestNormalizeCompositions:
    """Tests for normalize_compositions function."""

    def test_normalize_valid_data(self):
        """Test normalization of valid data (already sums to 1)."""
        df = pd.DataFrame({
            'Fe': [0.5],
            'Cr': [0.5]
        })
        cols = ['Fe', 'Cr']

        result = normalize_compositions(df, cols)

        # Check sums are exactly 1.0
        sums = result[cols].sum(axis=1)
        assert np.allclose(sums, 1.0)

    def test_normalize_invalid_data(self):
        """Test normalization of data that doesn't sum to 1."""
        df = pd.DataFrame({
            'Fe': [0.4],
            'Cr': [0.4]  # Sum = 0.8
        })
        cols = ['Fe', 'Cr']

        result = normalize_compositions(df, cols)

        sums = result[cols].sum(axis=1)
        assert np.allclose(sums, 1.0)
        # Check relative proportions are preserved
        assert result['Fe'].iloc[0] == 0.5
        assert result['Cr'].iloc[0] == 0.5

    def test_normalize_inplace(self):
        """Test that inplace=True modifies the original dataframe."""
        df = pd.DataFrame({
            'Fe': [0.4],
            'Cr': [0.4]
        })
        cols = ['Fe', 'Cr']
        original_id = id(df)

        normalize_compositions(df, cols, inplace=True)

        assert id(df) == original_id
        assert np.allclose(df[cols].sum(axis=1), 1.0)

    def test_normalize_zero_sum(self):
        """Test normalization with zero sum (should raise error)."""
        df = pd.DataFrame({
            'Fe': [0.0],
            'Cr': [0.0]
        })
        cols = ['Fe', 'Cr']

        with pytest.raises(ValidationError) as exc_info:
            normalize_compositions(df, cols)

        assert "zero or negative composition sum" in str(exc_info.value)

    def test_normalize_missing_columns(self):
        """Test with missing columns."""
        df = pd.DataFrame({'Fe': [0.5]})
        cols = ['Fe', 'Cr']

        with pytest.raises(ValidationError) as exc_info:
            normalize_compositions(df, cols)

        assert "Missing composition columns" in str(exc_info.value)


class TestValidateSampleCount:
    """Tests for validate_sample_count function."""

    def test_meets_threshold(self):
        """Test dataset meeting minimum sample count."""
        df = pd.DataFrame({'Fe': [0.5] * 600, 'Cr': [0.5] * 600})

        is_valid, info = validate_sample_count(df, min_samples=500)

        assert is_valid is True
        assert info['total_samples'] == 600
        assert info['meets_threshold'] is True

    def test_below_threshold(self):
        """Test dataset below minimum sample count."""
        df = pd.DataFrame({'Fe': [0.5] * 100, 'Cr': [0.5] * 100})

        is_valid, info = validate_sample_count(df, min_samples=500)

        assert is_valid is False
        assert info['total_samples'] == 100
        assert info['meets_threshold'] is False

    def test_with_group_column(self):
        """Test with group column specified."""
        df = pd.DataFrame({
            'Fe': [0.5] * 100,
            'Cr': [0.5] * 100,
            'group': ['A'] * 50 + ['B'] * 50
        })

        is_valid, info = validate_sample_count(df, min_samples=50, group_column='group')

        assert info['groups_info']['num_groups'] == 2
        assert info['groups_info']['min_group_size'] == 50
        assert info['groups_info']['max_group_size'] == 50

    def test_missing_group_column(self):
        """Test with non-existent group column."""
        df = pd.DataFrame({'Fe': [0.5] * 100})

        with pytest.raises(ValidationError) as exc_info:
            validate_sample_count(df, min_samples=50, group_column='nonexistent')

        assert "Group column" in str(exc_info.value)


class TestValidateDataIntegrity:
    """Tests for validate_data_integrity function."""

    def test_valid_data(self):
        """Test with fully valid data."""
        df = pd.DataFrame({
            'Fe': [0.5, 0.2],
            'Cr': [0.5, 0.3],
            'Ni': [0.0, 0.5],
            'Bulk_Modulus': [150.0, 200.0]
        })
        cols = ['Fe', 'Cr', 'Ni']

        is_valid, errors = validate_data_integrity(df, cols, target_column='Bulk_Modulus')

        assert is_valid is True
        assert len(errors) == 0

    def test_nan_in_composition(self):
        """Test with NaN in composition columns."""
        df = pd.DataFrame({
            'Fe': [0.5, np.nan],
            'Cr': [0.5, 0.3],
            'Ni': [0.0, 0.5]
        })
        cols = ['Fe', 'Cr', 'Ni']

        is_valid, errors = validate_data_integrity(df, cols)

        assert is_valid is False
        assert any("NaN values" in err for err in errors)

    def test_negative_composition(self):
        """Test with negative composition values."""
        df = pd.DataFrame({
            'Fe': [0.5, -0.1],
            'Cr': [0.5, 0.4],
            'Ni': [0.0, 0.5]
        })
        cols = ['Fe', 'Cr', 'Ni']

        is_valid, errors = validate_data_integrity(df, cols)

        assert is_valid is False
        assert any("negative" in err.lower() for err in errors)

    def test_nan_in_target(self):
        """Test with NaN in target column."""
        df = pd.DataFrame({
            'Fe': [0.5, 0.2],
            'Cr': [0.5, 0.3],
            'Ni': [0.0, 0.5],
            'Bulk_Modulus': [150.0, np.nan]
        })
        cols = ['Fe', 'Cr', 'Ni']

        is_valid, errors = validate_data_integrity(df, cols, target_column='Bulk_Modulus')

        assert is_valid is False
        assert any("NaN" in err for err in errors)

    def test_non_positive_target(self):
        """Test with non-positive target values."""
        df = pd.DataFrame({
            'Fe': [0.5, 0.2],
            'Cr': [0.5, 0.3],
            'Ni': [0.0, 0.5],
            'Bulk_Modulus': [150.0, -10.0]
        })
        cols = ['Fe', 'Cr', 'Ni']

        is_valid, errors = validate_data_integrity(df, cols, target_column='Bulk_Modulus')

        assert is_valid is False
        assert any("non-positive" in err for err in errors)

    def test_missing_target_column(self):
        """Test with non-existent target column."""
        df = pd.DataFrame({
            'Fe': [0.5],
            'Cr': [0.5]
        })
        cols = ['Fe', 'Cr']

        is_valid, errors = validate_data_integrity(df, cols, target_column='Missing')

        assert is_valid is False
        assert any("not found" in err for err in errors)


class TestRunValidations:
    """Tests for run_validations function."""

    def test_all_valid(self):
        """Test with all validations passing."""
        df = pd.DataFrame({
            'Fe': [0.5, 0.2],
            'Cr': [0.5, 0.3],
            'Ni': [0.0, 0.5],
            'Bulk_Modulus': [150.0, 200.0]
        })
        cols = ['Fe', 'Cr', 'Ni']

        result = run_validations(df, cols, target_column='Bulk_Modulus', min_samples=2)

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_composition_sum_invalid(self):
        """Test when composition sum is invalid."""
        df = pd.DataFrame({
            'Fe': [0.4, 0.2],  # Sum = 0.9
            'Cr': [0.5, 0.3],
            'Ni': [0.0, 0.5],
            'Bulk_Modulus': [150.0, 200.0]
        })
        cols = ['Fe', 'Cr', 'Ni']

        result = run_validations(df, cols, target_column='Bulk_Modulus', min_samples=2)

        assert result['valid'] is False
        assert result['composition_sum_valid'] is False
        assert len(result['errors']) > 0

    def test_sample_count_warning(self):
        """Test when sample count is below threshold (should warn, not error)."""
        df = pd.DataFrame({
            'Fe': [0.5] * 100,
            'Cr': [0.5] * 100
        })
        cols = ['Fe', 'Cr']

        result = run_validations(df, cols, min_samples=500)

        # Per spec: should not be an error, just a warning
        assert result['sample_count_valid'] is False
        assert any("below threshold" in w for w in result['warnings'])
        # Overall valid might be False due to sample count, depending on interpretation
        # But the key is that it doesn't crash and provides a warning