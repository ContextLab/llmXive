"""
Unit tests for code/stats/analyze_projection_loss.py
"""
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the module functions
from stats.analyze_projection_loss import (
    classify_failure_reason,
    run_projection_loss_analysis,
    CLASS_PROJECTION_LOSS,
    CLASS_ACTION_RESTRICTION,
    CLASS_OTHER
)


class TestClassifyFailureReason:
    def test_2d_success_no_classification(self):
        """If 2D succeeded, return OTHER (no failure)."""
        result_2d = {'success': True, 'task_type': 'occlusion'}
        result_baseline = {'success': False}
        gt = {}
        assert classify_failure_reason("t1", result_2d, result_baseline, gt) == CLASS_OTHER

    def test_2d_fail_baseline_success_occlusion(self):
        """2D failed, Baseline succeeded, Occlusion -> Projection Loss."""
        result_2d = {'success': False, 'task_type': 'occlusion'}
        result_baseline = {'success': True}
        gt = {'gt_3d_is_occluded': True}
        assert classify_failure_reason("t1", result_2d, result_baseline, gt) == CLASS_PROJECTION_LOSS

    def test_2d_fail_baseline_success_depth(self):
        """2D failed, Baseline succeeded, Depth -> Action Restriction."""
        result_2d = {'success': False, 'task_type': 'depth'}
        result_baseline = {'success': True}
        gt = {}
        assert classify_failure_reason("t1", result_2d, result_baseline, gt) == CLASS_ACTION_RESTRICTION

    def test_2d_fail_baseline_fail(self):
        """Both failed -> Other."""
        result_2d = {'success': False, 'task_type': 'occlusion'}
        result_baseline = {'success': False}
        gt = {}
        assert classify_failure_reason("t1", result_2d, result_baseline, gt) == CLASS_OTHER


class TestRunProjectionLossAnalysis:
    @pytest.fixture
    def mock_data(self):
        dataset = [
            {'task_id': 't1', 'task_type': 'occlusion', 'ground_truth_3d_params': {}},
            {'task_id': 't2', 'task_type': 'depth', 'ground_truth_3d_params': {}},
            {'task_id': 't3', 'task_type': 'occlusion', 'ground_truth_3d_params': {}},
        ]
        baseline = [
            {'task_id': 't1', 'success': True},
            {'task_id': 't2', 'success': True},
            {'task_id': 't3', 'success': False},
        ]
        agent_2d = [
            {'task_id': 't1', 'success': False, 'task_type': 'occlusion'},
            {'task_id': 't2', 'success': False, 'task_type': 'depth'},
            {'task_id': 't3', 'success': False, 'task_type': 'occlusion'},
        ]
        return dataset, baseline, agent_2d

    def test_analysis_counts(self, mock_data):
        dataset, baseline, agent_2d = mock_data
        stats = run_projection_loss_analysis(dataset, baseline, agent_2d)

        assert stats['total_tasks'] == 3
        assert stats['total_2d_failures'] == 3

        # t1: 2D Fail, Baseline Success, Occlusion -> Projection Loss
        # t2: 2D Fail, Baseline Success, Depth -> Action Restriction
        # t3: 2D Fail, Baseline Fail -> Other
        assert stats['breakdown'][CLASS_PROJECTION_LOSS] == 1
        assert stats['breakdown'][CLASS_ACTION_RESTRICTION] == 1
        assert stats['breakdown'][CLASS_OTHER] == 1

        # Check percentages
        assert stats['percentages'][CLASS_PROJECTION_LOSS] == pytest.approx(33.33, rel=0.1)
        assert stats['percentages'][CLASS_ACTION_RESTRICTION] == pytest.approx(33.33, rel=0.1)
        assert stats['percentages'][CLASS_OTHER] == pytest.approx(33.33, rel=0.1)
