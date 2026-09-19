import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.preprocessing import residualize_data, extract_alloy_series

class TestResidualization:
    
    def test_residualize_basic(self):
        """Test that residualization creates the residuals column."""
        # Create mock data
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'Grain_Size': np.random.randn(n) * 10 + 50,
            'Mg': np.random.rand(n) * 5,
            'Si': np.random.rand(n) * 2,
            'Alloy_Series': np.random.choice(['A', 'B', 'C'], n)
        })
        
        result_df = residualize_data(df, target_col='Grain_Size')
        
        assert 'Grain_Size_Residuals' in result_df.columns
        assert len(result_df) == n
        
        # Check that residuals are roughly centered (mean ~ 0)
        mean_res = result_df['Grain_Size_Residuals'].mean()
        assert abs(mean_res) < 1.0, f"Residuals mean {mean_res} is too far from 0"

    def test_residualize_uncorrelated_with_series(self):
        """Test that residuals are uncorrelated with the Alloy Series."""
        np.random.seed(42)
        n = 200
        # Create data where Grain Size depends heavily on Alloy Series
        series_map = {'A': 0, 'B': 20, 'C': 40}
        df = pd.DataFrame({
            'Grain_Size': [series_map[s] + np.random.randn() for s in np.random.choice(['A', 'B', 'C'], n)],
            'Mg': np.random.rand(n),
            'Alloy_Series': np.random.choice(['A', 'B', 'C'], n)
        })
        
        result_df = residualize_data(df, target_col='Grain_Size')
        
        # Check mean per group
        group_means = result_df.groupby('Alloy_Series')['Grain_Size_Residuals'].mean()
        
        # If the model worked, the means should be close to 0
        # Allow some tolerance due to random noise
        assert all(abs(m) < 2.0 for m in group_means), f"Group means not zero: {group_means}"

    def test_extract_alloy_series(self):
        """Test extraction of alloy series column."""
        df = pd.DataFrame({
            'Grain_Size': [1, 2, 3],
            'Alloy_Series': ['X', 'Y', 'Z']
        })
        
        groups = extract_alloy_series(df)
        
        assert isinstance(groups, np.ndarray)
        assert len(groups) == 3
        assert list(groups) == ['X', 'Y', 'Z']

    def test_extract_alloy_series_missing(self):
        """Test extraction when column is missing (fallback)."""
        df = pd.DataFrame({
            'Grain_Size': [1, 2, 3],
            'Other': ['a', 'b', 'c']
        })
        
        groups = extract_alloy_series(df)
        
        # Should fallback to all zeros
        assert isinstance(groups, np.ndarray)
        assert all(g == 0 for g in groups)
