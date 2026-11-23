"""
tests/unit/test_baseline_agent.py
Unit tests for the Static Multi-Query Baseline agent (T022).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.base import run_baseline, execute_static_query, load_curated_dataset
from config import get_config_summary

class TestBaselineAgent:
    """Tests for the static baseline agent logic."""

    def test_execute_static_query_structure(self):
        """Test that execute_static_query returns the expected structure."""
        mock_issue = {
            "issue_id": "test-123",
            "title": "Test Issue",
            "ground_truth_lines": [10, 20, 30]
        }
        config = get_config_summary()
        
        result = execute_static_query(mock_issue, 0, config)
        
        assert "query_index" in result
        assert result["query_index"] == 0
        assert "retrieved_context_ids" in result
        assert isinstance(result["retrieved_context_ids"], list)
        assert "raw_query" in result
        assert "static_analysis_signals" in result
        
        # Check that ground truth lines are represented in retrieved context
        expected_ids = [f"line_{i}" for i in mock_issue["ground_truth_lines"]]
        for eid in expected_ids:
            assert eid in result["retrieved_context_ids"]

    def test_run_baseline_metrics_calculation(self):
        """Test that run_baseline calculates coverage and ranking correctly."""
        mock_issue = {
            "issue_id": "test-456",
            "title": "Missing Import",
            "ground_truth_lines": [5, 6, 7],
            "initial_coverage": 0.5
        }
        config = get_config_summary()
        
        log_entry = run_baseline(mock_issue, config)
        
        assert log_entry["issue_id"] == "test-456"
        assert log_entry["agent_type"] == "static_baseline"
        assert log_entry["query_count"] == 3  # NUM_PARALLEL_QUERIES
        assert "retrieved_context_ids" in log_entry
        assert "coverage_score" in log_entry
        assert "ranking_metric" in log_entry
        assert "query_history" in log_entry
        assert len(log_entry["query_history"]) == 3
        
        # Coverage should be between 0 and 1
        assert 0.0 <= log_entry["coverage_score"] <= 1.0

    def test_run_baseline_schema_compliance(self):
        """Test that the output log entry matches the expected schema fields."""
        mock_issue = {
            "issue_id": "test-schema",
            "title": "Schema Test",
            "ground_truth_lines": [1, 2]
        }
        config = get_config_summary()
        
        log_entry = run_baseline(mock_issue, config)
        
        # Required fields per agent_log_schema.yaml (inferred from task description)
        required_fields = [
            "issue_id",
            "query_count",
            "retrieved_context_ids",
            "coverage_score",
            "agent_type"
        ]
        
        for field in required_fields:
            assert field in log_entry, f"Missing required field: {field}"

    def test_load_curated_dataset_missing_file(self):
        """Test that load_curated_dataset raises error if file missing."""
        config = get_config_summary()
        # Override path to non-existent file
        config["paths"]["curated"] = "/nonexistent/path"
        
        with pytest.raises(FileNotFoundError):
            load_curated_dataset(config)