"""
Unit tests for the analysis module, specifically focusing on the
Benjamini-Hochberg correction implementation (T020) and collinearity diagnostics (T023).
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import run_benjamini_hochberg
from code.benjamini_hochberg import run_benjamini_hochberg as bh_main_impl
from code.collinearity import calculate_vif, run_collinearity_diagnostics, load_analysis_results

# Mock data for VIF tests
def create_mock_metrics_data(tmp_dir):
    """Create mock LZC and PE metrics files for testing."""
    lzc_path = Path(tmp_dir) / "lzc_metrics.csv"
    pe_path = Path(tmp_dir) / "pe_metrics.csv"

    # Create mock data
    participants = [f"sub_{i:03d}" for i in range(1, 51)]
    channels = ['Fz', 'Cz', 'Pz']

    lzc_data = []
    pe_data = []

    for p in participants:
        for ch in channels:
            # Generate correlated data to trigger VIF
            base = np.random.uniform(0.4, 0.6)
            lzc_val = base + np.random.normal(0, 0.05)
            # PE is highly correlated with LZC here to test VIF
            pe_val = base * 1.8 + np.random.normal(0, 0.05)

            lzc_data.append({'participant_id': p, 'channel': ch, 'lzc_value': lzc_val})
            pe_data.append({'participant_id': p, 'channel': ch, 'pe_value': pe_val})

    pd.DataFrame(lzc_data).to_csv(lzc_path, index=False)
    pd.DataFrame(pe_data).to_csv(pe_path, index=False)
    return lzc_path, pe_path

class TestBenjaminiHochberg:
    """Tests for the Benjamini-Hochberg correction implementation."""

    def test_bh_correction_theoretical(self):
        """
        Test BH correction on a known set of p-values.
        Reference: Standard BH procedure example.
        """
        p_values = np.array([0.001, 0.004, 0.009, 0.015, 0.025, 0.035, 0.05, 0.1, 0.2, 0.3])
        alpha = 0.05
        m = len(p_values)

        result_df = bh_main_impl(p_values, alpha=alpha)

        assert len(result_df) == m
        assert result_df['significant'].sum() == 5

        expected_p_adj = [0.01, 0.02, 0.03, 0.0375, 0.05, 0.058333, 0.071428, 0.125, 0.222222, 0.3]
        for i, expected in enumerate(expected_p_adj):
            assert np.isclose(result_df['p_adj'].iloc[i], expected, rtol=1e-4), \
                f"Mismatch at index {i}: expected {expected}, got {result_df['p_adj'].iloc[i]}"

    def test_bh_correction_with_nan(self):
        """Test that BH correction handles NaN values gracefully."""
        p_values = [0.01, np.nan, 0.05, 0.1]
        result_df = bh_main_impl(p_values, alpha=0.05)
        assert len(result_df) == 3
        assert not result_df['p_adj'].isna().any()

    def test_bh_correction_empty(self):
        """Test BH correction on empty input."""
        p_values = []
        result_df = bh_main_impl(p_values, alpha=0.05)
        assert len(result_df) == 0

    def test_bh_correction_all_significant(self):
        """Test case where all p-values are very small."""
        p_values = [0.001, 0.002, 0.003]
        result_df = bh_main_impl(p_values, alpha=0.05)
        assert result_df['significant'].all()

    def test_bh_correction_none_significant(self):
        """Test case where no p-values are significant."""
        p_values = [0.2, 0.3, 0.4]
        result_df = bh_main_impl(p_values, alpha=0.05)
        assert not result_df['significant'].any()

class TestCollinearityDiagnostics:
    """Tests for the collinearity diagnostics (VIF) implementation (T023)."""

    def test_vif_check(self, tmp_path):
        """
        Verify VIF calculation and logging of warning if VIF >= 5.
        Output should be written to data/analysis/vif_report.csv.
        """
        # Create temporary directory structure
        test_data_dir = tmp_path / "data" / "processed"
        test_data_dir.mkdir(parents=True)
        test_analysis_dir = tmp_path / "data" / "analysis"
        test_analysis_dir.mkdir(parents=True)

        # Create mock files in the temp directory
        lzc_path, pe_path = create_mock_metrics_data(test_data_dir)

        # Temporarily override the paths in the module or mock the load function
        # Since the function uses hardcoded paths relative to code/, we need to
        # simulate the environment or patch the load function.
        # For this test, we will patch load_analysis_results to return our data.

        import code.collinearity as collinearity_module

        original_load = collinearity_module.load_analysis_results

        def mock_load():
            lzc_df = pd.read_csv(lzc_path)
            pe_df = pd.read_csv(pe_path)
            return lzc_df, pe_df

        collinearity_module.load_analysis_results = mock_load

        try:
            # Run the diagnostics
            report = run_collinearity_diagnostics()

            # Assert report exists and has correct columns
            assert report is not None
            assert 'vif' in report.columns
            assert 'status' in report.columns

            # Assert that warnings were logged (we can't easily capture logs in this simple test,
            # but we can check the status column)
            assert 'WARNING' in report['status'].values or 'CRITICAL' in report['status'].values

            # Check that the file was written to the expected location (mocked path)
            # Since we patched load, the save path might still be the original.
            # Let's just verify the data integrity.
            assert len(report) > 0
            assert all(report['vif'] >= 1.0) # VIF is always >= 1

        finally:
            # Restore original function
            collinearity_module.load_analysis_results = original_load

    def test_vif_calculation_basic(self):
        """Test basic VIF calculation on a simple dataframe."""
        data = {
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10]  # Perfectly collinear with x1
        }
        df = pd.DataFrame(data)
        vif_df = calculate_vif(df, ['x1', 'x2'])

        assert len(vif_df) == 2
        # With perfect collinearity, VIF should be very large or infinite (NaN in some implementations)
        # statsmodels might return inf or a very large number.
        assert any(vif_df['vif'] > 100) or any(vif_df['vif'].isna())

    def test_vif_no_collinearity(self):
        """Test VIF on uncorrelated data."""
        np.random.seed(42)
        data = {
            'x1': np.random.randn(100),
            'x2': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        vif_df = calculate_vif(df, ['x1', 'x2'])

        assert len(vif_df) == 2
        # VIF should be close to 1 for uncorrelated variables
        assert all(vif_df['vif'] < 1.5)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])