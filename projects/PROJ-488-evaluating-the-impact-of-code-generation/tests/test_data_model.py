"""
Tests for data model schema validation (T024).
"""
import pytest
import sys
import os
from datetime import datetime

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_model import MetricResult, validate_metric_result

class TestMetricResultSchema:
    """Test cases for MetricResult schema compliance."""

    def test_valid_metric_result(self):
        """Test that a valid MetricResult passes validation."""
        result = MetricResult(
            snippet_id="test-001",
            group="human",
            metric_name="cyclomatic_complexity",
            value=5.5,
            source_tool="radon"
        )
        assert validate_metric_result(result) is True

    def test_valid_pylint_result(self):
        """Test that a valid pylint result passes validation."""
        result = MetricResult(
            snippet_id="test-002",
            group="llm",
            metric_name="bug_count",
            value=1.0,
            source_tool="pylint"
        )
        assert validate_metric_result(result) is True

    def test_invalid_group(self):
        """Test that an invalid group fails validation."""
        result = MetricResult(
            snippet_id="test-003",
            group="invalid",
            metric_name="test_metric",
            value=1.0,
            source_tool="radon"
        )
        assert validate_metric_result(result) is False

    def test_invalid_tool(self):
        """Test that an invalid tool fails validation."""
        result = MetricResult(
            snippet_id="test-004",
            group="human",
            metric_name="test_metric",
            value=1.0,
            source_tool="invalid_tool"
        )
        assert validate_metric_result(result) is False

    def test_missing_snippet_id(self):
        """Test that missing snippet_id fails validation."""
        result = MetricResult(
            snippet_id="",
            group="human",
            metric_name="test_metric",
            value=1.0,
            source_tool="radon"
        )
        assert validate_metric_result(result) is False

    def test_invalid_value_type(self):
        """Test that non-numeric value fails validation."""
        result = MetricResult(
            snippet_id="test-005",
            group="human",
            metric_name="test_metric",
            value="not_a_number",
            source_tool="radon"
        )
        assert validate_metric_result(result) is False

    def test_to_dict_serialization(self):
        """Test that to_dict produces expected keys."""
        result = MetricResult(
            snippet_id="test-006",
            group="llm",
            metric_name="maintainability_index",
            value=10.0,
            source_tool="radon"
        )
        d = result.to_dict()
        assert 'snippet_id' in d
        assert 'group' in d
        assert 'metric_name' in d
        assert 'value' in d
        assert 'source_tool' in d
        assert 'timestamp' in d

    def test_from_dict_creation(self):
        """Test that from_dict creates a valid instance."""
        data = {
            "snippet_id": "test-007",
            "group": "human",
            "metric_name": "test_metric",
            "value": 3.0,
            "source_tool": "pylint"
        }
        result = MetricResult.from_dict(data)
        assert result.snippet_id == "test-007"
        assert result.group == "human"
        assert validate_metric_result(result) is True

    def test_from_dict_missing_field(self):
        """Test that from_dict raises error on missing field."""
        data = {
            "snippet_id": "test-008",
            "group": "human",
            "value": 3.0,
            "source_tool": "pylint"
        }
        with pytest.raises(ValueError):
            MetricResult.from_dict(data)
