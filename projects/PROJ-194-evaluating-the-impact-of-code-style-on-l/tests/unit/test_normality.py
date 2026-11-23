import unittest
from scipy.stats import shapiro
import numpy as np

class TestNormalityCheck(unittest.TestCase):

    def test_shapiro_wilk_normal_data(self):
        # Generate normally distributed data
        data = np.random.normal(loc=0, scale=1, size=100)
        # Perform Shapiro-Wilk test
        stat, p = shapiro(data)
        # Check if p-value is greater than 0.05 (indicating normality)
        self.assertGreater(p, 0.05)

    def test_shapiro_wilk_non_normal_data(self):
        # Generate non-normally distributed data (e.g., exponential)
        data = np.random.exponential(scale=1, size=100)
        # Perform Shapiro-Wilk test
        stat, p = shapiro(data)
        # Check if p-value is less than 0.05 (indicating non-normality)
        self.assertLess(p, 0.05)

if __name__ == '__main__':
    unittest.main()