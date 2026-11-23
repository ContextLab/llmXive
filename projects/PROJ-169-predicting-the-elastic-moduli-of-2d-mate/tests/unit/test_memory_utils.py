import unittest
from utils.memory_utils import calculate_max_safe_sample_size

class TestMemoryUtils(unittest.TestCase):

    def test_calculate_max_safe_sample_size(self):
        # Example values for testing (adjust as needed)
        available_memory_gb = 7.0  # Available memory in GB
        item_size_bytes = 1024    # Size of each item in bytes

        # Calculate the maximum safe sample size
        max_sample_size = calculate_max_safe_sample_size(available_memory_gb, item_size_bytes)

        # Assert that the calculated value is within a reasonable range
        self.assertIsInstance(max_sample_size, int)
        self.assertTrue(max_sample_size > 0)

if __name__ == '__main__':
    unittest.main()