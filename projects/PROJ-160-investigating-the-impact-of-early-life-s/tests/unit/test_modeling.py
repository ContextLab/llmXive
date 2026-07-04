import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.modeling import calculate_ca3_dg_ratio, fit_ca3_dg_ratio_model

class TestCA3DGRatio:
    """Unit tests for CA3:DG ratio calculation and modeling."""

    @pytest.fixture
    def sample_df(self):
        """Create a minimal valid DataFrame for testing."""
        data = {
            'CA3': [2.5, 3.0, 2.8, 3.2, 2.9],
            'DG': [1.5, 1.6, 1.4, 1.7, 1.5],
            'ACE_score': [10, 20, 15, 25, 30],
            'age': [12, 13, 12, 14, 13],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'scanner_site': ['A', 'B', 'A', 'B', 'A'],
            'family_id': [1, 1, 2, 2, 3]
        }
        return pd.DataFrame(data)

    def test_ratio_calculation(self, sample_df):
        """Test that CA3:DG ratio is calculated correctly."""
        result_df = calculate_ca3_dg_ratio(sample_df)
        
        assert 'CA3_DG_Ratio' in result_df.columns
        
        # Check first row: 2.5 / 1.5 = 1.666...
        expected_ratio = sample_df.iloc[0]['CA3'] / sample_df.iloc[0]['DG']
        assert np.isclose(result_df.iloc[0]['CA3_DG_Ratio'], expected_ratio)

    def test_ratio_handles_zero_dg(self):
        """Test that division by zero in DG is handled (becomes NaN)."""
        data = {
            'CA3': [2.5, 3.0],
            'DG': [1.5, 0.0],
            'ACE_score': [10, 20],
            'age': [12, 13],
            'sex': ['M', 'F'],
            'scanner_site': ['A', 'B'],
            'family_id': [1, 2]
        }
        df = pd.DataFrame(data)
        result_df = calculate_ca3_dg_ratio(df)
        
        assert pd.isna(result_df.iloc[1]['CA3_DG_Ratio'])

    def test_missing_columns_raises_error(self):
        """Test that missing CA3 or DG columns raises ValueError."""
        df = pd.DataFrame({'ACE_score': [10]})
        
        with pytest.raises(ValueError):
            calculate_ca3_dg_ratio(df)

    def test_model_fitting(self, sample_df):
        """Test that the LMM model fits successfully."""
        # Increase sample size for more robust fitting if needed, 
        # but for unit test logic check, we just ensure it runs.
        # The fixture has 5 rows, which might be small for mixedlm convergence.
        # Let's expand it slightly to ensure stability for the test.
        expanded_data = pd.concat([sample_df] * 10, ignore_index=True)
        
        try:
            results = fit_ca3_dg_ratio_model(expanded_data)
            
            assert 'model' in results
            assert 'params' in results
            assert 'ACE_score' in results['params']
            assert results['n_obs'] > 0
            assert results['n_groups'] > 0
            
            # Check that coefficient is a float
            assert isinstance(results['params']['ACE_score']['coef'], (float, np.floating))
            
        except Exception as e:
            # If fitting fails due to data size/structure, it's a test setup issue,
            # but the function logic is correct. However, we expect it to work.
            pytest.fail(f"Model fitting failed: {e}")

    def test_model_missing_columns_raises_error(self):
        """Test that missing columns in model fitting raises ValueError."""
        df = pd.DataFrame({'CA3_DG_Ratio': [1.0], 'ACE_score': [10]})
        
        with pytest.raises(ValueError):
            fit_ca3_dg_ratio_model(df)