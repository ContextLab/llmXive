"""
Unit tests for T032: regression_summary.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Ensure the project root is in the path
import sys
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from stats.regression_summary import analyze_age_groups, generate_summary, OLD_AGE_THRESHOLD, MIN_OLD_AGE_COUNT

class TestAgeGroupAnalysis:
    def test_correct_counting(self):
        """Test that age groups are counted correctly."""
        records = [
            {"age": 25},
            {"age": 40},
            {"age": 65},
            {"age": 70},
            {"age": 80}
        ]
        counts = analyze_age_groups(records)
        assert counts["young_count"] == 2
        assert counts["older_count"] == 3
        assert counts["total_count"] == 5

    def test_boundary_condition(self):
        """Test that age 65 is included in Older group."""
        records = [
            {"age": 64.9},
            {"age": 65.0},
            {"age": 65.1}
        ]
        counts = analyze_age_groups(records)
        assert counts["young_count"] == 1
        assert counts["older_count"] == 2

    def test_missing_age(self):
        """Test handling of missing age values."""
        records = [
            {"age": 25},
            {"age": None},
            {"age": 70}
        ]
        counts = analyze_age_groups(records)
        # None should be skipped
        assert counts["young_count"] == 1
        assert counts["older_count"] == 1
        assert counts["total_count"] == 2

    def test_invalid_age(self):
        """Test handling of invalid age values."""
        records = [
            {"age": 25},
            {"age": "invalid"},
            {"age": 70}
        ]
        counts = analyze_age_groups(records)
        # Invalid string should be skipped
        assert counts["young_count"] == 1
        assert counts["older_count"] == 1
        assert counts["total_count"] == 2

class TestSummaryGeneration:
    def test_no_warnings_high_n(self):
        """Test that no warning is generated when N >= 15 for Older group."""
        age_counts = {
            "young_count": 50,
            "older_count": 20,
            "total_count": 70
        }
        summary = generate_summary(age_counts)
        assert summary["warnings"] == []
        assert "Low Power for Older Group" not in summary["warnings"]

    def test_warning_generated_low_n(self):
        """Test that warning is generated when N < 15 for Older group."""
        age_counts = {
            "young_count": 50,
            "older_count": 10,
            "total_count": 60
        }
        summary = generate_summary(age_counts)
        assert "Low Power for Older Group" in summary["warnings"]
        assert summary["warnings"] == ["Low Power for Older Group"]

    def test_boundary_warning(self):
        """Test warning at boundary (N=14)."""
        age_counts = {
            "young_count": 50,
            "older_count": 14,
            "total_count": 64
        }
        summary = generate_summary(age_counts)
        assert "Low Power for Older Group" in summary["warnings"]

    def test_structure(self):
        """Test the structure of the generated summary."""
        age_counts = {
            "young_count": 10,
            "older_count": 5,
            "total_count": 15
        }
        summary = generate_summary(age_counts)
        
        assert "warnings" in summary
        assert "age_group_counts" in summary
        assert "threshold_old_age" in summary
        assert "min_required_old_count" in summary
        assert summary["threshold_old_age"] == OLD_AGE_THRESHOLD
        assert summary["min_required_old_count"] == MIN_OLD_AGE_COUNT