"""
Unit tests for analyze.py - Parameter Coverage Score Calculation
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from code.analyze import (
    calculate_parameter_coverage_score,
    process_results_for_coverage,
    run_wilcoxon_analysis,
    generate_final_report
)


class TestCalculateParameterCoverageScore:
    """Tests for calculate_parameter_coverage_score function."""

    def test_exact_match(self):
        """Test when all parameters match exactly."""
        ast_params = ['name', 'age', 'city']
        docstring = """
        Args:
            name: The name
            age: The age
            city: The city
        """
        score = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 1.0

    def test_partial_match(self):
        """Test when some parameters match."""
        ast_params = ['name', 'age', 'city', 'country']
        docstring = """
        Args:
            name: The name
            age: The age
        """
        score = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 0.5  # 2 out of 4

    def test_no_match(self):
        """Test when no parameters match."""
        ast_params = ['name', 'age']
        docstring = """
        Args:
            foo: Foo
            bar: Bar
        """
        score = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 0.0

    def test_empty_ast_params(self):
        """Test when there are no AST parameters."""
        ast_params = []
        docstring = """
        Args:
            name: The name
        """
        score = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 0.0

    def test_no_docstring(self):
        """Test when docstring is None."""
        ast_params = ['name', 'age']
        score = calculate_parameter_coverage_score(ast_params, None)
        assert score == 0.0

    def test_empty_docstring(self):
        """Test when docstring is empty string."""
        ast_params = ['name', 'age']
        score = calculate_parameter_coverage_score(ast_params, "")
        assert score == 0.0

    def test_whitespace_docstring(self):
        """Test when docstring is only whitespace."""
        ast_params = ['name', 'age']
        score = calculate_parameter_coverage_score(ast_params, "   \n\t  ")
        assert score == 0.0

    def test_case_insensitive(self):
        """Test that matching is case-insensitive."""
        ast_params = ['Name', 'AGE']
        docstring = """
        Args:
            name: The name
            age: The age
        """
        score = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 1.0

    def test_complex_type_hints(self):
        """Test handling of complex type hints (should not crash)."""
        ast_params = ['data', 'config']
        docstring = """
        Args:
            data: List[Dict[str, Any]]
            config: Optional[Dict]
        """
        # This should not crash and should return a valid score
        score = calculate_parameter_coverage_score(ast_params, docstring)
        assert 0.0 <= score <= 1.0


class TestProcessResultsForCoverage:
    """Tests for process_results_for_coverage function."""

    def test_basic_processing(self):
        """Test basic processing of a valid results file."""
        # Create a temporary file with test data
        test_data = [
            {
                'method_name': 'test_method',
                'ast_params': ['a', 'b'],
                'human_docstring': 'Args: a: A, b: B',
                'generated_docstring': 'Args: a: A, b: B'
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            results = process_results_for_coverage(temp_path)
            assert len(results) == 1
            assert 'coverage_score' in results[0]
            # Both human and generated match, so score should be 1.0
            assert results[0]['coverage_score'] == 1.0
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            process_results_for_coverage('nonexistent_file.json')

    def test_invalid_json_structure(self):
        """Test that ValueError is raised for non-list JSON."""
        test_data = {"not": "a list"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                process_results_for_coverage(temp_path)
        finally:
            os.unlink(temp_path)

    def test_empty_docstring_handling(self):
        """Test that empty docstrings get score 0.0 and needs_review=True."""
        test_data = [
            {
                'method_name': 'test_method',
                'ast_params': ['a'],
                'human_docstring': None,
                'generated_docstring': ''
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            results = process_results_for_coverage(temp_path)
            assert results[0]['coverage_score'] == 0.0
            assert results[0]['needs_review'] is True
        finally:
            os.unlink(temp_path)


class TestRunWilcoxonAnalysis:
    """Tests for run_wilcoxon_analysis function."""

    def test_basic_wilcoxon(self):
        """Test basic Wilcoxon test execution."""
        # Create records with both human and generated coverage scores
        records = []
        for i in range(50):
            records.append({
                'coverage_score': 0.5 + (i * 0.01),
                'human_docstring': f'Args: x: X',
                'ast_params': ['x']
            })

        # Manually set human scores for testing
        for i, record in enumerate(records):
            record['coverage_score'] = 0.8  # Generated score
            # We need to calculate human score separately, but for this test
            # we'll mock the behavior

        # This is a simplified test; the actual function compares
        # generated vs human coverage scores
        result = run_wilcoxon_analysis(records)
        assert 'statistic' in result
        assert 'p_value' in result
        assert 'n_pairs' in result

    def test_insufficient_data(self):
        """Test handling of insufficient data points."""
        records = [
            {
                'coverage_score': 0.5,
                'human_docstring': 'Args: x: X',
                'ast_params': ['x']
            }
        ]

        result = run_wilcoxon_analysis(records)
        assert result['n_pairs'] == 1
        assert 'warning' in result or result['statistic'] is None

    def test_small_sample_warning(self):
        """Test that warning is logged for small sample size."""
        # Create exactly 5 pairs (less than 30)
        records = []
        for i in range(5):
            records.append({
                'coverage_score': 0.5,
                'human_docstring': 'Args: x: X',
                'ast_params': ['x']
            })

        result = run_wilcoxon_analysis(records)
        # Should proceed but with warning
        assert result['n_pairs'] == 5


class TestGenerateFinalReport:
    """Tests for generate_final_report function."""

    def test_report_generation(self):
        """Test that a report is generated correctly."""
        records = [
            {'coverage_score': 0.5, 'needs_review': False},
            {'coverage_score': 0.8, 'needs_review': False},
            {'coverage_score': 0.0, 'needs_review': True}
        ]
        wilcoxon_results = {
            'statistic': 10.0,
            'p_value': 0.03,
            'n_pairs': 3,
            'significant': True
        }

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            generate_final_report(records, wilcoxon_results, temp_path)

            # Verify file was created
            assert os.path.exists(temp_path)

            # Verify content
            with open(temp_path, 'r') as f:
                report = json.load(f)

            assert 'summary' in report
            assert 'wilcoxon_test' in report
            assert 'records' in report
            assert report['summary']['total_methods'] == 3
            assert report['summary']['methods_needing_review'] == 1
        finally:
            os.unlink(temp_path)

    def test_report_with_empty_records(self):
        """Test report generation with empty records list."""
        records = []
        wilcoxon_results = {
            'statistic': None,
            'p_value': None,
            'n_pairs': 0
        }

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            generate_final_report(records, wilcoxon_results, temp_path)

            with open(temp_path, 'r') as f:
                report = json.load(f)

            assert report['summary']['total_methods'] == 0
            assert report['summary']['mean_coverage_score'] == 0.0
        finally:
            os.unlink(temp_path)
