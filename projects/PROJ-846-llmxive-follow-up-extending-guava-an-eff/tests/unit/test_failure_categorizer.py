"""
Unit tests for failure_categorizer.py

Tests the failure categorization logic independently of the full pipeline.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.failure_categorizer import (
    categorize_failure,
    categorize_all_failures,
    load_task_outcomes,
    load_perception_log
)
from utils.exceptions import LlmXiveError


class TestCategorizeFailure:
    """Tests for the categorize_failure function."""

    def test_success_outcome(self):
        """Test that successful tasks are categorized as 'success'."""
        outcome = {'success': True, 'task_id': 'test_1'}
        assert categorize_failure(outcome) == 'success'

    def test_latency_failure_explicit_category(self):
        """Test explicit latency failure category."""
        outcome = {
            'success': False,
            'failure_category': 'latency',
            'task_id': 'test_2'
        }
        assert categorize_failure(outcome) == 'latency'

    def test_latency_failure_by_reason(self):
        """Test latency failure detected by failure reason."""
        outcome = {
            'success': False,
            'failure_reason': 'Task exceeded latency threshold',
            'task_id': 'test_3'
        }
        assert categorize_failure(outcome) == 'latency'

    def test_perception_failure_missing_object(self):
        """Test perception failure when object is missing."""
        outcome = {
            'success': False,
            'failure_reason': 'Object not detected',
            'task_id': 'test_4'
        }
        perception_log = {
            'entries': [{
                'task_id': 'test_4',
                'object_missing_if_visible': True,
                'confidence_scores': [0.8]
            }]
        }
        assert categorize_failure(outcome, perception_log) == 'perception'

    def test_perception_failure_low_confidence(self):
        """Test perception failure with low confidence scores."""
        outcome = {
            'success': False,
            'failure_reason': 'Detection failed',
            'task_id': 'test_5'
        }
        perception_log = {
            'entries': [{
                'task_id': 'test_5',
                'object_missing_if_visible': False,
                'confidence_scores': [0.2, 0.3]  # Average < 0.5
            }]
        }
        assert categorize_failure(outcome, perception_log) == 'perception'

    def test_perception_failure_by_reason(self):
        """Test perception failure detected by failure reason keywords."""
        outcome = {
            'success': False,
            'failure_reason': 'Perception module failed to detect object',
            'task_id': 'test_6'
        }
        assert categorize_failure(outcome) == 'perception'

    def test_geometric_failure_by_reason(self):
        """Test geometric failure detected by failure reason keywords."""
        outcome = {
            'success': False,
            'failure_reason': 'Collision detected during navigation',
            'task_id': 'test_7'
        }
        assert categorize_failure(outcome) == 'geometric'

    def test_semantic_failure_by_reason(self):
        """Test semantic failure detected by failure reason keywords."""
        outcome = {
            'success': False,
            'failure_reason': 'Incorrect object identification',
            'task_id': 'test_8'
        }
        assert categorize_failure(outcome) == 'semantic'

    def test_geometric_by_action_type(self):
        """Test geometric categorization based on action type."""
        outcome = {
            'success': False,
            'action_type': 'navigate_to_location',
            'task_id': 'test_9'
        }
        assert categorize_failure(outcome) == 'geometric'

    def test_semantic_by_action_type(self):
        """Test semantic categorization based on action type."""
        outcome = {
            'success': False,
            'action_type': 'pick_object',
            'task_id': 'test_10'
        }
        assert categorize_failure(outcome) == 'semantic'

    def test_default_to_semantic(self):
        """Test that unknown failures default to semantic."""
        outcome = {
            'success': False,
            'failure_reason': 'Unknown error occurred',
            'task_id': 'test_11'
        }
        assert categorize_failure(outcome) == 'semantic'


class TestCategorizeAllFailures:
    """Tests for the categorize_all_failures function."""

    @pytest.fixture
    def temp_outcomes_file(self, tmp_path):
        """Create a temporary outcomes file for testing."""
        outcomes = [
            {'success': True, 'task_id': 't1'},
            {'success': False, 'failure_category': 'latency', 'task_id': 't2'},
            {'success': False, 'failure_reason': 'Object not detected', 'task_id': 't3'},
            {'success': False, 'failure_reason': 'Collision detected', 'task_id': 't4'},
            {'success': False, 'failure_reason': 'Wrong object', 'task_id': 't5'}
        ]
        file_path = tmp_path / "evaluation_outcomes.json"
        with open(file_path, 'w') as f:
            json.dump(outcomes, f)
        return file_path

    @pytest.fixture
    def temp_perception_log(self, tmp_path):
        """Create a temporary perception log for testing."""
        log = {
            'entries': [
                {'task_id': 't3', 'object_missing_if_visible': True, 'confidence_scores': [0.9]}
            ]
        }
        file_path = tmp_path / "perception_log.json"
        with open(file_path, 'w') as f:
            json.dump(log, f)
        return file_path

    def test_categorize_all_failures(self, temp_outcomes_file, temp_perception_log):
        """Test full categorization pipeline."""
        result = categorize_all_failures(temp_outcomes_file, temp_perception_log)

        assert 'categorized_outcomes' in result
        assert 'statistics' in result

        stats = result['statistics']
        assert stats['total_tasks'] == 5
        assert stats['total_failures'] == 4
        assert stats['success_rate'] == 0.2

        # Check failure distribution
        dist = stats['failure_distribution']
        assert dist['success'] == 1
        assert dist['latency'] == 1
        assert dist['perception'] == 1
        assert dist['geometric'] == 1
        assert dist['semantic'] == 1

    def test_categorize_all_failures_missing_perception_log(self, temp_outcomes_file):
        """Test categorization without perception log."""
        result = categorize_all_failures(temp_outcomes_file, None)

        assert 'categorized_outcomes' in result
        assert result['statistics']['total_tasks'] == 5

    def test_categorize_all_failures_empty_outcomes(self, tmp_path):
        """Test with empty outcomes list."""
        file_path = tmp_path / "empty_outcomes.json"
        with open(file_path, 'w') as f:
            json.dump([], f)

        result = categorize_all_failures(file_path)
        assert result['statistics']['total_tasks'] == 0
        assert result['statistics']['success_rate'] == 0


class TestLoadTaskOutcomes:
    """Tests for load_task_outcomes function."""

    def test_load_list_format(self, tmp_path):
        """Test loading outcomes in list format."""
        outcomes = [{'success': True}, {'success': False}]
        file_path = tmp_path / "outcomes.json"
        with open(file_path, 'w') as f:
            json.dump(outcomes, f)

        result = load_task_outcomes(file_path)
        assert len(result) == 2
        assert result[0]['success'] is True

    def test_load_dict_format(self, tmp_path):
        """Test loading outcomes in dict with 'outcomes' key."""
        data = {'outcomes': [{'success': True}]}
        file_path = tmp_path / "outcomes.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)

        result = load_task_outcomes(file_path)
        assert len(result) == 1

    def test_load_missing_file(self, tmp_path):
        """Test loading from non-existent file."""
        file_path = tmp_path / "missing.json"
        with pytest.raises(LlmXiveError):
            load_task_outcomes(file_path)

    def test_load_invalid_format(self, tmp_path):
        """Test loading invalid JSON format."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            json.dump({'key': 'value'}, f)  # Not a list or dict with 'outcomes'

        with pytest.raises(LlmXiveError):
            load_task_outcomes(file_path)


class TestLoadPerceptionLog:
    """Tests for load_perception_log function."""

    def test_load_perception_log(self, tmp_path):
        """Test loading perception log."""
        log = {'entries': [{'task_id': 't1'}]}
        file_path = tmp_path / "perception.json"
        with open(file_path, 'w') as f:
            json.dump(log, f)

        result = load_perception_log(file_path)
        assert 'entries' in result
        assert len(result['entries']) == 1

    def test_load_missing_perception_log(self, tmp_path):
        """Test loading non-existent perception log."""
        file_path = tmp_path / "missing.json"
        with pytest.raises(LlmXiveError):
            load_perception_log(file_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])