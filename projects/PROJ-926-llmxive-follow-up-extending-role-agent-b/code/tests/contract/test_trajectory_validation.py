"""
Contract test for trajectory validation logic in trajectory_generator.py.
Tests the validation filter functionality (T013b).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.sim.trajectory_generator import validate_and_filter_trajectories, extract_failure_reason

class TestTrajectoryValidation:
    """Contract tests for trajectory validation functionality."""

    def test_validate_trajectory_pass(self):
        """Test that valid trajectories pass validation."""
        # Mock ground-truth data
        ground_truth_data = {
            'task_1': {
                'expected_actions': ['pick up key', 'open door', 'go to room'],
                'success_states': ['room_opened', 'item_retrieved']
            }
        }
        
        # Valid trajectory
        valid_trajectory = {
            'trajectory_id': 'test-001',
            'task_id': 'task_1',
            'action_log': [
                {'action': 'pick up key', 'step': 1},
                {'action': 'open door', 'step': 2},
                {'action': 'go to room', 'step': 3}
            ],
            'state_transitions': ['start', 'key_picked', 'door_opened', 'room_entered']
        }
        
        trajectories = [valid_trajectory]
        valid_results, excluded_results = validate_and_filter_trajectories(
            trajectories, ground_truth_data
        )
        
        assert len(valid_results) == 1
        assert len(excluded_results) == 0
        assert valid_results[0]['validation_status'] == 'PASS'

    def test_validate_trajectory_fail(self):
        """Test that invalid trajectories are filtered out."""
        # Mock ground-truth data
        ground_truth_data = {
            'task_1': {
                'expected_actions': ['pick up key', 'open door'],
                'success_states': ['key_picked', 'door_opened']
            }
        }
        
        # Invalid trajectory (missing required action)
        invalid_trajectory = {
            'trajectory_id': 'test-002',
            'task_id': 'task_1',
            'action_log': [
                {'action': 'go to room', 'step': 1},
                {'action': 'pick up item', 'step': 2}
            ],
            'state_transitions': ['start', 'room_entered', 'item_picked']
        }
        
        trajectories = [invalid_trajectory]
        valid_results, excluded_results = validate_and_filter_trajectories(
            trajectories, ground_truth_data
        )
        
        assert len(valid_results) == 0
        assert len(excluded_results) == 1
        assert excluded_results[0]['trajectory_id'] == 'test-002'

    def test_extract_failure_reason_pattern_match(self):
        """Test failure reason extraction with pattern matching."""
        action_log = [
            {'action': 'go to kitchen', 'step': 1},
            {'action': 'failed to pick up apple after 3 steps', 'step': 2},
            {'action': 'timeout', 'step': 3}
        ]
        
        reason = extract_failure_reason(action_log)
        assert 'Pattern match' in reason or 'failed to pick up' in reason.lower()

    def test_extract_failure_reason_empty_log(self):
        """Test failure reason extraction with empty action log."""
        action_log = []
        reason = extract_failure_reason(action_log)
        assert 'Unknown' in reason
        assert 'Empty' in reason

    def test_extract_failure_reason_last_actions(self):
        """Test failure reason extraction using last actions."""
        action_log = [
            {'action': 'go to kitchen', 'step': 1},
            {'action': 'open drawer', 'step': 2},
            {'action': 'pick up spoon', 'step': 3}
        ]
        
        reason = extract_failure_reason(action_log)
        assert 'Last actions' in reason

    def test_validate_and_filter_mixed_trajectories(self):
        """Test validation with a mix of valid and invalid trajectories."""
        ground_truth_data = {
            'task_1': {
                'expected_actions': ['pick up key'],
                'success_states': ['key_picked']
            }
        }
        
        valid_traj = {
            'trajectory_id': 'test-003',
            'task_id': 'task_1',
            'action_log': [{'action': 'pick up key', 'step': 1}],
            'state_transitions': ['start', 'key_picked']
        }
        
        invalid_traj = {
            'trajectory_id': 'test-004',
            'task_id': 'task_1',
            'action_log': [{'action': 'go to room', 'step': 1}],
            'state_transitions': ['start', 'room_entered']
        }
        
        trajectories = [valid_traj, invalid_traj]
        valid_results, excluded_results = validate_and_filter_trajectories(
            trajectories, ground_truth_data
        )
        
        assert len(valid_results) == 1
        assert len(excluded_results) == 1
        assert valid_results[0]['trajectory_id'] == 'test-003'
        assert excluded_results[0]['trajectory_id'] == 'test-004'

    def test_validation_preserves_trajectory_metadata(self):
        """Test that validation preserves original trajectory metadata."""
        ground_truth_data = {
            'task_1': {
                'expected_actions': ['pick up key'],
                'success_states': ['key_picked']
            }
        }
        
        trajectory = {
            'trajectory_id': 'test-005',
            'task_id': 'task_1',
            'condition': 'baseline',
            'action_log': [{'action': 'pick up key', 'step': 1}],
            'state_transitions': ['start', 'key_picked'],
            'custom_field': 'custom_value'
        }
        
        trajectories = [trajectory]
        valid_results, _ = validate_and_filter_trajectories(
            trajectories, ground_truth_data
        )
        
        assert len(valid_results) == 1
        assert valid_results[0]['custom_field'] == 'custom_value'
        assert valid_results[0]['condition'] == 'baseline'
        assert 'validation_status' in valid_results[0]
        assert 'validation_timestamp' in valid_results[0]
