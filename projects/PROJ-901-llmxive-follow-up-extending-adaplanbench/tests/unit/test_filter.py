"""
Unit tests for the filter logic in code/dataset/loader.py.
Verifies exclusion of tasks with <5 constraints.
"""
import pytest
from typing import List, Dict, Any

from dataset.loader import filter_progressive_constraints


class TestFilterProgressiveConstraints:
    """Tests for the filter_progressive_constraints function."""

    def test_filter_excludes_less_than_5(self):
        """Test that tasks with <5 constraints are excluded."""
        # Create mock data
        mock_data = [
            {"id": "t1", "progressive_constraints": ["c1", "c2", "c3"]},  # 3 constraints
            {"id": "t2", "progressive_constraints": ["c1", "c2", "c3", "c4"]},  # 4 constraints
            {"id": "t3", "progressive_constraints": ["c1", "c2", "c3", "c4", "c5"]},  # 5 constraints
            {"id": "t4", "progressive_constraints": ["c1", "c2", "c3", "c4", "c5", "c6"]},  # 6 constraints
        ]

        result = filter_progressive_constraints(mock_data, min_constraints=5)

        # Verify only t3 and t4 remain
        assert len(result) == 2
        ids = [item["id"] for item in result]
        assert "t3" in ids
        assert "t4" in ids
        assert "t1" not in ids
        assert "t2" not in ids

    def test_filter_includes_equal_to_5(self):
        """Test that tasks with exactly 5 constraints are included."""
        mock_data = [
            {"id": "t1", "progressive_constraints": ["c1", "c2", "c3", "c4", "c5"]},
        ]

        result = filter_progressive_constraints(mock_data, min_constraints=5)

        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_filter_custom_threshold(self):
        """Test filtering with a custom threshold."""
        mock_data = [
            {"id": "t1", "progressive_constraints": ["c1", "c2"]},
            {"id": "t2", "progressive_constraints": ["c1", "c2", "c3"]},
            {"id": "t3", "progressive_constraints": ["c1", "c2", "c3", "c4", "c5"]},
        ]

        result = filter_progressive_constraints(mock_data, min_constraints=3)

        assert len(result) == 2
        ids = [item["id"] for item in result]
        assert "t2" in ids
        assert "t3" in ids
        assert "t1" not in ids

    def test_filter_empty_constraints(self):
        """Test filtering when progressive_constraints is empty or null."""
        mock_data = [
            {"id": "t1", "progressive_constraints": []},
            {"id": "t2", "progressive_constraints": None},
            {"id": "t3", "progressive_constraints": ["c1"]},
        ]

        result = filter_progressive_constraints(mock_data, min_constraints=1)

        # Empty and None should be excluded
        assert len(result) == 0

    def test_filter_all_pass(self):
        """Test when all tasks pass the filter."""
        mock_data = [
            {"id": "t1", "progressive_constraints": ["c1", "c2", "c3", "c4", "c5"]},
            {"id": "t2", "progressive_constraints": ["c1", "c2", "c3", "c4", "c5", "c6"]},
        ]

        result = filter_progressive_constraints(mock_data, min_constraints=5)

        assert len(result) == 2

    def test_filter_none_pass(self):
        """Test when no tasks pass the filter."""
        mock_data = [
            {"id": "t1", "progressive_constraints": ["c1", "c2"]},
            {"id": "t2", "progressive_constraints": ["c1", "c2", "c3"]},
        ]

        result = filter_progressive_constraints(mock_data, min_constraints=5)

        assert len(result) == 0