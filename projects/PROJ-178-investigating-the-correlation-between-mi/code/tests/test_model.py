import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import yaml
import numpy as np
from analysis.model import calculate_unadjusted_spearman, calculate_rank_ols, apply_benjamini_hochberg

def load_schema(schema_path):
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_dataset(dataset_path):
    """Load a dataset from a CSV file."""
    return pd.read_csv(dataset_path)

class TestStatisticalOutputSchema:
    """Test that statistical outputs conform to the expected schema."""

    def test_spearman_results_schema(self):
        """Test that Spearman results have the expected columns."""
        # This test would be run after the model.py script has executed
        # For now, we test the function directly
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        
        results = calculate_unadjusted_spearman(df)
        
        assert 'method' in results.columns
        assert 'correlation' in results.columns
        assert 'p_value' in results.columns
        assert len(results) == 1

    def test_rank_ols_results_schema(self):
        """Test that Rank-OLS results have the expected columns."""
        df = pd.DataFrame({
            'age': [20, 30, 40, 50, 60, 70],
            'burden': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'depth': [10, 20, 30, 40, 50, 60],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'PC2': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
            'sex': ['M', 'F', 'M', 'F', 'M', 'F']
        })
        
        results = calculate_rank_ols(df)
        
        assert 'variable' in results.columns
        assert 'coefficient' in results.columns
        assert 'std_err' in results.columns
        assert 't_value' in results.columns
        assert 'p_value' in results.columns

    def test_bh_correction_output(self):
        """Test that BH correction returns adjusted p-values."""
        p_values = [0.01, 0.03, 0.05, 0.10, 0.20]
        adjusted = apply_benjamini_hochberg(p_values)
        
        assert len(adjusted) == len(p_values)
        assert all(0 <= p <= 1 for p in adjusted)
        # Check monotonicity
        for i in range(len(adjusted)-1):
            assert adjusted[i] <= adjusted[i+1]

class TestRankOLSImplementation:
    """Test the Rank-OLS implementation with known data."""

    def test_rank_ols_with_synthetic_data(self):
        """Test Rank-OLS with a synthetic dataset that has a known correlation."""
        # Create a dataset with a known positive correlation
        np.random.seed(42)
        n = 100
        age = np.random.normal(50, 15, n)
        burden = 0.5 * age + np.random.normal(0, 5, n)
        depth = np.random.normal(30, 10, n)
        PC1 = np.random.normal(0, 1, n)
        PC2 = np.random.normal(0, 1, n)
        sex = np.random.choice(['M', 'F'], n)
        
        df = pd.DataFrame({
            'age': age,
            'burden': burden,
            'depth': depth,
            'PC1': PC1,
            'PC2': PC2,
            'sex': sex
        })
        
        results = calculate_rank_ols(df)
        
        # Check that the burden coefficient is positive (since we created a positive correlation)
        burden_coef = results.loc[results['variable'] == 'rank_burden', 'coefficient'].values[0]
        assert burden_coef > 0, "Expected positive coefficient for rank_burden"
        
        # Check that the p-value is significant (should be low for this synthetic data)
        burden_pval = results.loc[results['variable'] == 'rank_burden', 'p_value'].values[0]
        assert burden_pval < 0.05, f"Expected significant p-value, got {burden_pval}"

    def test_rank_ols_with_negative_correlation(self):
        """Test Rank-OLS with a synthetic dataset that has a known negative correlation."""
        np.random.seed(42)
        n = 100
        age = np.random.normal(50, 15, n)
        burden = -0.5 * age + np.random.normal(0, 5, n)
        depth = np.random.normal(30, 10, n)
        PC1 = np.random.normal(0, 1, n)
        PC2 = np.random.normal(0, 1, n)
        sex = np.random.choice(['M', 'F'], n)
        
        df = pd.DataFrame({
            'age': age,
            'burden': burden,
            'depth': depth,
            'PC1': PC1,
            'PC2': PC2,
            'sex': sex
        })
        
        results = calculate_rank_ols(df)
        
        # Check that the burden coefficient is negative
        burden_coef = results.loc[results['variable'] == 'rank_burden', 'coefficient'].values[0]
        assert burden_coef < 0, "Expected negative coefficient for rank_burden"