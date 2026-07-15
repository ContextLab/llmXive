import pytest
import os
import tempfile
import pandas as pd
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results

class TestCalculateErrorRates:
    def test_type_i_error_calculation(self):
        """Test Type I error calculation when null hypothesis is true"""
        data = [
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.01, 'hypothesis': 'null'},
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.03, 'hypothesis': 'null'},
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.06, 'hypothesis': 'null'},
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.08, 'hypothesis': 'null'},
        ]
        
        results = calculate_error_rates(data, alpha=0.05)
        
        assert len(results) == 1
        assert results[0]['error_type'] == 'type_i'
        assert results[0]['total_iterations'] == 4
        assert results[0]['error_count'] == 2  # 0.01 and 0.03 are < 0.05
        assert abs(results[0]['error_rate'] - 0.5) < 0.001

    def test_type_ii_error_calculation(self):
        """Test Type II error calculation when alternative hypothesis is true"""
        data = [
            {'sample_size': 30, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.01, 'hypothesis': 'alternative'},
            {'sample_size': 30, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.03, 'hypothesis': 'alternative'},
            {'sample_size': 30, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.06, 'hypothesis': 'alternative'},
            {'sample_size': 30, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.08, 'hypothesis': 'alternative'},
        ]
        
        results = calculate_error_rates(data, alpha=0.05)
        
        assert len(results) == 1
        assert results[0]['error_type'] == 'type_ii'
        assert results[0]['total_iterations'] == 4
        assert results[0]['error_count'] == 2  # 0.06 and 0.08 are > 0.05
        assert abs(results[0]['error_rate'] - 0.5) < 0.001

    def test_multiple_conditions(self):
        """Test aggregation across multiple conditions"""
        data = [
            # Condition 1: null hypothesis
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.01, 'hypothesis': 'null'},
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.06, 'hypothesis': 'null'},
            # Condition 2: alternative hypothesis
            {'sample_size': 30, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.01, 'hypothesis': 'alternative'},
            {'sample_size': 30, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.06, 'hypothesis': 'alternative'},
            # Condition 3: different sample size
            {'sample_size': 50, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.04, 'hypothesis': 'null'},
            {'sample_size': 50, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.07, 'hypothesis': 'null'},
        ]
        
        results = calculate_error_rates(data, alpha=0.05)
        
        assert len(results) == 3
        
        # Verify each condition
        cond1 = [r for r in results if r['sample_size'] == 30 and r['hypothesis'] == 'null'][0]
        assert cond1['error_count'] == 1
        assert cond1['error_rate'] == 0.5
        
        cond2 = [r for r in results if r['sample_size'] == 30 and r['hypothesis'] == 'alternative'][0]
        assert cond2['error_count'] == 1
        assert cond2['error_rate'] == 0.5
        
        cond3 = [r for r in results if r['sample_size'] == 50 and r['hypothesis'] == 'null'][0]
        assert cond3['error_count'] == 1
        assert cond3['error_rate'] == 0.5

    def test_empty_data(self):
        """Test handling of empty data"""
        results = calculate_error_rates([], alpha=0.05)
        assert results == []

    def test_invalid_p_values(self):
        """Test handling of invalid p-values (NaN)"""
        data = [
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.01, 'hypothesis': 'null'},
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': float('nan'), 'hypothesis': 'null'},
            {'sample_size': 30, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.06, 'hypothesis': 'null'},
        ]
        
        results = calculate_error_rates(data, alpha=0.05)
        
        # Should only use valid p-values
        assert len(results) == 1
        assert results[0]['total_iterations'] == 2
        assert results[0]['error_count'] == 1

class TestSaveAggregatedResults:
    def test_save_to_csv(self):
        """Test saving results to CSV file"""
        data = [
            {
                'sample_size': 30,
                'effect_size': 0.0,
                'test_type': 't-test',
                'hypothesis': 'null',
                'error_type': 'type_i',
                'total_iterations': 100,
                'error_count': 5,
                'error_rate': 0.05,
                'alpha_threshold': 0.05
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            save_aggregated_results(data, temp_path)
            
            assert os.path.exists(temp_path)
            
            df = pd.read_csv(temp_path)
            assert len(df) == 1
            assert df['sample_size'].iloc[0] == 30
            assert df['error_rate'].iloc[0] == 0.05
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_empty_results(self):
        """Test saving empty results creates file with headers"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            save_aggregated_results([], temp_path)
            
            assert os.path.exists(temp_path)
            
            df = pd.read_csv(temp_path)
            assert len(df) == 0
            assert 'sample_size' in df.columns
            assert 'error_rate' in df.columns
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_create_directories(self):
        """Test that function creates necessary directories"""
        data = [
            {
                'sample_size': 30,
                'effect_size': 0.0,
                'test_type': 't-test',
                'hypothesis': 'null',
                'error_type': 'type_i',
                'total_iterations': 100,
                'error_count': 5,
                'error_rate': 0.05,
                'alpha_threshold': 0.05
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, 'subdir1', 'subdir2', 'output.csv')
            
            save_aggregated_results(data, nested_path)
            
            assert os.path.exists(nested_path)
            df = pd.read_csv(nested_path)
            assert len(df) == 1