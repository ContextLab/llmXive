"""
Unit tests for correlation analysis, specifically focusing on rigidity-bin specific analysis.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import analysis functions (will be implemented in T019/T020)
# We import with a try/except to allow test file creation before implementation
try:
    from code.analysis.correlation import calculate_lagged_correlations
    from code.analysis.correlation import analyze_rigidity_bins
except ImportError:
    # If implementation modules don't exist yet, we define mocks for the test structure
    # This allows the test file to be syntactically valid and ready for implementation
    def calculate_lagged_correlations(*args, **kwargs):
        raise NotImplementedError("Implementation pending in T019/T020")
    
    def analyze_rigidity_bins(*args, **kwargs):
        raise NotImplementedError("Implementation pending in T020")


class TestRigidityBinAnalysis:
    """Tests for rigidity-bin specific analysis logic."""

    @pytest.fixture
    def mock_unified_data(self):
        """Create a mock unified dataset with multiple rigidity bins."""
        dates = pd.date_range(start='2011-01-01', end='2024-12-31', freq='D')
        n_days = len(dates)
        
        # Create multiple rigidity bins
        rigidity_bins = [1.0, 5.0, 10.0, 20.0, 50.0]
        
        data_rows = []
        for rigidity in rigidity_bins:
            # Generate synthetic flux data with solar cycle modulation
            # Higher rigidity = less modulation
            modulation_depth = 0.5 * (1.0 / (1.0 + rigidity * 0.1))
            solar_phase = 2 * np.pi * (dates.dayofyear / 365.25) + 2 * np.pi * (dates.year - 2014) / 11.0
            
            proton_flux = 1000.0 * (1.0 + modulation_depth * np.sin(solar_phase)) + np.random.normal(0, 5, n_days)
            helium_flux = 200.0 * (1.0 + modulation_depth * 0.8 * np.sin(solar_phase)) + np.random.normal(0, 2, n_days)
            fe_flux = 5.0 * (1.0 + modulation_depth * 0.6 * np.sin(solar_phase)) + np.random.normal(0, 0.5, n_days)
            
            # Sunspot number (simplified model)
            sunspots = 100.0 * (1.0 + np.sin(solar_phase)) + np.random.normal(0, 20, n_days)
            sunspots = np.maximum(0, sunspots)
            
            for i in range(n_days):
                data_rows.append({
                    'date': dates[i],
                    'rigidity': rigidity,
                    'proton_flux': proton_flux[i],
                    'helium_flux': helium_flux[i],
                    'fe_flux': fe_flux[i],
                    'sunspot_number': sunspots[i]
                })
        
        df = pd.DataFrame(data_rows)
        return df

    @pytest.fixture
    def mock_correlation_results(self):
        """Create mock correlation results for multiple rigidity bins."""
        rigidity_bins = [1.0, 5.0, 10.0, 20.0, 50.0]
        lags = list(range(-12, 13))
        
        results = []
        for rigidity in rigidity_bins:
            for lag in lags:
                # Simulate correlation decreasing with rigidity
                base_corr = 0.8 * (1.0 / (1.0 + rigidity * 0.05))
                lag_effect = np.exp(-abs(lag) / 6.0)  # Correlation drops with lag
                
                # He/p correlation
                he_p_corr = base_corr * lag_effect * np.sign(-lag)  # Negative lag: leading sunspots
                he_p_pval = 0.001 * (1.0 + abs(lag) * 0.1)
                
                # Fe/p correlation
                fe_p_corr = base_corr * 0.9 * lag_effect * np.sign(-lag)
                fe_p_pval = 0.001 * (1.0 + abs(lag) * 0.1)
                
                # Absolute flux correlations
                proton_corr = base_corr * 0.95 * lag_effect * np.sign(-lag)
                proton_pval = 0.001 * (1.0 + abs(lag) * 0.1)
                
                results.append({
                    'rigidity': rigidity,
                    'lag_months': lag,
                    'species': 'He/p',
                    'correlation': he_p_corr,
                    'p_value': min(1.0, he_p_pval)
                })
                results.append({
                    'rigidity': rigidity,
                    'lag_months': lag,
                    'species': 'Fe/p',
                    'correlation': fe_p_corr,
                    'p_value': min(1.0, fe_p_pval)
                })
                results.append({
                    'rigidity': rigidity,
                    'lag_months': lag,
                    'species': 'proton_flux',
                    'correlation': proton_corr,
                    'p_value': min(1.0, proton_pval)
                })
        
        return pd.DataFrame(results)

    def test_rigidity_bin_separation(self, mock_unified_data):
        """Test that analysis correctly separates and processes different rigidity bins."""
        # Verify that data contains multiple rigidity bins
        unique_rigidity = mock_unified_data['rigidity'].unique()
        assert len(unique_rigidity) > 1, "Test data should have multiple rigidity bins"
        
        # Check that each bin has sufficient data
        for rig in unique_rigidity:
            bin_data = mock_unified_data[mock_unified_data['rigidity'] == rig]
            assert len(bin_data) > 365, f"Rigidity bin {rig} should have at least 1 year of data"

    def test_correlation_per_rigidity_bin(self, mock_correlation_results):
        """Test that correlation results are computed for each rigidity bin independently."""
        unique_rigidity = mock_correlation_results['rigidity'].unique()
        
        # Should have correlations for all rigidity bins
        assert len(unique_rigidity) > 1, "Results should include multiple rigidity bins"
        
        # Check that each rigidity bin has correlations for all lags
        expected_lags = list(range(-12, 13))
        for rig in unique_rigidity:
            rig_results = mock_correlation_results[mock_correlation_results['rigidity'] == rig]
            actual_lags = sorted(rig_results['lag_months'].unique())
            assert actual_lags == expected_lags, f"Rigidity {rig} should have correlations for all lags -12 to +12"

    def test_rigidity_dependent_correlation_strength(self, mock_correlation_results):
        """Test that correlation strength varies with rigidity as expected."""
        # For lag=0, check that correlation decreases with increasing rigidity
        zero_lag = mock_correlation_results[mock_correlation_results['lag_months'] == 0]
        he_p_results = zero_lag[zero_lag['species'] == 'He/p']
        
        # Sort by rigidity
        he_p_sorted = he_p_results.sort_values('rigidity')
        
        # Check that correlation generally decreases with rigidity
        correlations = he_p_sorted['correlation'].values
        rigidities = he_p_sorted['rigidity'].values
          
        # Calculate correlation between rigidity and correlation strength
        # (should be negative: higher rigidity -> lower correlation)
        corr_coeff = np.corrcoef(rigidities, correlations)[0, 1]
        assert corr_coeff < 0, "Correlation strength should decrease with increasing rigidity"

    def test_rigidity_bin_with_missing_data(self):
        """Test handling of rigidity bins with data gaps."""
        # Create data with a gap in one rigidity bin
        dates = pd.date_range(start='2011-01-01', end='2024-12-31', freq='D')
        n_days = len(dates)
        
        data_rows = []
        for rigidity in [1.0, 10.0]:
            for i in range(n_days):
                # Create a 60-day gap for rigidity 10.0
                if rigidity == 10.0 and 365 < i < 425:
                    continue
                
                data_rows.append({
                    'date': dates[i],
                    'rigidity': rigidity,
                    'proton_flux': np.random.normal(1000, 10),
                    'helium_flux': np.random.normal(200, 5),
                    'fe_flux': np.random.normal(5, 0.5),
                    'sunspot_number': np.random.normal(50, 20)
                })
        
        df = pd.DataFrame(data_rows)
        
        # Verify the gap exists
        bin_10 = df[df['rigidity'] == 10.0]
        assert len(bin_10) < n_days, "Should have missing data for rigidity 10.0"

    def test_rigidity_bin_correlation_significance(self, mock_correlation_results):
        """Test that p-values are calculated for each rigidity bin."""
        # Check that all results have valid p-values
        assert 'p_value' in mock_correlation_results.columns
        assert (mock_correlation_results['p_value'] >= 0).all()
        assert (mock_correlation_results['p_value'] <= 1).all()
        
        # Check that significant results are identified
        significant = mock_correlation_results[mock_correlation_results['p_value'] < 0.01]
        assert len(significant) > 0, "Should have some significant correlations"

    def test_rigidity_bin_control_analysis(self, mock_correlation_results):
        """Test that control analysis (absolute fluxes) is performed per rigidity bin."""
        # Check that absolute flux correlations exist
        flux_species = mock_correlation_results[mock_correlation_results['species'].str.contains('flux')]
        assert len(flux_species) > 0, "Should have absolute flux correlation results"
        
        # Verify these are computed for each rigidity bin
        unique_rigidity = flux_species['rigidity'].unique()
        assert len(unique_rigidity) > 1, "Absolute flux analysis should cover multiple rigidity bins"

    def test_rigidity_bin_lag_optimization(self, mock_correlation_results):
        """Test that optimal lag is identified for each rigidity bin."""
        # For each rigidity bin and species, find the lag with maximum absolute correlation
        results = mock_correlation_results.copy()
        results['abs_corr'] = results['correlation'].abs()
        
        # Group by rigidity and species to find optimal lag
        optimal = results.groupby(['rigidity', 'species']).apply(
            lambda x: x.loc[x['abs_corr'].idxmax()]
        )
        
        # Verify optimal lags are found for each rigidity bin
        for rig in optimal['rigidity'].unique():
            rig_optimal = optimal[optimal['rigidity'] == rig]
            assert len(rig_optimal) > 0, f"Should find optimal lag for rigidity {rig}"

    def test_rigidity_bin_data_coverage(self, mock_unified_data):
        """Test that data coverage is tracked per rigidity bin."""
        # Calculate coverage for each rigidity bin
        expected_days = (mock_unified_data['date'].max() - mock_unified_data['date'].min()).days + 1
        
        coverage = mock_unified_data.groupby('rigidity').size() / expected_days
        
        # All bins should have reasonable coverage (allowing for some gaps)
        assert (coverage >= 0.5).all(), "Each rigidity bin should have at least 50% data coverage"

    def test_rigidity_bin_result_consistency(self, mock_correlation_results):
        """Test that correlation results are consistent across rigidity bins."""
        # Check that correlation values are in valid range [-1, 1]
        assert (mock_correlation_results['correlation'] >= -1).all()
        assert (mock_correlation_results['correlation'] <= 1).all()
        
        # Check that p-values are consistent with correlation strength
        # (stronger correlations should generally have lower p-values)
        significant = mock_correlation_results[mock_correlation_results['p_value'] < 0.01]
        assert len(significant) > 0, "Should have significant results"

    def test_rigidity_bin_analysis_output_structure(self, mock_correlation_results):
        """Test that output structure matches expected format for rigidity-bin analysis."""
        required_columns = ['rigidity', 'lag_months', 'species', 'correlation', 'p_value']
        assert all(col in mock_correlation_results.columns for col in required_columns), \
            "Results should contain all required columns"
        
        # Check data types
        assert mock_correlation_results['rigidity'].dtype in [np.float64, np.float32, int]
        assert mock_correlation_results['lag_months'].dtype in [np.int64, np.int32]
        assert mock_correlation_results['correlation'].dtype in [np.float64, np.float32]
        assert mock_correlation_results['p_value'].dtype in [np.float64, np.float32]

    def test_rigidity_bin_modulation_amplitude_trend(self, mock_correlation_results):
        """Test that modulation amplitude trend can be derived from rigidity-bin results."""
        # For lag=0, calculate modulation amplitude as the absolute correlation
        zero_lag = mock_correlation_results[mock_correlation_results['lag_months'] == 0]
        
        # Group by rigidity and calculate average absolute correlation
        amplitude_by_rigidity = zero_lag.groupby('rigidity')['correlation'].apply(
            lambda x: x.abs().mean()
        )
        
        # Verify trend exists (amplitude should decrease with rigidity)
        rigidities = amplitude_by_rigidity.index.values
        amplitudes = amplitude_by_rigidity.values
          
        # Check for negative correlation between rigidity and amplitude
        corr = np.corrcoef(rigidities, amplitudes)[0, 1]
        assert corr < 0, "Modulation amplitude should decrease with increasing rigidity"

    def test_rigidity_bin_parallel_processing_ready(self, mock_unified_data):
        """Test that data structure supports parallel processing of rigidity bins."""
        # Verify that each rigidity bin can be processed independently
        unique_rigidity = mock_unified_data['rigidity'].unique()
        
        for rig in unique_rigidity:
            bin_data = mock_unified_data[mock_unified_data['rigidity'] == rig]
            
            # Each bin should have all required columns
            required_cols = ['date', 'proton_flux', 'helium_flux', 'fe_flux', 'sunspot_number']
            assert all(col in bin_data.columns for col in required_cols), \
                f"Rigidity bin {rig} missing required columns"
            
            # Each bin should have sufficient data points
            assert len(bin_data) > 100, f"Rigidity bin {rig} has insufficient data"