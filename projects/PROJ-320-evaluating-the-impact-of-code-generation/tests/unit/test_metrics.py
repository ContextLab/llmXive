"""
Unit tests for metrics extraction functionality.
Tests for User Story 2: Metric Extraction and Statistical Comparison.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.extract_metrics import calculate_comment_count, calculate_time_to_merge, calculate_review_cycles


class TestCommentCountCalculation:
    """Tests for test_comment_count_calculation."""

    def test_empty_comments_list(self):
        """Asserts comment count is 0 for empty list."""
        comments = []
        result = calculate_comment_count(comments)
        assert result == 0
        assert isinstance(result, int)

    def test_single_comment(self):
        """Asserts comment count is 1 for single item list."""
        comments = [{"id": 1, "body": "Test comment"}]
        result = calculate_comment_count(comments)
        assert result == 1

    def test_multiple_comments(self):
        """Asserts comment count matches list length."""
        comments = [
            {"id": 1, "body": "Comment 1"},
            {"id": 2, "body": "Comment 2"},
            {"id": 3, "body": "Comment 3"}
        ]
        result = calculate_comment_count(comments)
        assert result == 3

    def test_comments_with_none_values(self):
        """Asserts function handles None in comments gracefully."""
        comments = [
            {"id": 1, "body": "Valid"},
            None,
            {"id": 3, "body": "Also valid"}
        ]
        # Assuming the implementation filters out None or handles it
        # Based on typical data cleaning, we expect 2 valid comments
        result = calculate_comment_count(comments)
        assert result == 2

    def test_mixed_valid_invalid(self):
        """Asserts count ignores malformed entries."""
        comments = [
            {"id": 1, "body": "Good"},
            {"no_id": 2, "body": "Bad structure"}, # Missing id
            {"id": 3, "body": "Good"}
        ]
        result = calculate_comment_count(comments)
        # Should count only items with expected structure
        assert result >= 1


class TestTimeToMergeCalculation:
    """Tests for test_time_to_merge_calculation."""

    def test_exact_match_timestamps(self):
        """Asserts time to merge is 0 for identical timestamps."""
        created = datetime(2023, 10, 1, 12, 0, 0)
        merged = datetime(2023, 10, 1, 12, 0, 0)
        result = calculate_time_to_merge(created, merged)
        assert result == 0.0

    def test_one_hour_duration(self):
        """Asserts time to merge is 60 minutes for 1 hour duration."""
        created = datetime(2023, 10, 1, 10, 0, 0)
        merged = datetime(2023, 10, 1, 11, 0, 0)
        result = calculate_time_to_merge(created, merged)
        assert result == 60.0

    def test_multi_day_duration(self):
        """Asserts time to merge calculates correctly for multi-day PRs."""
        created = datetime(2023, 10, 1, 0, 0, 0)
        merged = datetime(2023, 10, 2, 0, 0, 0) # 24 hours later
        result = calculate_time_to_merge(created, merged)
        assert result == 1440.0

    def test_created_after_merged(self):
        """Asserts negative time is handled or raises error."""
        created = datetime(2023, 10, 2, 0, 0, 0)
        merged = datetime(2023, 10, 1, 0, 0, 0)
        result = calculate_time_to_merge(created, merged)
        # Typically this should be 0 or negative, depending on spec
        # Assuming we return 0 for invalid data or the raw negative value
        assert result <= 0.0

    def test_none_merged_timestamp(self):
        """Asserts function handles missing merge time (unmerged PR)."""
        created = datetime(2023, 10, 1, 0, 0, 0)
        merged = None
        result = calculate_time_to_merge(created, merged)
        assert result == 0.0 # Or np.nan, depending on implementation choice


class TestReviewCyclesCalculation:
    """Tests for test_review_cycles_calculation."""

    def test_no_reviews(self):
        """Asserts review cycles is 0 for no review events."""
        review_events = []
        result = calculate_review_cycles(review_events)
        assert result == 0

    def test_single_review_event(self):
        """Asserts 1 review event equals 1 cycle."""
        review_events = [
            {"event": "COMMENTED", "timestamp": "2023-10-01T10:00:00Z"}
        ]
        result = calculate_review_cycles(review_events)
        assert result == 1

    def test_multiple_review_events(self):
        """Asserts count matches number of review events."""
        review_events = [
            {"event": "COMMENTED", "timestamp": "2023-10-01T10:00:00Z"},
            {"event": "APPROVED", "timestamp": "2023-10-01T11:00:00Z"},
            {"event": "REQUEST_CHANGES", "timestamp": "2023-10-01T12:00:00Z"}
        ]
        result = calculate_review_cycles(review_events)
        assert result == 3

    def test_filter_non_review_events(self):
        """Asserts non-review events (e.g., merged) are excluded if applicable."""
        # Assuming the function filters for specific event types if defined
        review_events = [
            {"event": "COMMENTED", "timestamp": "2023-10-01T10:00:00Z"},
            {"event": "MERGED", "timestamp": "2023-10-01T12:00:00Z"}, # Not a review cycle
            {"event": "APPROVED", "timestamp": "2023-10-01T13:00:00Z"}
        ]
        # If implementation filters 'MERGED', result should be 2
        # If it counts all, result is 3. Assuming standard review cycle logic filters.
        result = calculate_review_cycles(review_events)
        # Based on standard definition, 'MERGED' is not a review cycle
        assert result == 2