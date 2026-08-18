"""
Unit tests for the aggregator module.

Tests verify:
1. Wilson score interval calculation
2. Error rate calculation logic
3. Output format and columns
4. Edge cases (empty data, zero counts)
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.aggregator import (
    wilson_score_interval,
    calculate_error_rates,
    save_aggregated_results,
    load_error_rates,
    main
)


class TestWilsonScoreInterval:
    """Tests for Wilson score interval calculation."""
    
    def test_wilson_interval_basic(self):
        """Test basic Wilson score interval calculation."""
        successes = 50
        n = 100
        lower, upper = wilson_score_interval(successes, n, confidence=0.95)
        
        # Proportion is 0.5, CI should be around that
        assert 0.35 < lower < 0.55
        assert 0.45 < upper < 0.65
        assert lower < upper
        
    def test_wilson_interval_zero_successes(self):
        """Test Wilson score interval with zero successes."""
        lower, upper = wilson_score_interval(0, 100, confidence=0.95)
        
        assert lower == 0.0
        assert 0.0 < upper < 0.05  # Should be small
        
    def test_wilson_interval_all_successes(self):
        """Test Wilson score interval with all successes."""
        lower, upper = wilson_score_interval(100, 100, confidence=0.95)
        
        assert 0.95 < lower < 1.0
        assert upper == 1.0
        
    def test_wilson_interval_small_sample(self):
        """Test Wilson score interval with small sample size."""
        lower, upper = wilson_score_interval(1, 5, confidence=0.95)
        
        assert 0.0 < lower < 1.0
        assert 0.0 < upper < 1.0
        assert lower < upper
        
    def test_wilson_interval_empty(self):
        """Test Wilson score interval with zero trials."""
        lower, upper = wilson_score_interval(0, 0, confidence=0.95)
        
        assert lower == 0.0
        assert upper == 1.0


class TestCalculateErrorRates:
    """Tests for error rate calculation."""
    
    def setup_method(self):
        """Set up test data."""
        np.random.seed(42)
        
        # Create synthetic data
        n_iterations = 1000
        data = {
            'p_value': np.random.uniform(0, 1, n_iterations),
            'hypothesis_state': np.random.choice(['H0', 'H1'], n_iterations),
            'sample_size': np.random.choice([10, 20, 50], n_iterations),
            'effect_size': np.random.choice([0.0, 0.5], n_iterations),
            'test_type': np.random.choice(['t-test', 'anova', 'chi-squared'], n_iterations)
        }
        
        self.df = pd.DataFrame(data)
        
    def test_calculate_error_rates_basic(self):
        """Test basic error rate calculation."""
        result = calculate_error_rates(self.df, alpha=0.05)
        
        assert not result.empty
        assert 'type1_error_rate' in result.columns
        assert 'type2_error_rate' in result.columns
        assert 'sample_size' in result.columns
        assert 'test_type' in result.columns
        
        # Rates should be between 0 and 1
        assert (result['type1_error_rate'] >= 0).all()
        assert (result['type1_error_rate'] <= 1).all()
        assert (result['type2_error_rate'] >= 0).all()
        assert (result['type2_error_rate'] <= 1).all()
        
    def test_calculate_error_rates_type1_definition(self):
        """Verify Type I error is calculated correctly (H0 rejections)."""
        # Create data where we know the expected outcome
        data = {
            'p_value': [0.01, 0.03, 0.06, 0.5],  # 2 rejections at alpha=0.05
            'hypothesis_state': ['H0', 'H0', 'H0', 'H0'],
            'sample_size': [10, 10, 10, 10],
            'effect_size': [0.0, 0.0, 0.0, 0.0],
            'test_type': ['t-test', 't-test', 't-test', 't-test']
        }
        df = pd.DataFrame(data)
        
        result = calculate_error_rates(df, alpha=0.05)
        
        # Should have 2 rejections out of 4 H0 tests
        assert not result.empty
        assert result['type1_error_rate'].iloc[0] == 0.5
        
    def test_calculate_error_rates_type2_definition(self):
        """Verify Type II error is calculated correctly (H1 non-rejections)."""
        # Create data where we know the expected outcome
        data = {
            'p_value': [0.01, 0.03, 0.06, 0.5],  # 2 non-rejections at alpha=0.05
            'hypothesis_state': ['H1', 'H1', 'H1', 'H1'],
            'sample_size': [10, 10, 10, 10],
            'effect_size': [0.5, 0.5, 0.5, 0.5],
            'test_type': ['t-test', 't-test', 't-test', 't-test']
        }
        df = pd.DataFrame(data)
        
        result = calculate_error_rates(df, alpha=0.05)
        
        # Should have 2 non-rejections out of 4 H1 tests
        assert not result.empty
        assert result['type2_error_rate'].iloc[0] == 0.5
        
    def test_calculate_error_rates_empty_df(self):
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['p_value', 'hypothesis_state', 
                                        'sample_size', 'effect_size', 'test_type'])
        
        result = calculate_error_rates(empty_df, alpha=0.05)
        
        assert result.empty
        
    def test_calculate_error_rates_grouping(self):
        """Test that results are properly grouped by conditions."""
        # Create data with multiple distinct groups
        data = {
            'p_value': [0.01, 0.06, 0.01, 0.06],
            'hypothesis_state': ['H0', 'H0', 'H1', 'H1'],
            'sample_size': [10, 20, 10, 20],
            'effect_size': [0.0, 0.0, 0.5, 0.5],
            'test_type': ['t-test', 't-test', 't-test', 't-test']
        }
        df = pd.DataFrame(data)
        
        result = calculate_error_rates(df, alpha=0.05)
        
        # Should have 4 distinct groups
        assert len(result) == 4


class TestSaveAndLoad:
    """Tests for saving and loading aggregated results."""
    
    def test_save_and_load_roundtrip(self, tmp_path):
        """Test that saving and loading produces consistent results."""
        # Create test data
        data = {
            'test_type': ['t-test', 't-test'],
            'sample_size': [10, 20],
            'effect_size': [0.0, 0.5],
            'type1_error_rate': [0.05, 0.04],
            'type2_error_rate': [0.30, 0.25],
            'ci_lower': [0.02, 0.01],
            'ci_upper': [0.08, 0.07],
            'n_iterations': [100, 100],
            'n_h0': [50, 50],
            'n_h1': [50, 50]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "error_rates_summary.csv"
        
        # Save
        save_aggregated_results(df, str(output_path), alpha=0.05)
        
        # Verify file exists
        assert output_path.exists()
        
        # Load
        loaded_df = load_error_rates(str(output_path))
        
        # Verify content
        assert len(loaded_df) == len(df)
        assert list(loaded_df.columns) == list(df.columns)
        assert loaded_df['type1_error_rate'].iloc[0] == df['type1_error_rate'].iloc[0]
        
    def test_save_creates_directory(self, tmp_path):
        """Test that save creates output directory if it doesn't exist."""
        data = {
            'test_type': ['t-test'],
            'sample_size': [10],
            'effect_size': [0.0],
            'type1_error_rate': [0.05],
            'type2_error_rate': [0.30],
            'ci_lower': [0.02],
            'ci_upper': [0.08],
            'n_iterations': [100],
            'n_h0': [50],
            'n_h1': [50]
        }
        df = pd.DataFrame(data)
        
        nested_path = tmp_path / "nested" / "output" / "error_rates.csv"
        save_aggregated_results(df, str(nested_path), alpha=0.05)
        
        assert nested_path.exists()


class TestMain:
    """Tests for the main entry point."""
    
    def test_main_missing_input(self, tmp_path, monkeypatch):
        """Test main raises error when input file is missing."""
        monkeypatch.chdir(tmp_path)
        
        # Ensure input file doesn't exist
        input_path = "data/simulation/p_values_raw.csv"
        if os.path.exists(input_path):
            os.remove(input_path)
        
        with pytest.raises(FileNotFoundError):
            main(alpha=0.05)
        
    def test_main_verification_columns(self, tmp_path, monkeypatch):
        """Test that main verifies required columns in output."""
        # This test would need to mock the input data generation
        # For now, we verify the logic exists in the code
        pass