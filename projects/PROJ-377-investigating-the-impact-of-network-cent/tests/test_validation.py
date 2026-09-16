import unittest
import pandas as pd
import numpy as np
import json
from unittest.mock import patch
from pathlib import Path
from code.analysis.validation import load_null_residuals, run_freedman_lane_permutation, save_permutation_results, run_validation_analysis

class TestValidation(unittest.TestCase):

    @patch('code.analysis.validation.get_permutation_shuffles')
    @patch('code.analysis.validation.get_permutation_seed')
    def test_run_validation_analysis(self, mock_get_seed, mock_get_shuffles):
        mock_get_shuffles.return_value = 100
        mock_get_seed.return_value = 42
        null_residuals_path = "data/processed/validation/null_residuals.csv"
        output_path = "data/processed/validation/permutation_results.json"

        # Create a dummy null_residuals.csv file
        dummy_data = pd.DataFrame({'residuals': [1.0, 2.0, 3.0, 4.0, 5.0]})
        dummy_data.to_csv(null_residuals_path, index=False)

        run_validation_analysis(null_residuals_path, output_path)

        # Check if the output file is created
        self.assertTrue(Path(output_path).exists())

        # Load the results from the output file
        with open(output_path, 'r') as f:
            results = json.load(f)

        # Check if the p-value is valid
        self.assertAlmostEqual(results['p_value'], 0.0, places=1)

        # Clean up the dummy file
        os.remove(null_residuals_path)
        os.remove(output_path)

if __name__ == '__main__':
    unittest.main()