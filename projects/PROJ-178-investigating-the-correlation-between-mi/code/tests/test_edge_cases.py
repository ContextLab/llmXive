import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from analysis.model import calculate_unadjusted_spearman, calculate_rank_ols
from analysis.sensitivity import recalculate_burden_at_threshold, calculate_correlation

class TestZeroBurdenScenarios:
    """Test edge cases where heteroplasmy burden is zero."""

    def test_zero_burden_spearman(self):
        """Test Spearman correlation when all samples have zero burden."""
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [0.0, 0.0, 0.0, 0.0, 0.0],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        # Should not raise an error, but correlation should be NaN or undefined
        results = calculate_unadjusted_spearman(df)
        
        assert 'correlation' in results.columns
        assert 'p_value' in results.columns
        # With zero variance in burden, correlation is mathematically undefined
        # scipy returns NaN in this case
        assert pd.isna(results['correlation'].values[0]) or results['correlation'].values[0] == 0.0

    def test_zero_burden_rank_ols(self):
        """Test Rank-OLS when all samples have zero burden."""
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60, 70],
            'burden': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'depth': [10, 20, 30, 40, 50, 60],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
            'sex': ['M', 'F', 'M', 'F', 'M', 'F']
        })
        
        # Should handle zero variance gracefully
        results = calculate_rank_ols(df)
        
        assert 'variable' in results.columns
        assert 'coefficient' in results.columns
        # The coefficient for rank_burden should be NaN or 0 due to zero variance
        burden_row = results[results['variable'] == 'rank_burden']
        if not burden_row.empty:
            coef = burden_row['coefficient'].values[0]
            assert pd.isna(coef) or coef == 0.0

    def test_single_nonzero_burden(self):
        """Test with only one sample having non-zero burden."""
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [0.0, 0.0, 0.0, 0.0, 0.5],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        results = calculate_unadjusted_spearman(df)
        assert 'correlation' in results.columns
        # This should produce a valid (though potentially unstable) correlation
        assert not pd.isna(results['correlation'].values[0])

class TestMissingHaplogroupScenarios:
    """Test edge cases where haplogroup assignment fails."""

    def test_missing_haplogroup_in_dataset(self):
        """Test that models handle missing haplogroup values."""
        # Create a dataset with missing haplogroup (though model.py doesn't use haplogroup directly)
        # This tests the robustness of the data pipeline
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [0.1, 0.2, 0.3, 0.4, 0.5],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        # The model functions should work without haplogroup column
        spearman_results = calculate_unadjusted_spearman(df)
        assert not spearman_results.empty
        
        ols_results = calculate_rank_ols(df)
        assert not ols_results.empty

    def test_all_missing_haplogroup(self):
        """Test when all samples have missing haplogroup."""
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [0.1, 0.2, 0.3, 0.4, 0.5],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        # Models should still run as they don't depend on haplogroup
        results = calculate_rank_ols(df)
        assert 'coefficient' in results.columns

class TestEmptyDatasetScenarios:
    """Test edge cases with empty or near-empty datasets."""

    def test_empty_dataframe(self):
        """Test with completely empty dataframe."""
        df = pd.DataFrame(columns=['age', 'burden', 'depth', 'PC1', 'PC2', 'sex'])
        
        with pytest.raises((ValueError, IndexError)):
            calculate_unadjusted_spearman(df)

    def test_single_row(self):
        """Test with only one sample."""
        df = pd.DataFrame({
            'age': [20],
            'burden': [0.1],
            'depth': [10],
            'PC1': [0.1],
            'PC2': [0.2],
            'sex': ['M']
        })
        
        # Spearman requires at least 2 samples
        with pytest.raises((ValueError, IndexError)):
            calculate_unadjusted_spearman(df)

    def test_two_rows(self):
        """Test with minimum viable dataset."""
        df = pd.DataFrame({
            'age': [20, 30],
            'burden': [0.1, 0.2],
            'depth': [10, 20],
            'PC1': [0.1, 0.2],
            'PC2': [0.2, 0.3],
            'sex': ['M', 'F']
        })
        
        results = calculate_unadjusted_spearman(df)
        assert 'correlation' in results.columns

class TestBoundaryConditions:
    """Test boundary conditions for burden values."""

    def test_extreme_burden_values(self):
        """Test with very small and very large burden values."""
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [0.001, 0.01, 0.1, 0.5, 0.99],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        results = calculate_unadjusted_spearman(df)
        assert not pd.isna(results['correlation'].values[0])

    def test_negative_burden(self):
        """Test with negative burden values (should be filtered or handled)."""
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [-0.1, 0.0, 0.1, 0.2, 0.3],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        # Negative burdens should be handled (either filtered or cause NaN)
        results = calculate_unadjusted_spearman(df)
        # The function should handle this gracefully
        assert 'correlation' in results.columns

class TestMissingAgeScenarios:
    """Test edge cases where age is missing."""

    def test_missing_age_values(self):
        """Test with NaN age values."""
        df = pd.DataFrame({
            'age': [20, np.nan, 40, 50, 60],
            'burden': [0.1, 0.2, 0.3, 0.4, 0.5],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        # Should handle missing age gracefully
        results = calculate_unadjusted_spearman(df)
        # With missing age, correlation might be NaN or calculated on available data
        # The important thing is it doesn't crash
        assert 'correlation' in results.columns

    def test_all_missing_age(self):
        """Test when all age values are missing."""
        df = pd.DataFrame({
            'age': [np.nan, np.nan, np.nan, np.nan, np.nan],
            'burden': [0.1, 0.2, 0.3, 0.4, 0.5],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        with pytest.raises((ValueError, IndexError)):
            calculate_unadjusted_spearman(df)

    def test_mixed_missing_age_and_burden(self):
        """Test with missing values in both age and burden."""
        df = pd.DataFrame({
            'age': [20, np.nan, 40, np.nan, 60],
            'burden': [0.1, 0.2, np.nan, 0.4, 0.5],
            'depth': [10, 20, 30, 40, 50],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6],
            'sex': ['M', 'F', 'M', 'F', 'M']
        })
        
        # Should handle partial missing data
        results = calculate_unadjusted_spearman(df)
        assert 'correlation' in results.columns

class TestRankTransformationEdgeCases:
    """Test edge cases specific to rank transformation in Rank-OLS."""

    def test_tied_ranks(self):
        """Test with many tied values that create tied ranks."""
        df = pd.DataFrame({
            'age': [20, 20, 20, 50, 50, 50],
            'burden': [0.1, 0.1, 0.1, 0.5, 0.5, 0.5],
            'depth': [10, 10, 10, 30, 30, 30],
            'PC1': [0.1, 0.1, 0.1, 0.5, 0.5, 0.5],
            'PC2': [0.2, 0.2, 0.2, 0.6, 0.6, 0.6],
            'sex': ['M', 'M', 'M', 'F', 'F', 'F']
        })
        
        # Rank-OLS should handle tied ranks
        results = calculate_rank_ols(df)
        assert 'coefficient' in results.columns

    def test_constant_variables(self):
        """Test when all variables are constant."""
        df = pd.DataFrame({
            'age': [30, 30, 30, 30, 30],
            'burden': [0.1, 0.1, 0.1, 0.1, 0.1],
            'depth': [20, 20, 20, 20, 20],
            'PC1': [0.3, 0.3, 0.3, 0.3, 0.3],
            'PC2': [0.4, 0.4, 0.4, 0.4, 0.4],
            'sex': ['M', 'M', 'M', 'M', 'M']
        })
        
        # Should handle constant variables (all ranks will be tied)
        results = calculate_rank_ols(df)
        # Coefficients should be NaN or 0 due to no variance
        assert 'coefficient' in results.columns