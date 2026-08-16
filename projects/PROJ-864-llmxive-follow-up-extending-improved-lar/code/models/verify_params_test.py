"""
Unit tests for verify_params.py
"""
import sys
import unittest
from pathlib import Path

# Add code root to path
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from models.verify_params import count_parameters, verify_parameter_counts


class TestVerifyParams(unittest.TestCase):
    
    def test_count_parameters_basic(self):
        """Test that count_parameters works on a simple model."""
        import torch.nn as nn
        model = nn.Linear(10, 5)
        # 10*5 weights + 5 biases = 55
        self.assertEqual(count_parameters(model), 55)

    def test_verify_parameter_counts_logic(self):
        """Test the verification logic with mock numbers."""
        # Test passing case
        result = verify_parameter_counts(1000, 1000, {}, tolerance=0.01)
        self.assertTrue(result['overall_passed'])
        self.assertTrue(result['symmetry_check']['passed'])

        # Test failing case (large difference)
        result = verify_parameter_counts(1000, 2000, {}, tolerance=0.01)
        self.assertFalse(result['overall_passed'])
        self.assertFalse(result['symmetry_check']['passed'])

        # Test zero parameters
        result = verify_parameter_counts(0, 1000, {}, tolerance=0.01)
        self.assertFalse(result['overall_passed'])


if __name__ == '__main__':
    unittest.main()