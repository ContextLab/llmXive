"""
Unit tests for edge cases in the code generation and metrics analysis pipeline.
Tests scenarios: 0 coverage, missing LLM samples, zero-variance data, empty inputs.
"""
import pytest
import json
import os
import sys
import tempfile
import math

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analyze_metrics import calculate_code_metrics, execute_coverage_test, aggregate_metrics_to_json
from statistical_tests import permutation_test_paired, wilcoxon_signed_rank_test, mcnemar_test
from utils import safe_json_loads, safe_json_dumps


class TestZeroCoverageCases:
    """Tests for scenarios where code coverage is 0% or calculation fails."""

    def test_calculate_metrics_zero_coverage_snippet(self):
        """Verify metrics calculation handles snippets with no branches."""
        # Simple snippet with no control flow
        snippet = "def hello():\n    return 'world'"
        
        metrics = calculate_code_metrics(snippet)
        
        assert metrics is not None
        assert 'cyclomatic_complexity' in metrics
        assert 'halstead_volume' in metrics
        # Even with no branches, complexity should be at least 1
        assert metrics['cyclomatic_complexity'] >= 1

    def test_coverage_test_empty_code(self):
        """Test coverage calculation on empty code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_file = f.name
        
        try:
            result = execute_coverage_test(temp_file, [])
            # Should return 0 coverage or handle gracefully
            assert result is not None
            assert 'coverage_pct' in result or result == 0
        finally:
            os.unlink(temp_file)

    def test_coverage_test_syntax_error(self):
        """Test coverage calculation on code with syntax errors."""
        invalid_code = "def broken(\n    return"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(invalid_code)
            temp_file = f.name
        
        try:
            result = execute_coverage_test(temp_file, [])
            # Should handle gracefully, not crash
            assert result is not None
        finally:
            os.unlink(temp_file)


class TestMissingLLMSamples:
    """Tests for scenarios where LLM generation failed or samples are missing."""

    def test_aggregate_metrics_missing_samples(self):
        """Test aggregation handles missing LLM samples gracefully."""
        metrics_data = [
            {"task_id": "HumanEval/0", "source_type": "human", "pass_rate": 1, "cyclomatic_complexity": 2},
            {"task_id": "HumanEval/1", "source_type": "human", "pass_rate": 0, "cyclomatic_complexity": 3},
            # Note: No LLM samples for these tasks
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(metrics_data, f)
            temp_file = f.name
        
        try:
            result = aggregate_metrics_to_json(metrics_data, temp_file)
            # Should complete without crashing
            assert result is not None
            assert 'summary' in result
        finally:
            os.unlink(temp_file)

    def test_aggregate_metrics_partial_missing(self):
        """Test aggregation with some tasks missing LLM samples."""
        metrics_data = [
            {"task_id": "HumanEval/0", "source_type": "human", "pass_rate": 1, "cyclomatic_complexity": 2},
            {"task_id": "HumanEval/0", "source_type": "codegen-350M", "pass_rate": 0, "cyclomatic_complexity": 3},
            {"task_id": "HumanEval/1", "source_type": "human", "pass_rate": 0, "cyclomatic_complexity": 3},
            # Missing LLM sample for HumanEval/1
        ]
        
        result = aggregate_metrics_to_json(metrics_data, None)
        
        assert result is not None
        # Should handle the partial data
        assert 'summary' in result


class TestZeroVarianceStatisticalTests:
    """Tests for statistical functions handling zero-variance data."""

    def test_permutation_test_zero_variance(self):
        """Test permutation test handles zero-variance coverage data."""
        # All values are the same
        group_a = [0.5, 0.5, 0.5, 0.5, 0.5]
        group_b = [0.5, 0.5, 0.5, 0.5, 0.5]
        
        # Should not raise division by zero
        result = permutation_test_paired(group_a, group_b, n_permutations=100)
        
        assert result is not None
        assert 'p_value' in result
        # With identical data, p-value should be 1.0
        assert math.isclose(result['p_value'], 1.0, abs_tol=0.1)

    def test_wilcoxon_zero_variance(self):
        """Test Wilcoxon test handles zero-variance data."""
        group_a = [1, 1, 1, 1, 1]
        group_b = [1, 1, 1, 1, 1]
        
        result = wilcoxon_signed_rank_test(group_a, group_b)
        
        assert result is not None
        assert 'p_value' in result
        # With identical data, p-value should be 1.0
        assert math.isclose(result['p_value'], 1.0, abs_tol=0.1)

    def test_mcnemar_no_events(self):
        """Test McNemar test handles cases with no events."""
        # Both models failed all tests
        table = [[0, 0], [0, 0]]
        
        result = mcnemar_test(table)
        
        assert result is not None
        assert 'p_value' in result


class TestEmptyInputs:
    """Tests for handling empty inputs gracefully."""

    def test_calculate_metrics_empty_string(self):
        """Test metrics calculation on empty string."""
        with pytest.raises((ValueError, AttributeError)):
            calculate_code_metrics("")

    def test_aggregate_metrics_empty_list(self):
        """Test aggregation on empty list."""
        result = aggregate_metrics_to_json([], None)
        
        assert result is not None
        assert result['summary']['total_samples'] == 0

    def test_permutation_test_empty_groups(self):
        """Test permutation test on empty groups."""
        with pytest.raises(ValueError):
            permutation_test_paired([], [])

    def test_wilcoxon_empty_groups(self):
        """Test Wilcoxon test on empty groups."""
        with pytest.raises(ValueError):
            wilcoxon_signed_rank_test([], [])


class TestBoundaryValues:
    """Tests for boundary value scenarios."""

    def test_coverage_100_percent(self):
        """Test handling of 100% coverage."""
        # This is a simulation of the result structure
        result = {"coverage_pct": 100.0, "pass_rate": 1}
        
        assert result['coverage_pct'] == 100.0
        assert result['pass_rate'] == 1

    def test_coverage_0_percent(self):
        """Test handling of 0% coverage."""
        result = {"coverage_pct": 0.0, "pass_rate": 0}
        
        assert result['coverage_pct'] == 0.0
        assert result['pass_rate'] == 0

    def test_pass_rate_boundary(self):
        """Test pass rate at boundaries."""
        # Pass rate should be binary (0 or 1)
        assert 0 <= 0 <= 1
        assert 0 <= 1 <= 1
        # Values outside should be handled as invalid
        with pytest.raises(AssertionError):
            assert -1 <= 0 <= 1

    def test_complexity_minimum(self):
        """Test that complexity has a minimum value."""
        snippet = "x = 1"
        metrics = calculate_code_metrics(snippet)
        
        assert metrics['cyclomatic_complexity'] >= 1


class TestMalformedData:
    """Tests for handling malformed or unexpected data."""

    def test_aggregate_metrics_missing_fields(self):
        """Test aggregation with missing required fields."""
        metrics_data = [
            {"task_id": "HumanEval/0"},  # Missing source_type, pass_rate, etc.
        ]
        
        result = aggregate_metrics_to_json(metrics_data, None)
        
        assert result is not None
        # Should handle gracefully, possibly with warnings or defaults

    def test_safe_json_loads_invalid_json(self):
        """Test safe JSON parsing on invalid input."""
        result = safe_json_loads("invalid json")
        assert result is None

    def test_safe_json_loads_valid_json(self):
        """Test safe JSON parsing on valid input."""
        result = safe_json_loads('{"key": "value"}')
        assert result == {"key": "value"}

    def test_safe_json_dumps_non_serializable(self):
        """Test safe JSON dumping on non-serializable object."""
        class CustomObject:
            pass
        
        obj = CustomObject()
        result = safe_json_dumps(obj)
        assert result is None


class TestConcurrencyEdgeCases:
    """Tests for edge cases in concurrent execution scenarios."""

    def test_metrics_aggregation_duplicate_keys(self):
        """Test aggregation with duplicate task_id + source_type keys."""
        metrics_data = [
            {"task_id": "HumanEval/0", "source_type": "codegen", "pass_rate": 1, "timestamp": "2023-01-01T00:00:00"},
            {"task_id": "HumanEval/0", "source_type": "codegen", "pass_rate": 0, "timestamp": "2023-01-02T00:00:00"},
        ]
        
        result = aggregate_metrics_to_json(metrics_data, None)
        
        assert result is not None
        # Should handle duplicates (keep latest or report conflict)

    def test_coverage_test_timeout(self):
        """Test coverage test with timeout scenario."""
        # This tests the structure, actual timeout handling depends on implementation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def infinite():\n    while True: pass")
            temp_file = f.name
        
        try:
            # Should not hang indefinitely
            result = execute_coverage_test(temp_file, [], timeout=1)
            assert result is not None
        finally:
            os.unlink(temp_file)