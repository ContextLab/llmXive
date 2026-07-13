"""
Unit tests for timestamp extraction functionality.
"""
import pytest
from datetime import datetime, timedelta
from code.feature_extraction.timestamps import (
    parse_iso_date_safe,
    calculate_review_duration,
    extract_timestamps_from_pr
)

class TestParseIsoDateSafe:
    def test_valid_iso_date(self):
        date_str = "2023-01-15T10:30:00Z"
        result = parse_iso_date_safe(date_str)
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_none_input(self):
        result = parse_iso_date_safe(None)
        assert result is None

    def test_empty_string(self):
        result = parse_iso_date_safe("")
        assert result is None

    def test_invalid_format(self):
        result = parse_iso_date_safe("not-a-date")
        assert result is None

class TestCalculateReviewDuration:
    def test_with_first_comment(self):
        created = "2023-01-15T10:00:00Z"
        first_comment = "2023-01-15T12:30:00Z"
        merged = "2023-01-16T10:00:00Z"

        duration = calculate_review_duration(created, first_comment, merged)
        assert duration is not None
        # Should use first comment: 2.5 hours
        assert abs(duration - 2.5) < 0.01

    def test_without_comment_uses_merge(self):
        created = "2023-01-15T10:00:00Z"
        first_comment = None
        merged = "2023-01-15T14:00:00Z"

        duration = calculate_review_duration(created, first_comment, merged)
        assert duration is not None
        # Should use merge: 4 hours
        assert abs(duration - 4.0) < 0.01

    def test_missing_created_at(self):
        duration = calculate_review_duration(None, "2023-01-15T12:00:00Z", "2023-01-15T14:00:00Z")
        assert duration is None

    def test_missing_comment_and_merge(self):
        duration = calculate_review_duration("2023-01-15T10:00:00Z", None, None)
        assert duration is None

    def test_end_before_start(self):
        created = "2023-01-15T14:00:00Z"
        first_comment = "2023-01-15T10:00:00Z"
        merged = "2023-01-15T12:00:00Z"

        duration = calculate_review_duration(created, first_comment, merged)
        assert duration is None

class TestExtractTimestampsFromPr:
    def test_full_extraction(self):
        pr_data = {
            'pr_id': 'PR-123',
            'created_at': '2023-01-15T10:00:00Z',
            'first_comment_at': '2023-01-15T11:00:00Z',
            'merged_at': '2023-01-15T15:00:00Z'
        }

        duration, metadata = extract_timestamps_from_pr(pr_data)

        assert duration is not None
        assert abs(duration - 1.0) < 0.01
        assert metadata['pr_id'] == 'PR-123'
        assert metadata['duration_hours'] == duration
        assert 'calculation_note' in metadata

    def test_missing_first_comment(self):
        pr_data = {
            'pr_id': 'PR-456',
            'created_at': '2023-01-15T10:00:00Z',
            'first_comment_at': None,
            'merged_at': '2023-01-15T14:00:00Z'
        }

        duration, metadata = extract_timestamps_from_pr(pr_data)

        assert duration is not None
        assert abs(duration - 4.0) < 0.01
        assert metadata['first_comment_at'] is None

    def test_missing_all_timestamps(self):
        pr_data = {
            'pr_id': 'PR-789',
            'created_at': None,
            'first_comment_at': None,
            'merged_at': None
        }

        duration, metadata = extract_timestamps_from_pr(pr_data)

        assert duration is None
        assert metadata['pr_id'] == 'PR-789'
        assert metadata['duration_hours'] is None