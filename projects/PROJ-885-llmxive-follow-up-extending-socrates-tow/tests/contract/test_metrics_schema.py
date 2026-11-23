"""
Contract tests for the metrics output schema.

These tests verify that the gap closure metrics output conforms to the
expected schema required by downstream statistical analysis (T038).
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest


@pytest.fixture
def sample_metrics_report() -> Dict[str, Any]:
    """Create a sample metrics report for testing."""
    return {
        'generated_at': '2024-01-15T10:30:00',
        'summary': {
            'total_trajectories': 10,
            'adapter_count': 10,
            'static_count': 10,
            'avg_gap_closure_adapter': 0.25,
            'avg_gap_closure_static': 0.10,
            'improvement_rate_adapter': 80.0,
            'improvement_rate_static': 60.0,
            'gap_closure_difference': 0.15
        },
        'trajectory_metrics': [
            {
                'trajectory_id': 'traj-001',
                'condition': 'Adapter',
                'initial_gap': 0.8,
                'final_gap': 0.5,
                'gap_closure': 0.3,
                'gap_closure_percent': 37.5,
                'is_improved': True
            },
            {
                'trajectory_id': 'traj-001',
                'condition': 'Static',
                'initial_gap': 0.8,
                'final_gap': 0.65,
                'gap_closure': 0.15,
                'gap_closure_percent': 18.75,
                'is_improved': True
            }
        ]
    }


def test_metrics_report_has_required_top_level_keys(report: Dict[str, Any]) -> None:
    """Verify the report contains all required top-level keys."""
    required_keys = {'generated_at', 'summary', 'trajectory_metrics'}
    assert required_keys.issubset(set(report.keys())), \
        f"Missing required top-level keys: {required_keys - set(report.keys())}"


def test_summary_has_required_fields(summary: Dict[str, Any]) -> None:
    """Verify the summary section contains all required fields."""
    required_fields = {
        'total_trajectories',
        'adapter_count',
        'static_count',
        'avg_gap_closure_adapter',
        'avg_gap_closure_static',
        'improvement_rate_adapter',
        'improvement_rate_static',
        'gap_closure_difference'
    }
    assert required_fields.issubset(set(summary.keys())), \
        f"Missing required summary fields: {required_fields - set(summary.keys())}"


def test_trajectory_metrics_is_list(metrics: List[Dict[str, Any]]) -> None:
    """Verify trajectory_metrics is a list."""
    assert isinstance(metrics, list), "trajectory_metrics must be a list"


def test_each_metric_has_required_fields(metrics: List[Dict[str, Any]]) -> None:
    """Verify each trajectory metric has all required fields."""
    required_fields = {
        'trajectory_id',
        'condition',
        'initial_gap',
        'final_gap',
        'gap_closure',
        'gap_closure_percent',
        'is_improved'
    }

    for i, metric in enumerate(metrics):
        missing = required_fields - set(metric.keys())
        assert not missing, \
            f"Metric {i} missing required fields: {missing}"


def test_condition_values_are_valid(metrics: List[Dict[str, Any]]) -> None:
    """Verify condition values are either 'Adapter' or 'Static'."""
    valid_conditions = {'Adapter', 'Static'}
    for metric in metrics:
        assert metric['condition'] in valid_conditions, \
            f"Invalid condition value: {metric['condition']}"


def test_numeric_fields_are_numbers(metrics: List[Dict[str, Any]]) -> None:
    """Verify numeric fields contain numeric values."""
    numeric_fields = ['initial_gap', 'final_gap', 'gap_closure', 'gap_closure_percent']

    for metric in metrics:
        for field in numeric_fields:
            assert isinstance(metric[field], (int, float)), \
                f"Field {field} must be numeric, got {type(metric[field])}"


def test_is_improved_is_boolean(metrics: List[Dict[str, Any]]) -> None:
    """Verify is_improved field is a boolean."""
    for metric in metrics:
        assert isinstance(metric['is_improved'], bool), \
            f"is_improved must be boolean, got {type(metric['is_improved'])}"


def test_gap_closure_consistency(metrics: List[Dict[str, Any]]) -> None:
    """Verify gap_closure = initial_gap - final_gap."""
    for metric in metrics:
        expected_closure = metric['initial_gap'] - metric['final_gap']
        assert abs(metric['gap_closure'] - expected_closure) < 1e-6, \
            f"Gap closure mismatch: {metric['gap_closure']} != {expected_closure}"


def test_improvement_flag_consistency(metrics: List[Dict[str, Any]]) -> None:
    """Verify is_improved is True when gap_closure > 0."""
    for metric in metrics:
        expected_improved = metric['gap_closure'] > 0
        assert metric['is_improved'] == expected_improved, \
            f"is_improved mismatch for gap_closure {metric['gap_closure']}"


def test_summary_consistency_with_metrics(
    summary: Dict[str, Any],
    metrics: List[Dict[str, Any]]
) -> None:
    """Verify summary statistics are consistent with individual metrics."""
    adapter_metrics = [m for m in metrics if m['condition'] == 'Adapter']
    static_metrics = [m for m in metrics if m['condition'] == 'Static']

    # Check counts
    assert summary['adapter_count'] == len(adapter_metrics), \
        f"Adapter count mismatch: {summary['adapter_count']} != {len(adapter_metrics)}"
    assert summary['static_count'] == len(static_metrics), \
        f"Static count mismatch: {summary['static_count']} != {len(static_metrics)}"

    # Check average gap closure for adapter
    if adapter_metrics:
        expected_avg_adapter = sum(m['gap_closure'] for m in adapter_metrics) / len(adapter_metrics)
        assert abs(summary['avg_gap_closure_adapter'] - expected_avg_adapter) < 1e-6, \
            f"Adapter avg gap closure mismatch"

    # Check average gap closure for static
    if static_metrics:
        expected_avg_static = sum(m['gap_closure'] for m in static_metrics) / len(static_metrics)
        assert abs(summary['avg_gap_closure_static'] - expected_avg_static) < 1e-6, \
            f"Static avg gap closure mismatch"


# Fixtures to load the actual output file if it exists
@pytest.fixture
def report_path() -> Path:
    return Path('data/results/gap_closure_metrics.json')


@pytest.fixture
def report(report_path: Path) -> Dict[str, Any]:
    """Load the actual metrics report from disk."""
    if not report_path.exists():
        pytest.skip(f"Metrics report not found at {report_path}")

    with open(report_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def summary(report: Dict[str, Any]) -> Dict[str, Any]:
    return report['summary']


@pytest.fixture
def metrics(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    return report['trajectory_metrics']
