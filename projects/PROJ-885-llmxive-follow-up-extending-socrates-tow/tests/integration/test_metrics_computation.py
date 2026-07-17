"""
Integration tests for the metrics computation pipeline.

These tests verify that the metrics computation correctly processes
experiment logs and produces accurate gap closure calculations.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

from analysis.metrics import (
    compute_all_trajectory_metrics,
    compute_summary_statistics,
    write_metrics_report,
    load_experiment_logs
)
from models.evaluator import ConsensusGapEvaluator


@pytest.fixture
def sample_experiment_logs() -> list:
    """Create sample experiment logs for testing."""
    return [
        {
            'trajectory_id': 'traj-001',
            'condition': 'Adapter',
            'turn_number': 1,
            'llm_output': 'I understand your concern. Let me try to address it.',
            'injected_state': 'de-escalate'
        },
        {
            'trajectory_id': 'traj-001',
            'condition': 'Adapter',
            'turn_number': 2,
            'llm_output': 'That makes sense. I see your perspective now.',
            'injected_state': 'validate_cultural_norms'
        },
        {
            'trajectory_id': 'traj-001',
            'condition': 'Static',
            'turn_number': 1,
            'llm_output': 'I hear what you are saying.',
            'injected_state': None
        },
        {
            'trajectory_id': 'traj-001',
            'condition': 'Static',
            'turn_number': 2,
            'llm_output': 'Let me think about that.',
            'injected_state': None
        },
        {
            'trajectory_id': 'traj-002',
            'condition': 'Adapter',
            'turn_number': 1,
            'llm_output': 'I appreciate your patience.',
            'injected_state': 'de-escalate'
        },
        {
            'trajectory_id': 'traj-002',
            'condition': 'Static',
            'turn_number': 1,
            'llm_output': 'Okay, I am listening.',
            'injected_state': None
        }
    ]


@pytest.fixture
def temp_logs_file(sample_experiment_logs: list) -> Path:
    """Create a temporary file with sample logs."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_experiment_logs, f)
        return Path(f.name)


def test_load_experiment_logs(temp_logs_file: Path) -> None:
    """Test loading experiment logs from file."""
    logs = load_experiment_logs(temp_logs_file)
    assert len(logs) == 6
    assert all('trajectory_id' in log for log in logs)


def test_compute_metrics_produces_results(
    temp_logs_file: Path,
    sample_experiment_logs: list
) -> None:
    """Test that metrics computation produces results for all trajectories."""
    evaluator = ConsensusGapEvaluator()
    metrics, summary = compute_all_trajectory_metrics(temp_logs_file, evaluator)

    assert len(metrics) > 0, "Should produce at least one metric entry"

    # Should have metrics for both conditions
    conditions = set(m.condition for m in metrics)
    assert 'Adapter' in conditions
    assert 'Static' in conditions

    # Should have metrics for both trajectories
    trajectory_ids = set(m.trajectory_id for m in metrics)
    assert 'traj-001' in trajectory_ids
    assert 'traj-002' in trajectory_ids


def test_summary_statistics_computation(temp_logs_file: Path) -> None:
    """Test that summary statistics are computed correctly."""
    evaluator = ConsensusGapEvaluator()
    metrics, summary = compute_all_trajectory_metrics(temp_logs_file, evaluator)

    assert summary['total_trajectories'] == 2
    assert summary['adapter_count'] > 0
    assert summary['static_count'] > 0

    # Gap closure difference should be computable
    assert summary['gap_closure_difference'] is not None


def test_metrics_output_schema(temp_logs_file: Path, tmp_path: Path) -> None:
    """Test that metrics output conforms to expected schema."""
    evaluator = ConsensusGapEvaluator()
    metrics, summary = compute_all_trajectory_metrics(temp_logs_file, evaluator)

    output_path = tmp_path / 'test_metrics.json'
    write_metrics_report(metrics, summary, output_path)

    assert output_path.exists()

    with open(output_path, 'r') as f:
        report = json.load(f)

    # Verify schema
    assert 'generated_at' in report
    assert 'summary' in report
    assert 'trajectory_metrics' in report
    assert isinstance(report['trajectory_metrics'], list)

    # Verify each metric has required fields
    for metric in report['trajectory_metrics']:
        assert 'trajectory_id' in metric
        assert 'condition' in metric
        assert 'initial_gap' in metric
        assert 'final_gap' in metric
        assert 'gap_closure' in metric
        assert 'gap_closure_percent' in metric
        assert 'is_improved' in metric


def test_empty_logs_file(tmp_path: Path) -> None:
    """Test handling of empty logs file."""
    empty_logs_path = tmp_path / 'empty_logs.json'
    empty_logs_path.write_text('[]')

    evaluator = ConsensusGapEvaluator()
    metrics, summary = compute_all_trajectory_metrics(empty_logs_path, evaluator)

    assert len(metrics) == 0
    assert summary['total_trajectories'] == 0
    assert summary['adapter_count'] == 0
    assert summary['static_count'] == 0