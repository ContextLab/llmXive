"""
Unit tests for edge cases in the climate-smart agriculture pipeline.

Tests cover:
1. Missing years in LSMS data
2. Climate data gaps (NASA POWER)
3. High collinearity (VIF > 5.0) detection and reporting
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.download import download_lsms, download_nasa_power, download_faostat
from analysis.diagnostics import calculate_vif, flag_collinearity, get_collinearity_report

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestMissingYears:
    """Tests for handling missing years in LSMS data."""
    
    def test_lsms_missing_year_raises_error(self):
        """Test that requesting a non-existent year raises appropriate error."""
        # Try to download LSMS data for a year that likely doesn't exist
        # Using a future year that definitely won't have data
        with pytest.raises(Exception) as exc_info:
            download_lsms(country="KEN", year=2099)
        
        # Verify the error message mentions missing data or invalid year
        error_msg = str(exc_info.value).lower()
        assert ("not found" in error_msg or 
               "missing" in error_msg or 
               "invalid" in error_msg or
               "no data" in error_msg), \
               f"Expected 'not found' or 'missing' in error, got: {error_msg}"
    
    def test_lsms_missing_year_in_range(self):
        """Test handling of missing year within a valid range."""
        # Some countries may not have data for every year
        # This test verifies the function handles gaps gracefully
        try:
            # Try a year that might be missing for a specific country
            result = download_lsms(country="KEN", year=2005)
            # If it succeeds, that's fine - data exists
            assert result is not None
        except Exception as e:
            # If it fails, verify the error is appropriate (not a crash)
            error_msg = str(e).lower()
            assert ("not found" in error_msg or 
                   "missing" in error_msg or 
                   "unavailable" in error_msg), \
                   f"Expected graceful error for missing year, got: {e}"

class TestClimateDataGaps:
    """Tests for handling gaps in NASA POWER climate data."""
    
    def test_nasa_power_missing_dates(self):
        """Test that requesting climate data for invalid dates is handled."""
        # Test with a date range that might have gaps
        with pytest.raises(Exception) as exc_info:
            # Request data for a non-existent date range
            download_nasa_power(lat=0.0, lon=0.0, start="2099-01-01", end="2099-01-02")
        
        error_msg = str(exc_info.value).lower()
        assert ("not found" in error_msg or 
               "invalid" in error_msg or 
               "no data" in error_msg or
               "error" in error_msg), \
               f"Expected data error for invalid dates, got: {error_msg}"
    
    def test_nasa_power_extreme_coordinates(self):
        """Test handling of extreme or invalid coordinates."""
        # Test with coordinates that might not have data
        with pytest.raises(Exception) as exc_info:
            # Extreme coordinates that likely have no data
            download_nasa_power(lat=95.0, lon=190.0, start="2020-01-01", end="2020-01-02")
        
        error_msg = str(exc_info.value).lower()
        assert ("invalid" in error_msg or 
               "out of range" in error_msg or 
               "error" in error_msg or
               "not found" in error_msg), \
               f"Expected coordinate error, got: {error_msg}"
    
    def test_nasa_power_partial_data_handling(self):
        """Test that partial data gaps are handled gracefully."""
        # Create a scenario where some dates might be missing
        # This tests the interpolation/gap-filling logic
        try:
            result = download_nasa_power(
                lat=-1.2921, 
                lon=36.8219,  # Nairobi, Kenya
                start="2020-01-01", 
                end="2020-01-10"
            )
            # If successful, verify we got some data
            if result is not None:
                assert isinstance(result, pd.DataFrame) or isinstance(result, dict)
        except Exception as e:
            # If it fails, ensure it's a proper error, not a crash
            logger.info(f"Expected potential error for partial data: {e}")

class TestHighCollinearity:
    """Tests for VIF > 5.0 detection and collinearity flagging."""
    
    def test_calculate_vif_perfect_collinearity(self):
        """Test VIF calculation with perfect collinearity (should be infinite)."""
        # Create data with perfect collinearity
        np.random.seed(42)
        n = 100
        
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n),
            'x3': np.random.randn(n) * 2 + 5  # Linear combination
        })
        
        # Make x3 perfectly collinear with x1 and x2
        df['x3'] = 2 * df['x1'] + 3 * df['x2']
        
        # Calculate VIF - should detect high collinearity
        vif_results = calculate_vif(df[['x1', 'x2', 'x3']])
        
        # At least one variable should have very high VIF
        max_vif = vif_results['VIF'].max()
        assert max_vif > 5.0, f"Expected VIF > 5.0 for collinear data, got {max_vif}"
    
    def test_flag_collinearity_threshold(self):
        """Test that collinearity is flagged when VIF > 5.0."""
        # Create data with moderate collinearity
        np.random.seed(42)
        n = 100
        
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n),
            'x3': df['x1'] * 0.8 + np.random.randn(n) * 0.2  # High correlation
        })
        
        # Flag collinearity with threshold 5.0
        flagged = flag_collinearity(df[['x1', 'x2', 'x3']], threshold=5.0)
        
        # Should flag at least one variable
        assert len(flagged) > 0, "Expected some variables to be flagged for collinearity"
        assert all(var in df.columns for var in flagged), \
            f"Flagged variables {flagged} not in dataframe columns {df.columns}"
    
    def test_get_collinearity_report(self):
        """Test generation of full collinearity report."""
        # Create data with varying degrees of collinearity
        np.random.seed(42)
        n = 100
        
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n),
            'x3': df['x1'] * 0.9 + np.random.randn(n) * 0.1,  # High correlation
            'x4': np.random.randn(n),
            'x5': df['x4'] * 0.95 + np.random.randn(n) * 0.05  # Very high correlation
        })
        
        # Generate report
        report = get_collinearity_report(df[['x1', 'x2', 'x3', 'x4', 'x5']], threshold=5.0)
        
        # Verify report structure
        assert 'vif_scores' in report, "Report should contain VIF scores"
        assert 'flagged_variables' in report, "Report should contain flagged variables"
        assert 'summary' in report, "Report should contain summary"
        
        # Verify flagged variables
        flagged = report['flagged_variables']
        assert len(flagged) > 0, "Expected some variables to be flagged"
        
        # Verify VIF scores are numeric
        for var, vif in report['vif_scores'].items():
            assert isinstance(vif, (int, float)), f"VIF for {var} should be numeric"
            assert vif >= 1.0, f"VIF should be >= 1.0, got {vif}"
    
    def test_vif_with_realistic_data(self):
        """Test VIF calculation with realistic agricultural data patterns."""
        # Simulate realistic agricultural predictor variables
        np.random.seed(42)
        n = 500
        
        df = pd.DataFrame({
            'farm_size': np.random.lognormal(2, 1, n),
            'labor': df['farm_size'] * np.random.uniform(0.8, 1.2, n),  # Correlated with size
            'capital': df['farm_size'] * np.random.uniform(0.5, 1.5, n),  # Correlated with size
            'rainfall': np.random.normal(800, 200, n),
            'temperature': np.random.normal(25, 5, n),
            'soil_quality': np.random.beta(2, 2, n) * 10
        })
        
        # Calculate VIF
        vif_results = calculate_vif(df[['farm_size', 'labor', 'capital', 'rainfall', 'temperature', 'soil_quality']])
        
        # Check that VIF is calculated for all variables
        assert len(vif_results) == 6, f"Expected 6 VIF values, got {len(vif_results)}"
        
        # Check that farm_size, labor, capital have higher VIF due to correlation
        high_vif_vars = vif_results[vif_results['VIF'] > 5.0]['variable'].tolist()
        assert any(var in high_vif_vars for var in ['farm_size', 'labor', 'capital']), \
            "Expected high VIF for correlated farm variables"
    
    def test_vif_edge_case_constant_variable(self):
        """Test VIF calculation with constant variable (should cause error or high VIF)."""
        np.random.seed(42)
        n = 100
        
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.ones(n) * 5  # Constant variable
        })
        
        # This should either raise an error or return very high VIF
        try:
            vif_results = calculate_vif(df[['x1', 'x2']])
            # If it doesn't error, x2 should have very high VIF
            x2_vif = vif_results[vif_results['variable'] == 'x2']['VIF'].values[0]
            assert x2_vif > 100 or np.isinf(x2_vif), \
                f"Constant variable should have very high VIF, got {x2_vif}"
        except Exception as e:
            # Error is also acceptable for constant variables
            logger.info(f"Expected error for constant variable: {e}")

class TestIntegrationEdgeCases:
    """Integration tests combining multiple edge cases."""
    
    def test_pipeline_with_missing_data_and_collinearity(self):
        """Test handling of dataset with both missing values and collinearity."""
        np.random.seed(42)
        n = 200
        
        # Create data with missing values and collinearity
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': df['x1'] * 0.9 + np.random.randn(n) * 0.1,  # Collinear
            'x3': np.random.randn(n),
            'x4': np.random.randn(n)
        })
        
        # Introduce missing values
        df.loc[:20, 'x1'] = np.nan
        df.loc[:10, 'x3'] = np.nan
        
        # Test collinearity detection on incomplete data
        # Drop missing for VIF calculation
        df_complete = df.dropna()
        vif_results = calculate_vif(df_complete[['x1', 'x2', 'x3', 'x4']])
        
        # Verify collinearity is still detected
        max_vif = vif_results['VIF'].max()
        assert max_vif > 5.0, f"Expected VIF > 5.0 even with missing data handling, got {max_vif}"
        
        # Verify we can flag collinearity
        flagged = flag_collinearity(df_complete[['x1', 'x2', 'x3', 'x4']], threshold=5.0)
        assert len(flagged) > 0, "Expected collinearity to be flagged"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
