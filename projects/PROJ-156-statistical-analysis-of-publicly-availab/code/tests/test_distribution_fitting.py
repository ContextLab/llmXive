import unittest
import os
import sys
import tempfile
import shutil
import csv
import json
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.fit_distributions import (
    fit_distribution, 
    group_by_game, 
    load_config, 
    perform_anderson_darling
)

class TestDistributionFitting(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'data', 'processed')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Mock config
        self.config_path = os.path.join(self.test_dir, 'code')
        os.makedirs(self.config_path, exist_ok=True)
        self.config_file = os.path.join(self.config_path, 'config.yaml')
        with open(self.config_file, 'w') as f:
            f.write("games:\n  - test-game\nmin_sample_size: 10\nsalt: test\n")
        
        # Mock data
        self.data_file = os.path.join(self.data_dir, 'run_records.csv')
        with open(self.data_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['game_id', 'run_time_seconds', 'runner_id', 'attempt_number', 'submission_date'])
            # Generate 100 log-normal distributed values for test-game
            import random
            import math
            for i in range(100):
                # Simulate log-normal: exp(N(0, 1))
                val = math.exp(random.gauss(0, 0.5))
                writer.writerow(['test-game', f"{val:.4f}", f"runner_{i}", i, "2023-01-01"])

        # Temporarily override paths in the module if needed, 
        # but since the functions take paths as arguments or read from fixed locations,
        # we will mock the file system or use the test directory.
        # For this test, we will test the logic functions directly with data.

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_fit_lognormal(self):
        """Test fitting a log-normal distribution to log-normal data."""
        import math
        import random
        data = [math.exp(random.gauss(0, 0.5)) for _ in range(1000)]
        
        params, ks_d, ks_p, aic = fit_distribution(data, 'lognormal')
        
        self.assertIsNotNone(params)
        self.assertIsNotNone(ks_d)
        self.assertIsNotNone(ks_p)
        self.assertIsNotNone(aic)
        
        # For log-normal data, KS p-value should be high (not rejected)
        self.assertGreater(ks_p, 0.05)

    def test_fit_weibull(self):
        """Test fitting Weibull distribution."""
        import math
        import random
        # Generate Weibull data
        data = [random.weibullvariate(1.0, 2.0) for _ in range(1000)]
        
        params, ks_d, ks_p, aic = fit_distribution(data, 'weibull_min')
        
        self.assertIsNotNone(params)
        self.assertIsNotNone(ks_d)
        self.assertIsNotNone(ks_p)
        self.assertIsNotNone(aic)

    def test_fit_gamma(self):
        """Test fitting Gamma distribution."""
        import random
        # Generate Gamma data
        data = [random.gammavariate(2.0, 1.0) for _ in range(1000)]
        
        params, ks_d, ks_p, aic = fit_distribution(data, 'gamma')
        
        self.assertIsNotNone(params)
        self.assertIsNotNone(ks_d)
        self.assertIsNotNone(ks_p)
        self.assertIsNotNone(aic)

    def test_group_by_game(self):
        """Test grouping records by game."""
        records = [
            {'game_id': 'A', 'run_time_seconds': 10.0},
            {'game_id': 'B', 'run_time_seconds': 20.0},
            {'game_id': 'A', 'run_time_seconds': 15.0}
        ]
        grouped = group_by_game(records)
        
        self.assertIn('A', grouped)
        self.assertIn('B', grouped)
        self.assertEqual(len(grouped['A']), 2)
        self.assertEqual(len(grouped['B']), 1)

    def test_anderson_darling_lognormal(self):
        """Test Anderson-Darling statistic for lognormal."""
        import math
        import random
        data = [math.exp(random.gauss(0, 0.5)) for _ in range(100)]
        
        stat = perform_anderson_darling(data, 'lognormal')
        
        self.assertIsNotNone(stat)
        self.assertIsInstance(stat, float)

if __name__ == '__main__':
    unittest.main()