import os
import sys
import unittest
import pandas as pd
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.correlation import calculate_correlation_with_training
from code.data.synthetic_generator import generate_synthetic_dataset

class TestCorrelationAnalysis(unittest.TestCase):

    def test_integration_correlation_on_synthetic_data(self):
        # Generate synthetic data for testing
        num_subjects = 10
        df = generate_synthetic_dataset(num_subjects)

        # Filter musicians (years_of_training >= 1)
        musicians = df[df['years_of_training'] >= 1]

        if len(musicians) == 0:
            self.fail("No musicians found in the synthetic data.")

        # Calculate correlation between training years and a connectivity measure (e.g., 'connectivity_strength')
        correlation, p_value = calculate_correlation_with_training(musicians, 'connectivity_strength', 'years_of_training')

        # Assert that correlation is calculated and within a reasonable range
        self.assertIsNotNone(correlation)
        self.assertIsNotNone(p_value)
        self.assertTrue(-1 <= correlation <= 1)
        self.assertTrue(0 <= p_value <= 1)

        print("Correlation test passed successfully.")

if __name__ == '__main__':
    unittest.main()