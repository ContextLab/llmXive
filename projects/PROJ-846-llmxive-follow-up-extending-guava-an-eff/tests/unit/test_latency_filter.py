import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from analysis.latency_filter import (
    is_latency_failure, 
    filter_latency_failures, 
    load_categorized_outcomes,
    write_filtered_outcomes
)
from utils.config import get_path

class TestIsLatencyFailure:
    def test_success_outcome_returns_false(self):
        outcome = {"success": True, "failure_category": None}
        assert is_latency_failure(outcome) is False

    def test_non_latency_failure_returns_false(self):
        outcome = {"success": False, "failure_category": "perception"}
        assert is_latency_failure(outcome) is False

    def test_latency_failure_string_returns_true(self):
        outcome = {"success": False, "failure_category": "latency"}
        assert is_latency_failure(outcome) is True

    def test_latency_failure_list_returns_true(self):
        outcome = {"success": False, "failure_category": ["latency", "perception"]}
        assert is_latency_failure(outcome) is True

    def test_no_failure_category_returns_false(self):
        outcome = {"success": False}
        assert is_latency_failure(outcome) is False

class TestFilterLatencyFailures:
    def test_filters_correctly(self):
        outcomes = [
            {"success": True, "id": 1},
            {"success": False, "failure_category": "perception", "id": 2},
            {"success": False, "failure_category": "latency", "id": 3},
            {"success": False, "failure_category": "latency", "id": 4},
            {"success": False, "failure_category": "semantic", "id": 5},
        ]
        
        filtered = filter_latency_failures(outcomes)
        
        assert len(filtered) == 3
        ids = [item["id"] for item in filtered]
        assert 3 not in ids
        assert 4 not in ids
        assert 1 in ids
        assert 2 in ids
        assert 5 in ids

    def test_empty_list(self):
        assert filter_latency_failures([]) == []

    def test_all_latency_failures(self):
        outcomes = [
            {"success": False, "failure_category": "latency"},
            {"success": False, "failure_category": "latency"},
        ]
        assert len(filter_latency_failures(outcomes)) == 0

class TestWriteFilteredOutcomes:
    @patch('builtins.open')
    @patch('os.makedirs')
    @patch('utils.config.get_path')
    def test_writes_correct_files(self, mock_get_path, mock_makedirs, mock_open):
        mock_get_path.side_effect = [
            "data/processed/evaluation_outcomes.json",
            "data/processed/evaluation_outcomes_stats.json"
        ]
        
        filtered_outcomes = [{"id": 1, "success": True}]
        stats = {"total": 1, "excluded": 0}
        
        write_filtered_outcomes(filtered_outcomes, stats)
        
        assert mock_makedirs.called
        assert mock_open.call_count == 2
        
        # Verify first call (outcomes)
        call_args_0 = mock_open.call_args_list[0]
        assert "evaluation_outcomes.json" in str(call_args_0)
        
        # Verify second call (stats)
        call_args_1 = mock_open.call_args_list[1]
        assert "evaluation_outcomes_stats.json" in str(call_args_1)