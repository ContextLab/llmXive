"""
Integration tests for UCI dataset loading and subsampling.
Tests the validation pipeline for User Story 3 (US3).
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Add project root to path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from validation.uci_runner import fetch_uci_concrete_dataset, subsample_stratified


class TestUCIDataLoading:
    """Integration tests for fetching and loading the UCI Concrete dataset."""

    def test_fetch_uci_concrete_dataset(self, tmp_path):
        """
        Test that the UCI Concrete dataset is fetched correctly from the real source
        and saved to the specified directory.
        """
        output_dir = tmp_path / "raw"
        output_dir.mkdir(parents=True)
        
        # Fetch the dataset
        df = fetch_uci_concrete_dataset(output_dir)
        
        # Assertions
        assert df is not None, "Dataset should not be None"
        assert isinstance(df, pd.DataFrame), "Dataset should be a pandas DataFrame"
        assert len(df) > 0, "Dataset should contain rows"
        
        # Check for expected columns (Concrete dataset typically has these)
        expected_columns = ['Cement', 'Blast Furnace Slag', 'Fly Ash', 'Water', 
                          'Superplasticizer', 'Coarse Aggregate', 'Fine Aggregate', 
                          'Age', 'Concrete compressive strength']
        
        # Verify at least the target column exists
        assert 'Concrete compressive strength' in df.columns, \
            "Target column 'Concrete compressive strength' must exist"
        
        # Verify numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        assert len(numeric_cols) >= 8, "Should have at least 8 numeric predictor columns"

    def test_cache_file_created(self, tmp_path):
        """
        Test that the dataset is saved to the expected file path.
        """
        output_dir = tmp_path / "raw"
        output_dir.mkdir(parents=True)
        
        fetch_uci_concrete_dataset(output_dir)
        
        # Check if the CSV file exists
        expected_file = output_dir / "concrete_compressive_strength.csv"
        assert expected_file.exists(), f"Expected file {expected_file} should exist"

    def test_data_integrity(self, tmp_path):
        """
        Test that the loaded data has reasonable values (no NaN in critical columns).
        """
        output_dir = tmp_path / "raw"
        output_dir.mkdir(parents=True)
        
        df = fetch_uci_concrete_dataset(output_dir)
        
        # Check for NaN in target column
        target_col = 'Concrete compressive strength'
        assert not df[target_col].isna().any(), \
            "Target column should not contain NaN values"
        
        # Check that target values are positive (compressive strength is positive)
        assert (df[target_col] > 0).all(), \
            "Compressive strength values should be positive"


class TestSubsampling:
    """Integration tests for stratified subsampling logic."""

    def test_subsample_stratified_basic(self, tmp_path):
        """
        Test basic stratified subsampling functionality.
        """
        output_dir = tmp_path / "raw"
        output_dir.mkdir(parents=True)
        
        # Fetch full dataset
        full_df = fetch_uci_concrete_dataset(output_dir)
        
        # Define target column and sample size
        target_col = 'Concrete compressive strength'
        n_samples = 40
        
        # Perform stratified subsampling
        sample_df, metadata = subsample_stratified(
            full_df, 
            target_col=target_col, 
            n_samples=n_samples,
            random_state=42
        )
        
        # Assertions
        assert sample_df is not None, "Subsampled DataFrame should not be None"
        assert isinstance(sample_df, pd.DataFrame), "Should be a DataFrame"
        assert len(sample_df) == n_samples, f"Should have exactly {n_samples} rows"
        
        # Verify metadata
        assert isinstance(metadata, dict), "Metadata should be a dictionary"
        assert 'n_samples' in metadata, "Metadata should contain 'n_samples'"
        assert metadata['n_samples'] == n_samples
        assert 'original_size' in metadata, "Metadata should contain 'original_size'"
        assert 'target_col' in metadata, "Metadata should contain 'target_col'"

    def test_subsample_constraints(self, tmp_path):
        """
        Test that subsampling respects constraints: N > p and at least 3 predictors.
        """
        output_dir = tmp_path / "raw"
        output_dir.mkdir(parents=True)
        
        full_df = fetch_uci_concrete_dataset(output_dir)
        target_col = 'Concrete compressive strength'
        
        # Get predictor columns (all except target)
        predictor_cols = [col for col in full_df.columns if col != target_col]
        p = len(predictor_cols)
        
        # Try with N=40 (should be > p if p < 40, which it is for concrete dataset)
        n_samples = 40
        
        sample_df, metadata = subsample_stratified(
            full_df, 
            target_col=target_col, 
            n_samples=n_samples,
            random_state=123
        )
        
        # Verify N > p constraint
        assert n_samples > p, f"N ({n_samples}) must be greater than p ({p})"
        
        # Verify at least 3 predictors
        assert p >= 3, f"Must have at least 3 predictors, found {p}"
        
        # Verify metadata reflects this
        assert metadata.get('n_predictors') == p
        assert metadata.get('n_greater_than_p') is True

    def test_subsample_with_low_n(self, tmp_path):
        """
        Test behavior when N is too low (N <= p).
        This should trigger a warning or skip, not crash.
        """
        output_dir = tmp_path / "raw"
        output_dir.mkdir(parents=True)
        
        full_df = fetch_uci_concrete_dataset(output_dir)
        target_col = 'Concrete compressive strength'
        
        # Get predictor count
        p = len([col for col in full_df.columns if col != target_col])
        
        # Try with N <= p (e.g., N=5 if p=8)
        n_samples = 5
        
        # This should handle the constraint violation gracefully
        # The subsample_stratified function should either:
        # 1. Raise a clear error
        # 2. Return None with metadata indicating failure
        # 3. Adjust parameters
        
        try:
            sample_df, metadata = subsample_stratified(
                full_df, 
                target_col=target_col, 
                n_samples=n_samples,
                random_state=456
            )
            
            # If it succeeds, verify constraints are met
            assert n_samples > p, "Should not succeed if N <= p"
        except ValueError as e:
            # Expected behavior: raise error when constraints cannot be met
            assert "N must be greater than p" in str(e) or \
                   "rank-deficient" in str(e).lower()

    def test_subsample_preserves_target_distribution(self, tmp_path):
        """
        Test that stratified subsampling preserves the target variable distribution
        approximately.
        """
        output_dir = tmp_path / "raw"
        output_dir.mkdir(parents=True)
        
        full_df = fetch_uci_concrete_dataset(output_dir)
        target_col = 'Concrete compressive strength'
        
        n_samples = 40
        
        sample_df, _ = subsample_stratified(
            full_df, 
            target_col=target_col, 
            n_samples=n_samples,
            random_state=789
        )
        
        # Compare mean and std (should be reasonably close for stratified sampling)
        full_mean = full_df[target_col].mean()
        sample_mean = sample_df[target_col].mean()
        
        full_std = full_df[target_col].std()
        sample_std = sample_df[target_col].std()
        
        # Allow 20% deviation for small sample sizes
        mean_deviation = abs(sample_mean - full_mean) / full_mean
        std_deviation = abs(sample_std - full_std) / full_std if full_std > 0 else 0
        
        assert mean_deviation < 0.2, \
            f"Mean deviation too large: {mean_deviation:.2%}"
        assert std_deviation < 0.3, \
            f"Std deviation too large: {std_deviation:.2%}"