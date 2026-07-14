"""
Unit tests for edge cases in the data pipeline.
Tests empty datasets, missing columns, and data type inconsistencies.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.preprocessing import load_config, handle_high_missingness, apply_mice_imputation, apply_scale_scoring
from data.cohort import compute_propensity_scores, perform_matching
from analysis.models import fit_ols_model, create_interaction_term
from analysis.validation import calculate_smd, check_vif


class TestEmptyDatasets:
    """Tests for handling empty datasets."""

    def test_empty_dataframe_preprocessing(self):
        """Test that preprocessing handles empty DataFrames gracefully."""
        empty_df = pd.DataFrame()
        
        # handle_high_missingness should return empty DataFrame without error
        result = handle_high_missingness(empty_df, threshold=0.05)
        assert result.empty
        
        # apply_mice_imputation should handle empty DataFrame
        # Note: MICE might fail on empty data, so we expect an error or empty result
        with pytest.raises((ValueError, IndexError)):
            apply_mice_imputation(empty_df, ['age', 'gender'])

    def test_empty_dataframe_cohort(self):
        """Test that cohort construction handles empty datasets."""
        empty_df = pd.DataFrame()
        
        # compute_propensity_scores should handle empty DataFrame
        with pytest.raises((ValueError, KeyError)):
            compute_propensity_scores(empty_df, ['age', 'gender'])

    def test_empty_dataframe_modeling(self):
        """Test that modeling handles empty datasets."""
        empty_df = pd.DataFrame()
        
        # fit_ols_model should handle empty DataFrame
        with pytest.raises((ValueError, IndexError)):
            fit_ols_model(empty_df, 'depression', ['social_support', 'harassment_exposure'])


class TestMissingColumns:
    """Tests for handling missing columns in datasets."""

    def test_missing_required_column_preprocessing(self):
        """Test preprocessing with missing required columns."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'gender': ['M', 'F', 'M']
            # Missing 'education' column
        })
        
        # handle_high_missingness should handle missing columns gracefully
        result = handle_high_missingness(df, threshold=0.05)
        assert result is not None
        
        # apply_mice_imputation should raise error for missing columns
        with pytest.raises(KeyError):
            apply_mice_imputation(df, ['age', 'gender', 'education'])

    def test_missing_scale_columns(self):
        """Test scale scoring with missing scale items."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'depressed1': [1, 2, 3],
            # Missing other CES-D items
        })
        
        # apply_scale_scoring should handle missing items
        result = apply_scale_scoring(df)
        # Should not crash, may return NaN for missing scales
        assert result is not None

    def test_missing_cohort_columns(self):
        """Test cohort construction with missing propensity score columns."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'gender': ['M', 'F', 'M'],
            # Missing 'education' and 'income'
            'dataset_source': ['GSS', 'GSS', 'Cyber']
        })
        
        # compute_propensity_scores should handle missing columns
        with pytest.raises(KeyError):
            compute_propensity_scores(df, ['age', 'gender', 'education', 'income'])

    def test_missing_model_columns(self):
        """Test modeling with missing outcome or predictor columns."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'social_support': [10, 15, 20],
            # Missing 'depression' outcome column
        })
        
        # fit_ols_model should raise error for missing outcome
        with pytest.raises(KeyError):
            fit_ols_model(df, 'depression', ['social_support'])

        # Test with missing predictor
        df_with_outcome = df.copy()
        df_with_outcome['depression'] = [5, 10, 15]
        
        with pytest.raises(KeyError):
            fit_ols_model(df_with_outcome, 'depression', ['social_support', 'harassment_exposure'])


class TestDataQualityIssues:
    """Tests for data quality issues like all NaN columns, constant values, etc."""

    def test_all_nan_column(self):
        """Test handling of columns with all NaN values."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'nan_column': [np.nan, np.nan, np.nan],
            'social_support': [10, 15, 20],
            'depression': [5, 10, 15]
        })
        
        # handle_high_missingness should remove all-NaN columns
        result = handle_high_missingness(df, threshold=0.05)
        assert 'nan_column' not in result.columns

    def test_constant_column(self):
        """Test handling of columns with constant values."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'constant_col': [5, 5, 5],
            'social_support': [10, 15, 20],
            'depression': [5, 10, 15]
        })
        
        # create_interaction_term should handle constant columns
        result = create_interaction_term(df, 'social_support', 'constant_col')
        assert result is not None

    def test_single_row_dataframe(self):
        """Test handling of single-row DataFrames."""
        df = pd.DataFrame({
            'age': [25],
            'social_support': [10],
            'depression': [5]
        })
        
        # Most operations should fail gracefully on single row
        with pytest.raises((ValueError, IndexError)):
            fit_ols_model(df, 'depression', ['social_support'])

    def test_infinite_values(self):
        """Test handling of infinite values in data."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'social_support': [10, np.inf, 20],
            'depression': [5, 10, 15]
        })
        
        # Operations should handle or raise error for infinite values
        with pytest.raises((ValueError, FloatingPointError)):
            fit_ols_model(df, 'depression', ['social_support'])


class TestTypeInconsistencies:
    """Tests for data type inconsistencies."""

    def test_string_in_numeric_column(self):
        """Test handling of strings in numeric columns."""
        df = pd.DataFrame({
            'age': [25, 'thirty', 35],
            'social_support': [10, 15, 20],
            'depression': [5, 10, 15]
        })
        
        # Operations should handle type conversion errors
        with pytest.raises((ValueError, TypeError)):
            fit_ols_model(df, 'depression', ['age', 'social_support'])

    def test_mixed_types_in_categorical(self):
        """Test handling of mixed types in categorical columns."""
        df = pd.DataFrame({
            'gender': ['M', 'F', 1],
            'social_support': [10, 15, 20],
            'depression': [5, 10, 15]
        })
        
        # Operations should handle mixed types
        result = compute_propensity_scores(df, ['gender'])
        assert result is not None


class TestEdgeCaseValues:
    """Tests for extreme or edge case values."""

    def test_extreme_outliers(self):
        """Test handling of extreme outliers."""
        df = pd.DataFrame({
            'age': [25, 30, 35, 150],
            'social_support': [10, 15, 20, 1000],
            'depression': [5, 10, 15, 500]
        })
        
        # Models should handle outliers (may produce warnings)
        result = fit_ols_model(df, 'depression', ['age', 'social_support'])
        assert result is not None

    def test_zero_variance_in_predictor(self):
        """Test handling of zero variance in predictor variables."""
        df = pd.DataFrame({
            'age': [25, 25, 25],
            'social_support': [10, 15, 20],
            'depression': [5, 10, 15]
        })
        
        # fit_ols_model should handle zero variance
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            fit_ols_model(df, 'depression', ['age'])

    def test_perfect_multicollinearity(self):
        """Test handling of perfect multicollinearity."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'age_doubled': [50, 60, 70],
            'social_support': [10, 15, 20],
            'depression': [5, 10, 15]
        })
        
        # fit_ols_model should handle multicollinearity
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            fit_ols_model(df, 'depression', ['age', 'age_doubled', 'social_support'])

    def test_interaction_with_constant(self):
        """Test interaction term creation with constant variable."""
        df = pd.DataFrame({
            'social_support': [10, 15, 20],
            'constant': [5, 5, 5],
            'depression': [5, 10, 15]
        })
        
        result = create_interaction_term(df, 'social_support', 'constant')
        assert result is not None
        assert 'social_support:constant' in result.columns