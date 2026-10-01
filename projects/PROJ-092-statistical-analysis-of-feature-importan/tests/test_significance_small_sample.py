import pytest
import os
import csv
import tempfile
import math
from code.significance_test import mann_kendall_test, block_permutation_test, run_significance_tests

class TestSmallSampleHandling:
    """Tests for T024: Small sample size constraints (n < 10) and permutation reliance."""

    def test_mann_kendall_small_sample_returns_values(self):
        """Verify MK test runs but returns values that should be flagged as unreliable for n < 10."""
        # Create a small dataset (n=5)
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        tau, p, trend = mann_kendall_test(data)
        
        assert isinstance(tau, float)
        assert isinstance(p, float)
        assert trend in ["monotonic increase", "monotonic decrease", "no trend"]
        # For perfect increase, trend should be increase
        assert trend == "monotonic increase"

    def test_block_permutation_small_sample(self):
        """Verify block permutation test works on small samples."""
        data = [0.1, 0.2, 0.3, 0.4, 0.5]
        p_val = block_permutation_test(data, n_resamples=100)
        
        assert 0.0 <= p_val <= 1.0
        # For a perfect trend, p-value should be low (significant)
        assert p_val < 0.1

    def test_run_significance_switches_to_permutation(self):
        """Test that run_significance_tests uses permutation for n < 10."""
        # Create a temporary CSV with 4 rows (n=4 < 10)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_in:
            writer = csv.DictWriter(tmp_in, fieldnames=['window_t', 'window_t+1', 'rho', 'p_value'])
            writer.writeheader()
            # 4 windows -> 3 transitions? No, 4 rows in input means 4 rho values.
            # Let's create 4 rho values.
            rows = [
                {'window_t': '1', 'window_t+1': '2', 'rho': '0.9', 'p_value': '0.0'},
                {'window_t': '2', 'window_t+1': '3', 'rho': '0.8', 'p_value': '0.0'},
                {'window_t': '3', 'window_t+1': '4', 'rho': '0.7', 'p_value': '0.0'},
                {'window_t': '4', 'window_t+1': '5', 'rho': '0.6', 'p_value': '0.0'},
            ]
            writer.writerows(rows)
            input_path = tmp_in.name

        output_path = input_path.replace('.csv', '_final.csv')

        try:
            result = run_significance_tests(input_path, output_path)
            
            # Verify the result indicates permutation was used
            assert result['n'] == 4
            assert result['method_used'] == 'block_permutation'
            assert 'p_value' in result
            assert 0.0 <= result['p_value'] <= 1.0

            # Verify the output file contains the method tag
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows_out = list(reader)
                assert len(rows_out) == 4
                assert 'p_value_method' in rows_out[0]
                assert all(row['p_value_method'] == 'block_permutation' for row in rows_out)
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_run_significance_uses_mk_for_large_sample(self):
        """Test that run_significance_tests uses Mann-Kendall for n >= 10."""
        # Create a temporary CSV with 12 rows (n=12 >= 10)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_in:
            writer = csv.DictWriter(tmp_in, fieldnames=['window_t', 'window_t+1', 'rho', 'p_value'])
            writer.writeheader()
            # 12 rho values
            rows = []
            for i in range(12):
                rows.append({
                    'window_t': str(i), 
                    'window_t+1': str(i+1), 
                    'rho': str(0.9 - (i * 0.05)), 
                    'p_value': '0.0'
                })
            writer.writerows(rows)
            input_path = tmp_in.name

        output_path = input_path.replace('.csv', '_final.csv')

        try:
            result = run_significance_tests(input_path, output_path)
            
            # Verify the result indicates MK approximation was used
            assert result['n'] == 12
            assert result['method_used'] == 'mann_kendall_approx'
            assert 'p_value' in result
            assert 0.0 <= result['p_value'] <= 1.0

            # Verify the output file contains the method tag
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows_out = list(reader)
                assert all(row['p_value_method'] == 'mann_kendall_approx' for row in rows_out)
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
