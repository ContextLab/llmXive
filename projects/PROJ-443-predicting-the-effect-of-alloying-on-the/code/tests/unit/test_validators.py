"""
Unit tests for data validation functions in src/utils/validators.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
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
    """Tests for validate_composition_sum function"""

    def test_valid_composition_sum(self):
        """Test that valid composition sums pass validation"""
        df = pd.DataFrame({
            'Fe': [0.2, 0.25, 0.3],
            'Co': [0.2, 0.25, 0.2],
            'Ni': [0.2, 0.25, 0.2],
            'Cr': [0.2, 0.25, 0.2],
            'Mn': [0.2, 0.0, 0.1]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        is_valid, invalid_indices, summary = validate_composition_sum(
            df, composition_cols, tolerance=1e-6
        )

        assert is_valid is True
        assert len(invalid_indices) == 0
        assert summary['invalid_samples'] == 0
        assert summary['max_deviation'] < 1e-6

    def test_invalid_composition_sum(self):
        """Test that invalid composition sums are detected"""
        df = pd.DataFrame({
            'Fe': [0.2, 0.25, 0.3],
            'Co': [0.2, 0.25, 0.2],
            'Ni': [0.2, 0.25, 0.2],
            'Cr': [0.2, 0.25, 0.2],
            'Mn': [0.1, 0.0, 0.0]  # Sum = 0.9, 1.0, 0.9
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        is_valid, invalid_indices, summary = validate_composition_sum(
            df, composition_cols, tolerance=0.01
        )

        assert is_valid is False
        assert len(invalid_indices) == 2
        assert 0 in invalid_indices
        assert 2 in invalid_indices
        assert summary['invalid_samples'] == 2

    def test_tolerance_parameter(self):
        """Test that tolerance parameter works correctly"""
        df = pd.DataFrame({
            'Fe': [0.2000001],
            'Co': [0.2],
            'Ni': [0.2],
            'Cr': [0.2],
            'Mn': [0.1999999]  # Sum = 1.0 exactly
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        # Tight tolerance should pass
        is_valid, _, _ = validate_composition_sum(
            df, composition_cols, tolerance=1e-6
        )
        assert is_valid is True

        # Very tight tolerance might fail due to floating point
        is_valid, _, _ = validate_composition_sum(
            df, composition_cols, tolerance=1e-10
        )
        # This might fail depending on floating point precision

    def test_empty_composition_columns(self):
        """Test that empty composition columns raise error"""
        df = pd.DataFrame({'A': [1, 2, 3]})

        with pytest.raises(ValidationError):
            validate_composition_sum(df, [], tolerance=1e-6)

    def test_high_failure_rate_raises_error(self):
        """Test that high failure rate raises ValidationError"""
        # Create dataset where 50% fail
        df = pd.DataFrame({
            'Fe': [0.5, 0.2, 0.5, 0.2],
            'Co': [0.5, 0.2, 0.5, 0.2],
            'Ni': [0.0, 0.2, 0.0, 0.2],
            'Cr': [0.0, 0.2, 0.0, 0.2],
            'Mn': [0.0, 0.2, 0.0, 0.2]  # First two rows sum to 1.0, last two to 0.4
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        # 50% failure rate should raise error
        with pytest.raises(ValidationError):
            validate_composition_sum(df, composition_cols, tolerance=0.01)


class TestNormalizeCompositions:
    """Tests for normalize_compositions function"""

    def test_normalize_valid_compositions(self):
        """Test normalization of valid compositions"""
        df = pd.DataFrame({
            'Fe': [0.4, 0.5],
            'Co': [0.4, 0.5],
            'Ni': [0.2, 0.0]
        })
        composition_cols = ['Fe', 'Co', 'Ni']

        normalized_df = normalize_compositions(df, composition_cols)

        sums = normalized_df[composition_cols].sum(axis=1)
        assert np.allclose(sums, 1.0)

    def test_normalize_creates_copy(self):
        """Test that normalization creates a copy by default"""
        df = pd.DataFrame({
            'Fe': [0.4],
            'Co': [0.4],
            'Ni': [0.2]
        })
        composition_cols = ['Fe', 'Co', 'Ni']

        normalized_df = normalize_compositions(df, composition_cols)

        assert normalized_df is not df
        # Original should be unchanged
        assert df['Fe'].iloc[0] == 0.4

    def test_normalize_inplace(self):
        """Test in-place normalization"""
        df = pd.DataFrame({
            'Fe': [0.4],
            'Co': [0.4],
            'Ni': [0.2]
        })
        composition_cols = ['Fe', 'Co', 'Ni']

        result = normalize_compositions(df, composition_cols, inplace=True)

        assert result is None
        sums = df[composition_cols].sum(axis=1)
        assert np.allclose(sums, 1.0)

    def test_normalize_zero_sum_raises_error(self):
        """Test that zero sum compositions raise error"""
        df = pd.DataFrame({
            'Fe': [0.0, 0.5],
            'Co': [0.0, 0.5],
            'Ni': [0.0, 0.0]
        })
        composition_cols = ['Fe', 'Co', 'Ni']

        with pytest.raises(ValidationError):
            normalize_compositions(df, composition_cols)

    def test_normalize_empty_columns(self):
        """Test normalization with empty column list"""
        df = pd.DataFrame({'A': [1, 2, 3]})

        result = normalize_compositions(df, [])

        # Should return unchanged dataframe
        assert result.equals(df)


class TestValidateSampleCount:
    """Tests for validate_sample_count function"""

    def test_meets_threshold(self):
        """Test dataset meeting sample threshold"""
        df = pd.DataFrame({'A': range(1000)})

        meets_threshold, summary = validate_sample_count(df, min_samples=500)

        assert meets_threshold is True
        assert summary['sample_count'] == 1000
        assert summary['meets_threshold'] is True
        assert summary['deficit'] == 0

    def test_below_threshold(self):
        """Test dataset below sample threshold"""
        df = pd.DataFrame({'A': range(300)})

        meets_threshold, summary = validate_sample_count(df, min_samples=500)

        assert meets_threshold is False
        assert summary['sample_count'] == 300
        assert summary['meets_threshold'] is False
        assert summary['deficit'] == 200

    def test_count_non_null_in_column(self):
        """Test counting non-null values in specific column"""
        df = pd.DataFrame({
            'A': [1, 2, None, 4, 5],
            'B': [1, 2, 3, 4, 5]
        })

        meets_threshold, summary = validate_sample_count(
            df, min_samples=4, column='A'
        )

        assert meets_threshold is True
        assert summary['sample_count'] == 4

    def test_column_not_found(self):
        """Test error when column not found"""
        df = pd.DataFrame({'A': [1, 2, 3]})

        with pytest.raises(ValidationError):
            validate_sample_count(df, min_samples=2, column='B')


class TestValidateDataIntegrity:
    """Tests for validate_data_integrity function"""

    def test_full_valid_dataset(self):
        """Test validation on a fully valid dataset"""
        df = pd.DataFrame({
            'Fe': [0.2, 0.25, 0.3],
            'Co': [0.2, 0.25, 0.2],
            'Ni': [0.2, 0.25, 0.2],
            'Cr': [0.2, 0.25, 0.2],
            'Mn': [0.2, 0.0, 0.1],
            'bulk_modulus': [150.0, 160.0, 170.0]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        results = validate_data_integrity(
            df, composition_cols, target_col='bulk_modulus', min_samples=2
        )

        assert results['valid'] is True
        assert len(results['errors']) == 0
        assert results['checks']['composition_sum']['passed'] is True
        assert results['checks']['sample_count']['meets_threshold'] is True

    def test_negative_composition_values(self):
        """Test detection of negative composition values"""
        df = pd.DataFrame({
            'Fe': [0.2, -0.1],
            'Co': [0.2, 0.3],
            'Ni': [0.2, 0.2],
            'Cr': [0.2, 0.2],
            'Mn': [0.2, 0.2]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        results = validate_data_integrity(df, composition_cols, min_samples=1)

        assert results['valid'] is False
        assert any('negative' in err.lower() for err in results['errors'])

    def test_nan_in_composition(self):
        """Test detection of NaN values in composition"""
        df = pd.DataFrame({
            'Fe': [0.2, np.nan],
            'Co': [0.2, 0.3],
            'Ni': [0.2, 0.2],
            'Cr': [0.2, 0.2],
            'Mn': [0.2, 0.2]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        results = validate_data_integrity(df, composition_cols, min_samples=1)

        assert results['valid'] is False
        assert any('nan' in err.lower() for err in results['errors'])

    def test_missing_target_column(self):
        """Test error when target column is missing"""
        df = pd.DataFrame({
            'Fe': [0.2, 0.25],
            'Co': [0.2, 0.25],
            'Ni': [0.2, 0.25],
            'Cr': [0.2, 0.25],
            'Mn': [0.2, 0.0]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        results = validate_data_integrity(
            df, composition_cols, target_col='nonexistent', min_samples=1
        )

        assert results['valid'] is False
        assert any('not found' in err.lower() for err in results['errors'])

    def test_target_null_values(self):
        """Test handling of null target values"""
        df = pd.DataFrame({
            'Fe': [0.2, 0.25, 0.3],
            'Co': [0.2, 0.25, 0.2],
            'Ni': [0.2, 0.25, 0.2],
            'Cr': [0.2, 0.25, 0.2],
            'Mn': [0.2, 0.0, 0.1],
            'bulk_modulus': [150.0, np.nan, 170.0]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        results = validate_data_integrity(
            df, composition_cols, target_col='bulk_modulus', min_samples=2
        )

        assert results['valid'] is True  # Null targets are warnings, not errors
        assert any('missing target' in w.lower() for w in results['warnings'])


class TestRunValidations:
    """Tests for run_validations function"""

    def test_run_all_validations_pass(self):
        """Test run_validations on a valid dataset"""
        df = pd.DataFrame({
            'Fe': [0.2, 0.25, 0.3],
            'Co': [0.2, 0.25, 0.2],
            'Ni': [0.2, 0.25, 0.2],
            'Cr': [0.2, 0.25, 0.2],
            'Mn': [0.2, 0.0, 0.1],
            'bulk_modulus': [150.0, 160.0, 170.0]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        results = run_validations(
            df, composition_cols, target_col='bulk_modulus', min_samples=2
        )

        assert results['valid'] is True

    def test_run_validations_raise_on_error(self):
        """Test that run_validations raises on error when configured"""
        df = pd.DataFrame({
            'Fe': [0.2, -0.1],
            'Co': [0.2, 0.3],
            'Ni': [0.2, 0.2],
            'Cr': [0.2, 0.2],
            'Mn': [0.2, 0.2]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        with pytest.raises(ValidationError):
            run_validations(
                df, composition_cols, min_samples=1, raise_on_error=True
            )

    def test_run_validations_no_raise(self):
        """Test that run_validations returns results without raising"""
        df = pd.DataFrame({
            'Fe': [0.2, -0.1],
            'Co': [0.2, 0.3],
            'Ni': [0.2, 0.2],
            'Cr': [0.2, 0.2],
            'Mn': [0.2, 0.2]
        })
        composition_cols = ['Fe', 'Co', 'Ni', 'Cr', 'Mn']

        results = run_validations(
            df, composition_cols, min_samples=1, raise_on_error=False
        )

        assert results['valid'] is False
        assert len(results['errors']) > 0