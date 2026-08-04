import pytest
import pandas as pd
import numpy as np
from code.analysis import calculate_correlations, apply_fdr_correction

class TestCalculateCorrelations:
    def test_correlation_calculation(self):
        """Test that correlations are calculated correctly."""
        # Create sample data
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'shannon': np.random.rand(n) * 4,
            'sleep_duration': np.random.rand(n) * 10,
            'age': np.random.randint(20, 60, n),
            'bmi': np.random.rand(n) * 10 + 15
        })
        
        # Calculate correlations
        correlations = calculate_correlations(df, 'shannon', ['sleep_duration', 'age', 'bmi'])
        
        # Check structure
        assert 'correlation' in correlations.index
        assert 'p_value' in correlations.index
        
        # Check that we have correlations for all variables
        assert 'sleep_duration' in correlations['correlation']
        assert 'age' in correlations['correlation']
        assert 'bmi' in correlations['correlation']

    def test_correlation_significance(self):
        """Test that significant correlations are identified correctly."""
        # Create data with known correlation
        np.random.seed(42)
        n = 200
        x = np.random.rand(n)
        y = x * 2 + np.random.normal(0, 0.1, n)  # Strong positive correlation
        
        df = pd.DataFrame({
            'var1': x,
            'var2': y
        })
        
        correlations = calculate_correlations(df, 'var1', ['var2'])
        
        # Check that correlation is positive and significant
        assert correlations['correlation']['var2'] > 0.5
        assert correlations['p_value']['var2'] < 0.05

class TestApplyFdrCorrection:
    def test_fdr_correction(self):
        """Test that FDR correction is applied correctly."""
        # Create sample p-values
        p_values = pd.Series([0.01, 0.03, 0.05, 0.1, 0.2, 0.5, 0.8])
        
        # Apply FDR correction
        corrected = apply_fdr_correction(p_values)
        
        # Check that corrected p-values are monotonic
        assert all(corrected.diff().dropna() >= 0)
        
        # Check that corrected p-values are >= original p-values
        assert all(corrected >= p_values)
        
        # Check that corrected p-values are <= 1
        assert all(corrected <= 1)

    def test_fdr_correction_single_value(self):
        """Test FDR correction with a single p-value."""
        p_values = pd.Series([0.05])
        corrected = apply_fdr_correction(p_values)
        
        # For a single value, corrected should equal original
        assert corrected.iloc[0] == p_values.iloc[0]

    def test_fdr_correction_all_zeros(self):
        """Test FDR correction with all zero p-values."""
        p_values = pd.Series([0.0, 0.0, 0.0])
        corrected = apply_fdr_correction(p_values)
        
        # All should remain zero
        assert all(corrected == 0)

    def test_fdr_correction_all_ones(self):
        """Test FDR correction with all one p-values."""
        p_values = pd.Series([1.0, 1.0, 1.0])
        corrected = apply_fdr_correction(p_values)
        
        # All should remain one
        assert all(corrected == 1)