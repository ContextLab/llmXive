import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.aggregator import calculate_error_rates, save_aggregated_results

class TestCalculateErrorRates:
    def test_type_i_error_rate_calculation(self):
        """Test Type I error rate calculation when H0 is true"""
        # Create mock data: H0 true, alpha=0.05
        # If H0 is true, p-values should be uniformly distributed [0, 1]
        # Expected Type I error rate ~ alpha (0.05)
        np.random.seed(42)
        n = 1000
        p_values = np.random.uniform(0, 1, n)
        
        df = pd.DataFrame({
            'sample_size': [50] * n,
            'effect_size': [0.0] * n,
            'test_type': ['t-test'] * n,
            'p_value': p_values,
            'hypothesis': ['H0'] * n
        })
        
        result_df = calculate_error_rates(df, alpha=0.05)
        
        assert not result_df.empty
        assert 'type_i_error_rate' in result_df.columns
        assert result_df['hypothesis'].iloc[0] == 'H0'
        
        # The observed rate should be close to 0.05 (within statistical fluctuation)
        observed_rate = result_df['type_i_error_rate'].iloc[0]
        assert 0.03 <= observed_rate <= 0.07, f"Type I error rate {observed_rate} outside expected range [0.03, 0.07]"

    def test_type_ii_error_rate_calculation(self):
        """Test Type II error rate calculation when H1 is true"""
        # Create mock data: H1 true, effect size > 0
        # Simulate low p-values (high power) -> low Type II error
        np.random.seed(42)
        n = 1000
        # Simulate high power scenario: most p-values < 0.05
        p_values = np.random.beta(1, 10, n)  # Skewed towards 0
        
        df = pd.DataFrame({
            'sample_size': [100] * n,
            'effect_size': [0.5] * n,
            'test_type': ['t-test'] * n,
            'p_value': p_values,
            'hypothesis': ['H1'] * n
        })
        
        result_df = calculate_error_rates(df, alpha=0.05)
        
        assert not result_df.empty
        assert 'type_ii_error_rate' in result_df.columns
        assert result_df['hypothesis'].iloc[0] == 'H1'
        
        observed_type_ii = result_df['type_ii_error_rate'].iloc[0]
        observed_power = result_df['power'].iloc[0]
        
        # Check consistency: power = 1 - type_ii
        assert np.isclose(observed_power, 1.0 - observed_type_ii, atol=1e-6)
        # With high power simulation, Type II should be low (< 0.2)
        assert observed_type_ii < 0.2, f"Type II error rate {observed_type_ii} unexpectedly high"

    def test_multiple_conditions(self):
        """Test calculation across multiple experimental conditions"""
        np.random.seed(123)
        
        data = []
        for n in [50, 100]:
            for eff in [0.0, 0.5]:
                for hyp in ['H0', 'H1']:
                    count = 200
                    if hyp == 'H0':
                        p_vals = np.random.uniform(0, 1, count)
                    else:
                        p_vals = np.random.beta(1, 5, count)
                    
                    for p in p_vals:
                        data.append({
                            'sample_size': n,
                            'effect_size': eff,
                            'test_type': 't-test',
                            'p_value': p,
                            'hypothesis': hyp
                        })
        
        df = pd.DataFrame(data)
        result_df = calculate_error_rates(df, alpha=0.05)
        
        # Should have 4 unique conditions (2 n * 2 eff * 2 hyp = 8? No, H0/H1 logic splits them)
        # Actually: n=50/100 (2), eff=0.0/0.5 (2), hyp=H0/H1 (2) => 8 rows expected
        assert len(result_df) == 8
        
        # Verify all expected columns exist
        expected_cols = ['sample_size', 'effect_size', 'test_type', 'hypothesis', 
                       'total_iterations', 'type_i_error_rate', 'type_ii_error_rate', 'power']
        for col in expected_cols:
            assert col in result_df.columns

class TestSaveAggregatedResults:
    def test_save_to_csv(self, tmp_path):
        """Test saving aggregated results to CSV"""
        df = pd.DataFrame({
            'sample_size': [50],
            'effect_size': [0.0],
            'test_type': ['t-test'],
            'hypothesis': ['H0'],
            'total_iterations': [100],
            'type_i_error_rate': [0.05],
            'type_ii_error_rate': [np.nan],
            'power': [0.05],
            'alpha': [0.05]
        })
        
        output_file = os.path.join(tmp_path, "test_output.csv")
        success = save_aggregated_results(df, output_file)
        
        assert success
        assert os.path.exists(output_file)
        
        # Verify content
        loaded_df = pd.read_csv(output_file)
        assert len(loaded_df) == 1
        assert loaded_df['type_i_error_rate'].iloc[0] == 0.05
        assert loaded_df['test_type'].iloc[0] == 't-test'