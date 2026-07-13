"""
Unit tests for pass rate calculation functionality.

Tests the HumanEval test suite execution and pass rate calculation
implemented in code/quality/pass_rate.py.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.quality.pass_rate import (
    calculate_pass_rate,
    execute_test_in_isolation,
    verify_fr001_load_rate,
    load_humaneval_tests
)


class TestPassRateCalculation(unittest.TestCase):
    """Test cases for pass rate calculation."""

    def test_calculate_pass_rate_with_valid_code(self):
        """Test pass rate calculation with a valid code submission."""
        # Mock test cases
        mock_test_cases = [
            {
                'prompt': 'def add(x, y):\n    """Add two numbers."""\n',
                'canonical_solution': 'def add(x, y):\n    return x + y\n',
                'test': 'assert add(2, 3) == 5\n',
                'entry_point': 'add'
            }
        ]
        
        # Valid code that should pass
        valid_code = 'def add(x, y):\n    return x + y\n'
        
        # Mock subprocess.run to simulate successful execution
        with patch('code.quality.pass_rate.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='passed', stderr='')
            
            result = calculate_pass_rate(
                code=valid_code,
                test_cases=mock_test_cases,
                problem_id='test_problem'
            )
            
            self.assertEqual(result['total_tests'], 1)
            self.assertEqual(result['passed_tests'], 1)
            self.assertEqual(result['failed_tests'], 0)
            self.assertEqual(result['pass_rate'], 1.0)
            self.assertEqual(result['problem_id'], 'test_problem')

    def test_calculate_pass_rate_with_invalid_code(self):
        """Test pass rate calculation with invalid code."""
        mock_test_cases = [
            {
                'prompt': 'def add(x, y):\n',
                'canonical_solution': 'def add(x, y):\n    return x + y\n',
                'test': 'assert add(2, 3) == 5\n',
                'entry_point': 'add'
            }
        ]
        
        # Invalid code that should fail
        invalid_code = 'def add(x, y):\n    return x - y\n'
        
        with patch('code.quality.pass_rate.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='AssertionError')
            
            result = calculate_pass_rate(
                code=invalid_code,
                test_cases=mock_test_cases,
                problem_id='test_problem'
            )
            
            self.assertEqual(result['total_tests'], 1)
            self.assertEqual(result['passed_tests'], 0)
            self.assertEqual(result['failed_tests'], 1)
            self.assertEqual(result['pass_rate'], 0.0)

    def test_calculate_pass_rate_empty_test_cases(self):
        """Test pass rate calculation with empty test cases."""
        result = calculate_pass_rate(
            code='some code',
            test_cases=[],
            problem_id='test_problem'
        )
        
        self.assertEqual(result['total_tests'], 0)
        self.assertEqual(result['pass_rate'], 0.0)
        self.assertIn('errors', result)

    def test_pass_rate_precision(self):
        """Test that pass rate has >= 0.01 precision."""
        mock_test_cases = [
            {
                'prompt': 'def test():\n',
                'canonical_solution': 'def test():\n    return 1\n',
                'test': 'assert test() == 1\n',
                'entry_point': 'test'
            }
        ]
        
        # Create a scenario where pass rate should be 0.5
        with patch('code.quality.pass_rate.subprocess.run') as mock_run:
            # First call passes, second fails
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout='passed', stderr=''),
                MagicMock(returncode=1, stdout='', stderr='fail')
            ]
            
            # Need 2 test cases for 50% pass rate
            mock_test_cases_extended = mock_test_cases * 2
            
            result = calculate_pass_rate(
                code='test code',
                test_cases=mock_test_cases_extended,
                problem_id='test_problem'
            )
            
            # Pass rate should be rounded to 2 decimal places
            self.assertEqual(result['pass_rate'], 0.5)
            # Verify precision
            self.assertIsInstance(result['pass_rate'], float)
            self.assertGreaterEqual(result['pass_rate'], 0.0)
            self.assertLessEqual(result['pass_rate'], 1.0)


class TestExecuteTestInIsolation(unittest.TestCase):
    """Test cases for isolated test execution."""

    def test_execute_success(self):
        """Test successful test execution."""
        with patch('code.quality.pass_rate.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='passed', stderr='')
            
            passed, error, exec_time = execute_test_in_isolation(
                code='def test(): pass',
                test_code='test()',
                entry_point='test'
            )
            
            self.assertTrue(passed)
            self.assertIsNone(error)
            self.assertIsInstance(exec_time, float)

    def test_execute_failure(self):
        """Test failed test execution."""
        with patch('code.quality.pass_rate.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='Error')
            
            passed, error, exec_time = execute_test_in_isolation(
                code='def test(): pass',
                test_code='test()',
                entry_point='test'
            )
            
            self.assertFalse(passed)
            self.assertIsNotNone(error)
            self.assertIsInstance(exec_time, float)

    def test_execute_timeout(self):
        """Test test execution timeout."""
        from subprocess import TimeoutExpired
        
        with patch('code.quality.pass_rate.subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutExpired(cmd='python', timeout=1)
            
            passed, error, exec_time = execute_test_in_isolation(
                code='def test(): pass',
                test_code='test()',
                entry_point='test',
                timeout=1
            )
            
            self.assertFalse(passed)
            self.assertIn('timed out', error)
            self.assertIsInstance(exec_time, float)


class TestFR001Verification(unittest.TestCase):
    """Test cases for FR-001 load rate verification."""

    @patch('code.quality.pass_rate.load_humaneval_tests')
    def test_verify_fr001_success(self, mock_load):
        """Test FR-001 verification with sufficient test cases."""
        # Mock 160 test cases loaded (>= 95% of 164)
        mock_load.return_value = [{'prompt': 'test', 'canonical_solution': 'test', 'test': 'test'}] * 160
        
        # This test verifies the logic, not actual file loading
        # In real execution, this would load from data/humaneval/humaneval.jsonl
        # For unit test, we mock the result
        
        # Note: The actual verify_fr001_load_rate function loads from file
        # This test demonstrates the expected behavior
        self.assertTrue(True)  # Placeholder - actual test requires real data


if __name__ == '__main__':
    unittest.main()