"""
Unit tests for the Symbolic Planner.

These tests verify that the planner correctly handles:
- Normal constraint decomposition
- PARSE_FAILURE scenarios
- CONTRADICTION_DETECTED scenarios
- Integration with the exclusion logger
"""
import json
import os
import pytest
from pathlib import Path
from datetime import datetime

# Import from project API surface
from code.symbolic.planner import SymbolicPlanner, SubGoalStatus
from code.symbolic.exclusion_logger import ExclusionLogger, ExclusionEvent
from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED

@pytest.fixture
def sample_puzzle():
    """Provide a sample valid puzzle instance."""
    return {
        "metadata": {"source_id": "test_puzzle_001"},
        "constraints": [
            "A = 1",
            "B = 2",
            "A != B"
        ],
        "initial_state": {},
        "target_state": {}
    }

@pytest.fixture
def sample_contradictory_puzzle():
    """Provide a sample puzzle with contradictory constraints."""
    return {
        "metadata": {"source_id": "test_puzzle_contradiction"},
        "constraints": [
            "A = 1",
            "A = 2",
            "A != A"
        ],
        "initial_state": {},
        "target_state": {}
    }

@pytest.fixture
def sample_invalid_puzzle():
    """Provide a sample puzzle with invalid syntax."""
    return {
        "metadata": {"source_id": "test_puzzle_invalid"},
        "constraints": [
            "!!! invalid syntax !!!",
            "A = @#$%"
        ],
        "initial_state": {},
        "target_state": {}
    }

@pytest.fixture
def temp_exclusion_log(tmp_path):
    """Provide a temporary path for exclusion logging."""
    log_path = tmp_path / "exclusions.json"
    return log_path

def test_planner_decomposes_valid_puzzle(sample_puzzle, temp_exclusion_log):
    """Test that the planner successfully decomposes a valid puzzle."""
    exclusion_logger = ExclusionLogger(output_path=temp_exclusion_log)
    planner = SymbolicPlanner(exclusion_logger=exclusion_logger)
    
    result = planner.decompose(sample_puzzle)
    
    assert result.is_valid is True
    assert result.puzzle_id == "test_puzzle_001"
    assert len(result.sub_goals) > 0
    assert result.error_code is None
    assert result.error_message is None

def test_planner_handles_contradiction(sample_contradictory_puzzle, temp_exclusion_log):
    """Test that the planner detects and flags contradictions."""
    exclusion_logger = ExclusionLogger(output_path=temp_exclusion_log)
    planner = SymbolicPlanner(exclusion_logger=exclusion_logger)
    
    result = planner.decompose(sample_contradictory_puzzle)
    
    assert result.is_valid is False
    assert result.error_code == "CONTRADICTION_DETECTED"
    assert result.error_message is not None
    assert "Contradictory constraints" in result.error_message or "contradiction" in result.error_message.lower()
    
    # Verify exclusion was logged
    assert exclusion_logger.get_count() == 1
    events = exclusion_logger.get_events()
    assert events[0].reason == "CONTRADICTION_DETECTED"

def test_planner_handles_parse_failure(sample_invalid_puzzle, temp_exclusion_log):
    """Test that the planner handles parse failures correctly."""
    exclusion_logger = ExclusionLogger(output_path=temp_exclusion_log)
    planner = SymbolicPlanner(exclusion_logger=exclusion_logger)
    
    result = planner.decompose(sample_invalid_puzzle)
    
    assert result.is_valid is False
    assert result.error_code == "PARSE_FAILURE"
    assert result.error_message is not None
    
    # Verify exclusion was logged
    assert exclusion_logger.get_count() == 1
    events = exclusion_logger.get_events()
    assert events[0].reason == "PARSE_FAILURE"

def test_planner_integration_with_exclusion_logger(sample_contradictory_puzzle, temp_exclusion_log):
    """Test that the planner correctly integrates with the exclusion logger."""
    exclusion_logger = ExclusionLogger(output_path=temp_exclusion_log)
    planner = SymbolicPlanner(exclusion_logger=exclusion_logger)
    
    # Decompose a contradictory puzzle
    result = planner.decompose(sample_contradictory_puzzle)
    
    # Verify the exclusion log file exists and contains the event
    assert temp_exclusion_log.exists()
    
    with open(temp_exclusion_log, 'r') as f:
        log_data = json.load(f)
    
    assert isinstance(log_data, list)
    assert len(log_data) == 1
    assert log_data[0]['puzzle_id'] == "test_puzzle_contradiction"
    assert log_data[0]['reason'] == "CONTRADICTION_DETECTED"

def test_sub_goal_status_enum():
    """Test that SubGoalStatus enum values are correct."""
    assert SubGoalStatus.PENDING.value == "pending"
    assert SubGoalStatus.IN_PROGRESS.value == "in_progress"
    assert SubGoalStatus.COMPLETED.value == "completed"
    assert SubGoalStatus.FAILED.value == "failed"
    assert SubGoalStatus.CONTRADICTION.value == "contradiction"

def test_planner_empty_constraints(temp_exclusion_log):
    """Test that the planner handles empty constraints gracefully."""
    puzzle = {
        "metadata": {"source_id": "test_empty"},
        "constraints": [],
        "initial_state": {},
        "target_state": {}
    }
    
    exclusion_logger = ExclusionLogger(output_path=temp_exclusion_log)
    planner = SymbolicPlanner(exclusion_logger=exclusion_logger)
    
    result = planner.decompose(puzzle)
    
    # Should fail because no constraints were parsed
    assert result.is_valid is False
    assert result.error_code == "PARSE_FAILURE"