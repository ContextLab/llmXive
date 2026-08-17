import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add code to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from metrics.tost_equivalence import (
    perform_tost_test, 
    run_tost_equivalence_tests, 
    save_tost_results,
    load_hybrid_output
)

class TestTOSTEquivalence:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Setup temp directory for test artifacts
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = os.path.join(self.temp_dir, 'data', 'metrics')
        self.test_input_dir = os.path.join(self.temp_dir, 'data', 'processed')
        os.makedirs(self.test_output_dir, exist_ok=True)
        os.makedirs(self.test_input_dir, exist_ok=True)
        yield
        # Teardown
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_perform_tost_equivalent(self):
        """Test TOST when groups are truly equivalent."""
        # Create two groups with very similar means and small variance
        group_a = np.random.normal(loc=0.01, scale=0.01, size=1000)
        group_b = np.random.normal(loc=0.015, scale=0.01, size=1000)
        
        result = perform_tost_test(group_a, group_b, equivalence_margin=0.05)
        
        assert result['equivalent'] is True
        assert result['p_value_lower'] < 0.05
        assert result['p_value_upper'] < 0.05
        assert result['n_a'] == 1000
        assert result['n_b'] == 1000

    def test_perform_tost_not_equivalent(self):
        """Test TOST when groups are significantly different."""
        # Create two groups with large difference
        group_a = np.random.normal(loc=0.0, scale=0.01, size=1000)
        group_b = np.random.normal(loc=0.1, scale=0.01, size=1000)
        
        result = perform_tost_test(group_a, group_b, equivalence_margin=0.05)
        
        assert result['equivalent'] is False
        # At least one p-value should be > 0.05

    def test_perform_tost_empty_group(self):
        """Test TOST with empty group."""
        group_a = np.array([])
        group_b = np.random.normal(loc=0.0, scale=0.01, size=100)
        
        result = perform_tost_test(group_a, group_b)
        
        assert result['equivalent'] is False
        assert 'error' in result

    def test_run_tost_equivalence_tests_integration(self):
        """Integration test for run_tost_equivalence_tests."""
        # Create a mock hybrid dataframe
        n = 2000
        df = pd.DataFrame({
            'frame_id': range(n),
            'latency': np.random.normal(100, 10, n),
            'fid_score': np.random.normal(0.02, 0.005, n),
            'skip_flag': [i % 2 == 0 for i in range(n)] # 50% skipped
        })
        
        results = run_tost_equivalence_tests(df, metric_columns=['fid_score', 'latency'], equivalence_margin=0.05)
        
        assert len(results) == 2
        for r in results:
            assert r['status'] == 'completed'
            assert 'p_value_lower' in r
            assert 'p_value_upper' in r
            assert 'equivalent' in r

    def test_save_tost_results(self):
        """Test saving TOST results to CSV."""
        results = [
            {
                'metric': 'fid_score',
                'equivalence_margin': 0.05,
                'n_skipped': 100,
                'n_full': 100,
                'mean_skipped': 0.02,
                'mean_full': 0.021,
                'diff_mean': -0.001,
                'p_value_lower': 0.01,
                'p_value_upper': 0.02,
                'equivalent': True,
                'status': 'completed'
            }
        ]
        
        output_path = os.path.join(self.test_output_dir, 'test_tost_results.csv')
        save_tost_results(results, output_path)
        
        assert os.path.exists(output_path)
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert df.iloc[0]['metric'] == 'fid_score'
        assert df.iloc[0]['equivalent'] is True

    def test_load_hybrid_output_missing_file(self):
        """Test loading from missing file raises error."""
        with pytest.raises(FileNotFoundError):
            load_hybrid_output('non_existent_path.parquet')

    def test_load_hybrid_output_invalid_schema(self):
        """Test loading file with missing columns raises error."""
        temp_path = os.path.join(self.temp_dir, 'invalid.parquet')
        df_invalid = pd.DataFrame({'wrong_col': [1, 2, 3]})
        df_invalid.to_parquet(temp_path)
        
        with pytest.raises(ValueError):
            load_hybrid_output(temp_path)
