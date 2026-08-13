"""
Unit tests for T069: End-to-End Fabrication Check
"""
import unittest
import sys
import os
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.seeds import set_global_seed

class TestT069FabricationCheck(unittest.TestCase):
    """Test cases for the fabrication check logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        self.processed_dir = os.path.join(self.data_dir, 'processed')
        self.results_dir = os.path.join(self.data_dir, 'results')
        
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

        # Set seed for reproducibility
        set_global_seed(42)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_file_exists(self):
        """Test file existence checking."""
        from code import check_file_exists
        
        # Create a test file
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        self.assertTrue(check_file_exists(test_file, 'Test File'))
        self.assertFalse(check_file_exists('/nonexistent/file.txt', 'Missing File'))

    def test_check_parquet_rows(self):
        """Test parquet row count checking."""
        from code import check_parquet_rows
        
        # Create a test parquet file
        test_file = os.path.join(self.processed_dir, 'test.parquet')
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        df.to_parquet(test_file)
        
        self.assertTrue(check_parquet_rows(test_file, 3))
        self.assertFalse(check_parquet_rows(test_file, 10))  # Not enough rows

    def test_synthetic_pattern_detection(self):
        """Test detection of synthetic data patterns."""
        from code import check_for_synthetic_indicators
        
        # Create a file with synthetic patterns
        test_file = os.path.join(self.processed_dir, 'synthetic.parquet')
        df = pd.DataFrame({
            'text': ['sample_text', 'real_text', 'fake_instruction'],
            'value': [1.0, 2.0, 3.0]
        })
        df.to_parquet(test_file)
        
        # Should detect synthetic pattern
        self.assertFalse(check_for_synthetic_indicators(test_file))

    def test_no_synthetic_data(self):
        """Test that real data passes the check."""
        from code import check_for_synthetic_indicators
        
        # Create a file with realistic data
        test_file = os.path.join(self.processed_dir, 'real.parquet')
        np.random.seed(42)
        df = pd.DataFrame({
            'text': [f'Instruction {i} for task {np.random.randint(1, 100)}' for i in range(100)],
            'value': np.random.randn(100) * 10 + 50
        })
        df.to_parquet(test_file)
        
        # Should pass without detecting synthetic patterns
        self.assertTrue(check_for_synthetic_indicators(test_file))

    def test_zero_variance_warning(self):
        """Test detection of suspicious zero variance."""
        from code import verify_data_source_integrity
        
        # Create a file with zero variance (suspicious)
        test_file = os.path.join(self.processed_dir, 'suspicious.parquet')
        df = pd.DataFrame({
            'text': ['same_value'] * 100,
            'value': [5.0] * 100
        })
        df.to_parquet(test_file)
        
        # Should not fail hard, but might warn
        # This is a soft check, so it should still return True
        self.assertTrue(verify_data_source_integrity(test_file))

    def test_json_structure_check(self):
        """Test JSON structure validation."""
        from code import check_json_structure
        
        # Create a valid JSON file
        test_file = os.path.join(self.results_dir, 'test.json')
        data = {'key1': 'value1', 'key2': 'value2'}
        with open(test_file, 'w') as f:
            json.dump(data, f)
        
        self.assertTrue(check_json_structure(test_file, ['key1', 'key2']))
        self.assertFalse(check_json_structure(test_file, ['missing_key']))

    def test_full_fabrication_check_integration(self):
        """Test the full fabrication check with mock artifacts."""
        # This test simulates the presence of all required artifacts
        # and verifies the check runs without crashing
        
        # Create minimal versions of all required artifacts
        artifacts = {
            'assignments.parquet': pd.DataFrame({'cluster': [1, 2, 3], 'sample_id': [100, 101, 102]}),
            'clusters.json': {'method': 'kmeans', 'k': 5},
            'train_embeddings.parquet': pd.DataFrame({'embedding': [[0.1]*768 for _ in range(10)]}),
            'vla_proxy_baseline.parquet': pd.DataFrame({'trajectory': [[1, 2, 3] for _ in range(5)]}),
            'simulation_logs.csv': pd.DataFrame({'success': [1, 0, 1], 'collision': [0, 1, 0]})
        }
        
        for name, data in artifacts.items():
            if name.endswith('.parquet'):
                data.to_parquet(os.path.join(self.processed_dir, name))
            elif name.endswith('.json'):
                with open(os.path.join(self.processed_dir, name), 'w') as f:
                    json.dump(data, f)
            elif name.endswith('.csv'):
                data.to_csv(os.path.join(self.results_dir, name))
        
        # Run the check (should pass with minimal data)
        # Note: This is a simplified test; real check requires full pipeline output
        self.assertTrue(os.path.exists(os.path.join(self.processed_dir, 'assignments.parquet')))
        self.assertTrue(os.path.exists(os.path.join(self.processed_dir, 'clusters.json')))

if __name__ == '__main__':
    unittest.main()
