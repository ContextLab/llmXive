"""
Unit tests for coverage metrics calculation.
"""
import pytest
import numpy as np
from code.metrics.coverage import (
    check_coverage,
    calculate_coverage_metrics,
    aggregate_coverage_by_method
)


class TestCheckCoverage:
    def test_true_inside_interval(self):
        assert check_coverage(0.0, 1.0, 0.5) is True
        assert check_coverage(-1.0, 1.0, 0.0) is True
        assert check_coverage(0.0, 1.0, 0.0) is True
        assert check_coverage(0.0, 1.0, 1.0) is True

    def test_true_outside_interval(self):
        assert check_coverage(0.0, 1.0, 1.1) is False
        assert check_coverage(0.0, 1.0, -0.1) is False
        assert check_coverage(2.0, 3.0, 1.0) is False

    def test_tolerance(self):
        # Test with values very close to boundaries
        assert check_coverage(0.0, 1.0, 1.0 + 1e-10) is True
        assert check_coverage(0.0, 1.0, 0.0 - 1e-10) is True
        assert check_coverage(0.0, 1.0, 1.0 + 1e-8) is False


class TestCalculateCoverageMetrics:
    def test_perfect_coverage(self):
        intervals = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]
        true_vals = [0.5, 0.5, 0.5]
        metrics = calculate_coverage_metrics(intervals, true_vals)
        assert metrics['coverage_rate'] == 1.0
        assert metrics['covered_count'] == 3
        assert metrics['total_evaluated'] == 3
        assert all(metrics['covered_flags'])

    def test_zero_coverage(self):
        intervals = [(0.0, 0.1), (0.0, 0.1), (0.0, 0.1)]
        true_vals = [0.5, 0.5, 0.5]
        metrics = calculate_coverage_metrics(intervals, true_vals)
        assert metrics['coverage_rate'] == 0.0
        assert metrics['covered_count'] == 0

    def test_partial_coverage(self):
        intervals = [(0.0, 1.0), (0.0, 0.1), (0.0, 1.0)]
        true_vals = [0.5, 0.5, 0.5]
        metrics = calculate_coverage_metrics(intervals, true_vals)
        assert metrics['coverage_rate'] == 2/3
        assert metrics['covered_count'] == 2

    def test_interval_widths(self):
        intervals = [(0.0, 2.0), (0.0, 4.0)]
        true_vals = [1.0, 2.0]
        metrics = calculate_coverage_metrics(intervals, true_vals)
        assert metrics['interval_widths'] == [2.0, 4.0]
        assert metrics['mean_width'] == 3.0

    def test_empty_input(self):
        metrics = calculate_coverage_metrics([], [])
        assert metrics['coverage_rate'] == 0.0
        assert metrics['total_evaluated'] == 0

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            calculate_coverage_metrics([(0.0, 1.0)], [0.5, 0.5])


class TestAggregateCoverageByMethod:
    def test_single_method(self):
        results = [
            {
                'method_id': 'OLS',
                'intervals': [(0.0, 1.0), (0.0, 1.0)],
                'true_values': [0.5, 0.5]
            }
        ]
        agg = aggregate_coverage_by_method(results)
        assert 'OLS' in agg
        assert agg['OLS']['coverage_rate'] == 1.0
        assert agg['OLS']['n_replications'] == 2

    def test_multiple_methods(self):
        results = [
            {
                'method_id': 'OLS',
                'intervals': [(0.0, 1.0)],
                'true_values': [0.5]
            },
            {
                'method_id': 'Bayesian',
                'intervals': [(0.0, 2.0)],
                'true_values': [1.0]
            }
        ]
        agg = aggregate_coverage_by_method(results)
        assert 'OLS' in agg
        assert 'Bayesian' in agg
        assert agg['OLS']['coverage_rate'] == 1.0
        assert agg['Bayesian']['coverage_rate'] == 1.0

    def test_mixed_coverage(self):
        results = [
            {
                'method_id': 'Bootstrap',
                'intervals': [(0.0, 0.1), (0.0, 1.0)],
                'true_values': [0.5, 0.5]
            }
        ]
        agg = aggregate_coverage_by_method(results)
        assert agg['Bootstrap']['coverage_rate'] == 0.5
        assert agg['Bootstrap']['n_replications'] == 2

    def test_missing_method_id(self):
        results = [
            {
                'intervals': [(0.0, 1.0)],
                'true_values': [0.5]
            }
        ]
        agg = aggregate_coverage_by_method(results)
        assert len(agg) == 0