import unittest
import sys
import os
import tempfile
import pandas as pd
import numpy as np

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.analyze import compute_correlations


class TestCorrelationCalculation(unittest.TestCase):
    """
    Unit test for correlation calculation in data.analyze.
    Tests Pearson coefficient with perfectly correlated and uncorrelated series.
    """

    def test_correlation_calculation(self):
        """
        Verify Pearson coefficient is ~1.0 for perfectly correlated series (y=x)
        and ~0.0 for uncorrelated series (y=random).
        """
        # Create a temporary directory for test data
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test Case 1: Perfectly correlated series (y = x)
            # Generate a time series
            dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
            values_x = np.arange(100, dtype=float)
            values_y_perfect = values_x.copy()  # y = x

            df_perfect = pd.DataFrame({
                'date': dates,
                'news_zscore': values_x,
                'anxiety_zscore': values_y_perfect
            })

            # Save to a temporary CSV
            path_perfect = os.path.join(tmpdir, 'perfect_corr.csv')
            df_perfect.to_csv(path_perfect, index=False)

            # Run correlation calculation
            result_perfect = compute_correlations(path_perfect)

            # Assert Pearson coefficient is approximately 1.0
            self.assertAlmostEqual(result_perfect['pearson_r'], 1.0, places=5,
                                   msg="Pearson coefficient should be ~1.0 for perfectly correlated series")
            self.assertAlmostEqual(result_perfect['spearman_r'], 1.0, places=5,
                                   msg="Spearman coefficient should be ~1.0 for perfectly correlated series")
            # P-value should be very small (highly significant)
            self.assertLess(result_perfect['pearson_p'], 0.001,
                            msg="P-value should be very small for perfect correlation")

            # Test Case 2: Uncorrelated series (y = random noise)
            np.random.seed(42)  # For reproducibility
            values_y_uncorrelated = np.random.normal(0, 1, 100)

            df_uncorrelated = pd.DataFrame({
                'date': dates,
                'news_zscore': values_x,
                'anxiety_zscore': values_y_uncorrelated
            })

            # Save to a temporary CSV
            path_uncorrelated = os.path.join(tmpdir, 'uncorrelated.csv')
            df_uncorrelated.to_csv(path_uncorrelated, index=False)

            # Run correlation calculation
            result_uncorrelated = compute_correlations(path_uncorrelated)

            # Assert Pearson coefficient is approximately 0.0 (allow some tolerance for randomness)
            self.assertLess(abs(result_uncorrelated['pearson_r']), 0.2,
                            msg="Pearson coefficient should be close to 0.0 for uncorrelated series")
            # P-value should be large (not significant)
            self.assertGreater(result_uncorrelated['pearson_p'], 0.05,
                               msg="P-value should be > 0.05 for uncorrelated series")


if __name__ == '__main__':
    unittest.main()