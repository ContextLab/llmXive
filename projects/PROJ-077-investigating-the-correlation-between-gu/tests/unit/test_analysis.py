"""
Tests for the analysis module (T022a).
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path for imports if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis import compute_spearman_correlation, save_correlation_results, check_zero_variance

class TestSpearmanCorrelation:
    """Tests for T022a: Spearman correlation implementation."""

    def test_compute_spearman_correlation_basic(self, tmp_path):
        """Test basic Spearman correlation calculation."""
        # Create a simple dataset with known correlation
        data = {
            'shannon_index': [1.0, 2.0, 3.0, 4.0, 5.0],
            'fluid_intelligence_score': [10.0, 20.0, 30.0, 40.0, 50.0]
        }
        df = pd.DataFrame(data)
        
        r, p, n = compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence_score')
        
        # Perfect positive correlation
        assert r == 1.0
        assert p < 0.05  # Significant
        assert n == 5

    def test_compute_spearman_correlation_negative(self):
        """Test negative correlation."""
        data = {
            'shannon_index': [1.0, 2.0, 3.0, 4.0, 5.0],
            'fluid_intelligence_score': [50.0, 40.0, 30.0, 20.0, 10.0]
        }
        df = pd.DataFrame(data)
        
        r, p, n = compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence_score')
        
        # Perfect negative correlation
        assert r == -1.0
        assert p < 0.05
        assert n == 5

    def test_compute_spearman_correlation_no_correlation(self):
        """Test zero correlation."""
        data = {
            'shannon_index': [1.0, 2.0, 3.0, 4.0, 5.0],
            'fluid_intelligence_score': [5.0, 1.0, 4.0, 2.0, 3.0]
        }
        df = pd.DataFrame(data)
        
        r, p, n = compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence_score')
        
        # Low correlation (not exactly 0 due to small sample, but low)
        assert abs(r) < 0.5
        assert n == 5

    def test_compute_spearman_correlation_with_nulls(self):
        """Test handling of null values."""
        data = {
            'shannon_index': [1.0, 2.0, np.nan, 4.0, 5.0],
            'fluid_intelligence_score': [10.0, 20.0, 30.0, np.nan, 50.0]
        }
        df = pd.DataFrame(data)
        
        r, p, n = compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence_score')
        
        # Should only use valid pairs (1,10), (2,20), (5,50) -> 3 points
        assert n == 3
        assert r == 1.0  # Perfect correlation on remaining points

    def test_compute_spearman_correlation_insufficient_data(self):
        """Test error on insufficient data."""
        data = {
            'shannon_index': [1.0],
            'fluid_intelligence_score': [10.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError):
            compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence_score')

    def test_save_correlation_results(self, tmp_path):
        """Test saving correlation results to CSV."""
        # Mock the OUTPUT_DIR
        import code.analysis as analysis_module
        original_path = analysis_module.OUTPUT_DIR
        analysis_module.OUTPUT_DIR = tmp_path
        
        try:
            save_correlation_results(0.5, 0.01, 100)
            
            output_file = tmp_path / "correlation_results.csv"
            assert output_file.exists()
            
            df = pd.read_csv(output_file)
            assert 'r_value' in df.columns
            assert 'p_value' in df.columns
            assert 'n_obs' in df.columns
            assert len(df) == 1
            assert df['r_value'].iloc[0] == 0.5
            assert df['p_value'].iloc[0] == 0.01
            assert df['n_obs'].iloc[0] == 100
        finally:
            analysis_module.OUTPUT_DIR = original_path

class TestZeroVariance:
    """Tests for zero variance detection."""

    def test_check_zero_variance(self):
        """Test detection of zero variance columns."""
        data = {
            'varied': [1.0, 2.0, 3.0],
            'constant': [5.0, 5.0, 5.0],
            'another_varied': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        zero_cols = check_zero_variance(df, ['varied', 'constant', 'another_varied'])
        
        assert 'constant' in zero_cols
        assert 'varied' not in zero_cols
        assert 'another_varied' not in zero_cols
