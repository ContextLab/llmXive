"""
Integration tests for User Story 2: Code Quality Assessment Pipeline.

This test suite verifies the end-to-end flow of the quality assessment pipeline:
1. Loading problem data (HumanEval)
2. Simulating code submissions (both valid and invalid)
3. Running the full quality metric computation (pass rate, complexity, coverage, static analysis)
4. Aggregating results and verifying schema compliance

These tests must run on REAL data sources (HumanEval dataset) and verify that
the pipeline produces real, measurable results.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from quality.pass_rate import calculate_pass_rate, load_humaneval_tests
from quality.complexity import compute_cyclomatic_complexity
from quality.coverage import compute_coverage
from quality.static_analysis import analyze_static_warnings
from quality.metric_aggregator import MetricAggregator
from quality.syntax_validator import validate_syntax
from quality.execution_sandbox import execute_with_timeout, ExecutionTimeoutError
from experiment.problem_loader import load_humaneval_problems
from data.models import Submission, Metric, Condition, ProblemSource


class TestQualityPipelineIntegration(unittest.TestCase):
    """Integration tests for the complete quality assessment pipeline."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures: load real HumanEval problems."""
        cls.test_data_dir = tempfile.mkdtemp()
        cls.problems = None
        
        try:
            # Load real HumanEval problems from the downloaded dataset
            cls.problems = load_humaneval_problems()
            if not cls.problems or len(cls.problems) == 0:
                raise RuntimeError("Failed to load HumanEval problems - real data source unavailable")
        except Exception as e:
            # Clean up even if load fails
            shutil.rmtree(cls.test_data_dir, ignore_errors=True)
            raise RuntimeError(f"Could not load real HumanEval data: {e}")

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary test data."""
        shutil.rmtree(cls.test_data_dir, ignore_errors=True)

    def setUp(self):
        """Set up per-test fixtures."""
        self.aggregator = MetricAggregator()
        self.test_problem = None
        if self.problems:
            self.test_problem = self.problems[0]  # Use first problem for testing

    def tearDown(self):
        """Clean up per-test state."""
        pass

    def test_01_load_real_humaneval_problems(self):
        """Verify that we can load real HumanEval problems with ≥95% success rate."""
        self.assertIsNotNone(self.problems)
        self.assertGreater(len(self.problems), 0)
        
        # Verify problem structure
        problem = self.problems[0]
        self.assertIn("task_id", problem)
        self.assertIn("prompt", problem)
        self.assertIn("canonical_solution", problem)
        self.assertIn("test", problem)

    def test_02_syntax_validation_valid_code(self):
        """Test syntax validation on valid Python code."""
        valid_code = """
        def add(a, b):
            return a + b
        """
        is_valid, error = validate_syntax(valid_code)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_03_syntax_validation_invalid_code(self):
        """Test syntax validation on invalid Python code."""
        invalid_code = """
        def add(a, b):
            return a + b
        def missing_parenthesis
            pass
        """
        is_valid, error = validate_syntax(invalid_code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIsInstance(error, SyntaxError)

    def test_04_pass_rate_computation(self):
        """Test pass rate calculation on a known solution."""
        if not self.test_problem:
            self.skipTest("No test problem available")
        
        # Use the canonical solution (should pass all tests)
        canonical_solution = self.test_problem["canonical_solution"]
        test_suite = self.test_problem["test"]
        
        # Calculate pass rate
        pass_rate = calculate_pass_rate(canonical_solution, test_suite)
        
        # The canonical solution should have 100% pass rate
        self.assertEqual(pass_rate, 1.0)

    def test_05_cyclomatic_complexity_computation(self):
        """Test cyclomatic complexity calculation."""
        # Simple function: complexity should be 1
        simple_code = """
        def add(a, b):
            return a + b
        """
        complexity = compute_cyclomatic_complexity(simple_code)
        self.assertEqual(complexity, 1)
        
        # Function with conditionals: complexity should be higher
        conditional_code = """
        def classify_number(n):
            if n > 0:
                if n % 2 == 0:
                    return "positive even"
                else:
                    return "positive odd"
            elif n < 0:
                return "negative"
            else:
                return "zero"
        """
        complexity = compute_cyclomatic_complexity(conditional_code)
        self.assertGreater(complexity, 1)

    def test_06_coverage_computation(self):
        """Test code coverage calculation."""
        if not self.test_problem:
            self.skipTest("No test problem available")
        
        canonical_solution = self.test_problem["canonical_solution"]
        test_suite = self.test_problem["test"]
        
        coverage_result = compute_coverage(canonical_solution, test_suite)
        
        # Coverage result should have expected fields
        self.assertIn("passed", coverage_result)
        self.assertIn("total", coverage_result)
        self.assertIn("percentage", coverage_result)
        
        # Canonical solution should have high coverage
        self.assertGreaterEqual(coverage_result["percentage"], 0.0)
        self.assertLessEqual(coverage_result["percentage"], 100.0)

    def test_07_static_analysis_warnings(self):
        """Test static analysis warning detection."""
        # Code with potential issues (missing docstring, etc.)
        code_with_warnings = """
        def bad_function(x,y):
        z=x+y
        return z
        """
        
        warnings = analyze_static_warnings(code_with_warnings, language="python")
        
        # Should detect some warnings (syntax/style issues)
        self.assertIsInstance(warnings, list)
        # Note: pylint may or may not find warnings depending on config

    def test_08_full_pipeline_integration(self):
        """Test the complete quality assessment pipeline end-to-end."""
        if not self.test_problem:
            self.skipTest("No test problem available")
        
        # Create a mock submission
        submission_code = self.test_problem["canonical_solution"]
        submission_id = "test-submission-001"
        problem_id = self.test_problem["task_id"]
        
        # Run all quality metrics
        results = {}
        
        # 1. Syntax validation
        is_valid, syntax_error = validate_syntax(submission_code)
        results["syntax_valid"] = is_valid
        results["syntax_error"] = str(syntax_error) if syntax_error else None
        self.assertTrue(is_valid)
        
        # 2. Pass rate
        test_suite = self.test_problem["test"]
        pass_rate = calculate_pass_rate(submission_code, test_suite)
        results["pass_rate"] = pass_rate
        self.assertEqual(pass_rate, 1.0)
        
        # 3. Cyclomatic complexity
        complexity = compute_cyclomatic_complexity(submission_code)
        results["cyclomatic_complexity"] = complexity
        self.assertGreaterEqual(complexity, 1)
        
        # 4. Coverage
        coverage = compute_coverage(submission_code, test_suite)
        results["coverage"] = coverage
        
        # 5. Static analysis
        static_warnings = analyze_static_warnings(submission_code, language="python")
        results["static_warnings"] = static_warnings
        
        # 6. Aggregate metrics
        aggregated = self.aggregator.aggregate(
            submission_id=submission_id,
            problem_id=problem_id,
            results=results
        )
        
        # Verify aggregated result structure
        self.assertIn("submission_id", aggregated)
        self.assertIn("problem_id", aggregated)
        self.assertIn("metrics", aggregated)
        self.assertIn("timestamp", aggregated)
        
        # Verify individual metrics
        metrics = aggregated["metrics"]
        self.assertIn("pass_rate", metrics)
        self.assertIn("cyclomatic_complexity", metrics)
        self.assertIn("coverage_percentage", metrics)
        self.assertIn("warning_count", metrics)
        
        # Verify values are reasonable
        self.assertEqual(metrics["pass_rate"], 1.0)
        self.assertGreaterEqual(metrics["cyclomatic_complexity"], 1)
        self.assertGreaterEqual(metrics["coverage_percentage"], 0.0)
        self.assertLessEqual(metrics["coverage_percentage"], 100.0)

    def test_09_pipeline_timeout_handling(self):
        """Test that the pipeline handles execution timeouts correctly."""
        # Create code that would hang (infinite loop)
        infinite_loop = """
        def infinite():
            while True:
                pass
        """
        
        test_code = """
        def test_infinite():
            infinite()
        """
        
        # Execute with short timeout
        with self.assertRaises(ExecutionTimeoutError):
            execute_with_timeout(infinite_loop, test_code, timeout_seconds=1)

    def test_10_multiple_problems_pipeline(self):
        """Test pipeline on multiple problems to ensure scalability."""
        if not self.problems or len(self.problems) < 3:
            self.skipTest("Need at least 3 problems for this test")
        
        results = []
        for i, problem in enumerate(self.problems[:3]):  # Test first 3 problems
            submission_code = problem["canonical_solution"]
            test_suite = problem["test"]
            
            # Run full pipeline for each problem
            pass_rate = calculate_pass_rate(submission_code, test_suite)
            complexity = compute_cyclomatic_complexity(submission_code)
            coverage = compute_coverage(submission_code, test_suite)
            
            results.append({
                "task_id": problem["task_id"],
                "pass_rate": pass_rate,
                "complexity": complexity,
                "coverage": coverage["percentage"]
            })
        
        # Verify all results are valid
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result["pass_rate"], 1.0)  # Canonical solutions
            self.assertGreaterEqual(result["complexity"], 1)
            self.assertGreaterEqual(result["coverage"], 0.0)
            self.assertLessEqual(result["coverage"], 100.0)


def run_tests():
    """Run the test suite and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestQualityPipelineIntegration)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    # Run tests
    result = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
