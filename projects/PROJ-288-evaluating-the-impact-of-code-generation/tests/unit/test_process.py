"""
Unit tests for outlier filtering logic in code/data/process.py.

Tests the apply_outlier_exclusion function to ensure it correctly:
1. Removes PRs with negative review times
2. Removes PRs with review times > 30 days (MAX_REVIEW_DAYS)
3. Preserves valid PRs within the acceptable range
"""
import pytest
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.process import apply_outlier_exclusion
from code.config import MAX_REVIEW_DAYS


def create_sample_pr(
    pr_number: int,
    first_review_time: Optional[float] = None,
    total_review_time: Optional[float] = None
) -> Dict[str, Any]:
    """Helper to create a sample PR dictionary for testing."""
    pr = {
        "pr_number": pr_number,
        "repo": "test/repo",
        "title": "Test PR",
        "author": "test_user",
        "lines_changed": 100,
        "origin_label": "Non-Disclosing",
        "first_review_time": first_review_time,
        "total_review_time": total_review_time
    }
    return pr


class TestOutlierExclusion:
    """Tests for the apply_outlier_exclusion function."""

    def test_removes_negative_first_review_time(self):
        """Test that PRs with negative first_review_time are removed."""
        prs = [
            create_sample_pr(1, first_review_time=-5.0, total_review_time=10.0),
            create_sample_pr(2, first_review_time=5.0, total_review_time=10.0),
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 1
        assert filtered_prs[0]["pr_number"] == 2
        assert removed_count == 1

    def test_removes_negative_total_review_time(self):
        """Test that PRs with negative total_review_time are removed."""
        prs = [
            create_sample_pr(1, first_review_time=5.0, total_review_time=-10.0),
            create_sample_pr(2, first_review_time=5.0, total_review_time=10.0),
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 1
        assert filtered_prs[0]["pr_number"] == 2
        assert removed_count == 1

    def test_removes_excessive_duration_first_review_time(self):
        """Test that PRs with first_review_time > MAX_REVIEW_DAYS are removed."""
        # MAX_REVIEW_DAYS is in days, convert to minutes (24 * 60 * MAX_REVIEW_DAYS)
        max_minutes = MAX_REVIEW_DAYS * 24 * 60
        excessive_time = max_minutes + 100
        
        prs = [
            create_sample_pr(1, first_review_time=excessive_time, total_review_time=excessive_time + 10),
            create_sample_pr(2, first_review_time=100.0, total_review_time=200.0),
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 1
        assert filtered_prs[0]["pr_number"] == 2
        assert removed_count == 1

    def test_removes_excessive_duration_total_review_time(self):
        """Test that PRs with total_review_time > MAX_REVIEW_DAYS are removed."""
        max_minutes = MAX_REVIEW_DAYS * 24 * 60
        excessive_time = max_minutes + 100
        
        prs = [
            create_sample_pr(1, first_review_time=100.0, total_review_time=excessive_time),
            create_sample_pr(2, first_review_time=100.0, total_review_time=200.0),
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 1
        assert filtered_prs[0]["pr_number"] == 2
        assert removed_count == 1

    def test_preserves_valid_prs(self):
        """Test that PRs within valid range are preserved."""
        prs = [
            create_sample_pr(1, first_review_time=10.0, total_review_time=20.0),
            create_sample_pr(2, first_review_time=50.0, total_review_time=100.0),
            create_sample_pr(3, first_review_time=0.0, total_review_time=0.0),  # Edge case: 0 is valid
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 3
        assert removed_count == 0
        assert {p["pr_number"] for p in filtered_prs} == {1, 2, 3}

    def test_handles_missing_review_times(self):
        """Test behavior when review times are None."""
        prs = [
            create_sample_pr(1, first_review_time=None, total_review_time=None),
            create_sample_pr(2, first_review_time=10.0, total_review_time=20.0),
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        # PRs with None values should be removed as they can't be validated
        assert len(filtered_prs) == 1
        assert filtered_prs[0]["pr_number"] == 2
        assert removed_count == 1

    def test_empty_input(self):
        """Test handling of empty input list."""
        prs = []
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 0
        assert removed_count == 0

    def test_all_prs_removed(self):
        """Test when all PRs are outliers."""
        prs = [
            create_sample_pr(1, first_review_time=-10.0, total_review_time=-20.0),
            create_sample_pr(2, first_review_time=100.0, total_review_time=100000.0),
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 0
        assert removed_count == 2

    def test_boundary_condition_exact_max_duration(self):
        """Test that PRs with exactly MAX_REVIEW_DAYS duration are kept."""
        max_minutes = MAX_REVIEW_DAYS * 24 * 60
        
        prs = [
            create_sample_pr(1, first_review_time=max_minutes, total_review_time=max_minutes),
            create_sample_pr(2, first_review_time=10.0, total_review_time=20.0),
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        # Exact boundary should be kept (<= MAX_REVIEW_DAYS)
        assert len(filtered_prs) == 2
        assert removed_count == 0

    def test_boundary_condition_just_over_max_duration(self):
        """Test that PRs just over MAX_REVIEW_DAYS are removed."""
        max_minutes = MAX_REVIEW_DAYS * 24 * 60
        
        prs = [
            create_sample_pr(1, first_review_time=max_minutes + 0.1, total_review_time=max_minutes + 0.1),
            create_sample_pr(2, first_review_time=10.0, total_review_time=20.0),
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 1
        assert filtered_prs[0]["pr_number"] == 2
        assert removed_count == 1

    def test_mixed_valid_and_invalid_prs(self):
        """Test filtering with a mix of valid and invalid PRs."""
        prs = [
            create_sample_pr(1, first_review_time=10.0, total_review_time=20.0),  # Valid
            create_sample_pr(2, first_review_time=-5.0, total_review_time=30.0),  # Invalid: negative first
            create_sample_pr(3, first_review_time=15.0, total_review_time=-10.0), # Invalid: negative total
            create_sample_pr(4, first_review_time=100.0, total_review_time=200.0), # Valid
            create_sample_pr(5, first_review_time=500000.0, total_review_time=600000.0), # Invalid: too large
            create_sample_pr(6, first_review_time=25.0, total_review_time=35.0),  # Valid
        ]
        
        filtered_prs, removed_count = apply_outlier_exclusion(prs)
        
        assert len(filtered_prs) == 3
        assert {p["pr_number"] for p in filtered_prs} == {1, 4, 6}
        assert removed_count == 3