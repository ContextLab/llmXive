"""Contract test verifying timestamps are normalized to UTC.

This test validates that the normalize_timestamp function from
code/pipeline/utils.py correctly converts various timestamp formats to UTC.

Per T070 requirements:
- All timestamps in cascade data must be normalized to UTC
- Various input formats should be handled (ISO 8601 with timezone, without timezone, etc.)
- Output should be in a consistent UTC format
"""

import pytest
from datetime import datetime, timezone, timedelta
from pipeline.utils import normalize_timestamp


class TestTimestampNormalization:
    """Contract tests for UTC timestamp normalization."""

    def test_iso8601_with_utc_timezone(self):
        """Test ISO 8601 timestamp with explicit UTC timezone is normalized correctly."""
        input_ts = "2023-05-15T14:30:00Z"
        result = normalize_timestamp(input_ts)
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.year == 2023
        assert result.month == 5
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30

    def test_iso8601_with_positive_offset(self):
        """Test ISO 8601 timestamp with positive timezone offset is converted to UTC."""
        input_ts = "2023-05-15T14:30:00+02:00"
        result = normalize_timestamp(input_ts)
        assert result is not None
        assert result.tzinfo == timezone.utc
        # 14:30 +02:00 should become 12:30 UTC
        assert result.hour == 12
        assert result.minute == 30

    def test_iso8601_with_negative_offset(self):
        """Test ISO 8601 timestamp with negative timezone offset is converted to UTC."""
        input_ts = "2023-05-15T14:30:00-05:00"
        result = normalize_timestamp(input_ts)
        assert result is not None
        assert result.tzinfo == timezone.utc
        # 14:30 -05:00 should become 19:30 UTC
        assert result.hour == 19
        assert result.minute == 30

    def test_iso8601_with_millisecond_offset(self):
        """Test ISO 8601 timestamp with millisecond precision."""
        input_ts = "2023-05-15T14:30:00.123Z"
        result = normalize_timestamp(input_ts)
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.year == 2023
        assert result.month == 5
        assert result.day == 15

    def test_iso8601_without_timezone(self):
        """Test ISO 8601 timestamp without timezone is treated as UTC."""
        input_ts = "2023-05-15T14:30:00"
        result = normalize_timestamp(input_ts)
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_date_only_format(self):
        """Test date-only format (YYYY-MM-DD) is handled."""
        input_ts = "2023-05-15"
        result = normalize_timestamp(input_ts)
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.year == 2023
        assert result.month == 5
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0

    def test_datetime_object(self):
        """Test datetime object with UTC timezone passes through."""
        input_dt = datetime(2023, 5, 15, 14, 30, 0, tzinfo=timezone.utc)
        result = normalize_timestamp(input_dt)
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_datetime_object_with_offset(self):
        """Test datetime object with non-UTC timezone is converted."""
        tz_plus_5 = timezone(timedelta(hours=5))
        input_dt = datetime(2023, 5, 15, 14, 30, 0, tzinfo=tz_plus_5)
        result = normalize_timestamp(input_dt)
        assert result is not None
        assert result.tzinfo == timezone.utc
        # 14:30 +05:00 should become 09:30 UTC
        assert result.hour == 9
        assert result.minute == 30

    def test_empty_string(self):
        """Test that empty string input is handled."""
        result = normalize_timestamp("")
        assert result is None

    def test_none_input(self):
        """Test that None input is handled."""
        result = normalize_timestamp(None)
        assert result is None

    def test_invalid_format_raises(self):
        """Test that invalid timestamp format raises ValueError."""
        with pytest.raises(ValueError):
            normalize_timestamp("not-a-timestamp")

    def test_utc_output_format(self):
        """Test that all outputs are in a consistent UTC format."""
        inputs = [
            "2023-05-15T14:30:00Z",
            "2023-05-15T14:30:00+02:00",
            "2023-05-15T14:30:00-05:00",
            "2023-05-15T14:30:00",
        ]
        for ts_input in inputs:
            result = normalize_timestamp(ts_input)
            assert result is not None
            assert result.tzinfo == timezone.utc
            # Verify ISO format output is consistent
            iso_str = result.isoformat()
            assert "+00:00" in iso_str or iso_str.endswith("Z")

    def test_real_world_timestamps(self):
        """Test with real-world timestamp formats from cascade data."""
        # Common formats found in social media cascade data
        test_cases = [
            ("2023-01-15T08:30:00.000Z", 8, 30),  # UTC with milliseconds
            ("2023-01-15T08:30:00.000+00:00", 8, 30),  # UTC with +00:00
            ("2023-01-15T13:30:00+05:00", 8, 30),  # IST to UTC
            ("2023-01-15T03:30:00-05:00", 8, 30),  # EST to UTC
            ("2023-01-15T18:30:00+10:00", 8, 30),  # AEST to UTC
        ]
        for ts_input, expected_hour, expected_minute in test_cases:
            result = normalize_timestamp(ts_input)
            assert result is not None, f"Failed to parse: {ts_input}"
            assert result.hour == expected_hour, f"Hour mismatch for {ts_input}: got {result.hour}, expected {expected_hour}"
            assert result.minute == expected_minute, f"Minute mismatch for {ts_input}: got {result.minute}, expected {expected_minute}"
            assert result.tzinfo == timezone.utc, f"Not UTC for {ts_input}"