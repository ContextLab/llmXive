"""
Unit tests for T021b: Rubric execution and metrics collection.
"""
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the functions being tested
# Note: We import from the module where they are defined
from validation import (
    calculate_loc,
    calculate_cyclomatic_complexity,
    evaluate_repository_rubric,
    check_documentation_criteria
)

class TestMetricCalculations:
    def test_calculate_loc_simple(self):
        code = """
        def hello():
            print("Hello")
        """
        # Should count non-comment, non-blank lines
        assert calculate_loc(code) > 0

    def test_calculate_loc_ignore_comments(self):
        code = """
        # This is a comment
        
        x = 1
        """
        assert calculate_loc(code) == 1

    def test_calculate_cc_simple(self):
        code = """
        def f(x):
            if x > 0:
                return 1
            else:
                return 0
        """
        # Base 1 + 1 for if
        assert calculate_cyclomatic_complexity(code) == 2

    def test_calculate_cc_loop(self):
        code = """
        def f():
            for i in range(10):
                pass
        """
        # Base 1 + 1 for for
        assert calculate_cyclomatic_complexity(code) == 2

class TestRubricEvaluation:
    def test_evaluate_repository_rubric_pass(self):
        metrics = {'total_loc': 5000, 'avg_cc': 2.0}
        criteria = {'setup_instructions': True, 'api_ref': True, 'architecture': True}
        
        result = evaluate_repository_rubric("http://test.com", metrics, criteria)
        
        assert result['passed'] is True
        assert result['score'] >= 6

    def test_evaluate_repository_rubric_fail_loc(self):
        metrics = {'total_loc': 500, 'avg_cc': 2.0}
        criteria = {'setup_instructions': True, 'api_ref': True, 'architecture': True}
        
        result = evaluate_repository_rubric("http://test.com", metrics, criteria)
        
        # Fails LOC check
        assert result['passed'] is False
        assert result['details']['loc_ok'] is False

    def test_evaluate_repository_rubric_fail_docs(self):
        metrics = {'total_loc': 5000, 'avg_cc': 2.0}
        criteria = {'setup_instructions': False, 'api_ref': False, 'architecture': False}
        
        result = evaluate_repository_rubric("http://test.com", metrics, criteria)
        
        # Fails doc checks
        assert result['passed'] is False
        assert result['details']['setup_instructions'] is False

class TestDocumentationCriteria:
    def test_check_docs_with_readme(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            readme = os.path.join(tmpdir, 'README.md')
            with open(readme, 'w') as f:
                f.write("# Test")
            
            criteria = check_documentation_criteria(tmpdir)
            assert criteria['setup_instructions'] is True

    def test_check_docs_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            criteria = check_documentation_criteria(tmpdir)
            assert criteria['setup_instructions'] is False
            assert criteria['api_ref'] is False
            assert criteria['architecture'] is False
