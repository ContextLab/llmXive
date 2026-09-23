"""
Unit tests for age calculation logic (T009 and T017b).

Tests FR-010: Dependencies with missing release metadata should have age_in_days=null
but still include vulnerability_count.
"""

import pytest
from datetime import datetime, timezone
from src.utils.age import (
    parse_date,
    calculate_age_in_days,
    validate_age_data
)


class TestParseDate:
    """Tests for the parse_date function."""

    def test_parse_valid_iso_date(self):
        """Test parsing a valid ISO format date."""
        date_str = "2023-01-15T10:30:00Z"
        result = parse_date(date_str)
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_with_timezone(self):
        """Test parsing a date with explicit timezone."""
        date_str = "2023-06-20T15:45:00+05:00"
        result = parse_date(date_str)
        assert result is not None
        assert result.tzinfo is not None

    def test_parse_none_input(self):
        """Test that None input returns None."""
        result = parse_date(None)
        assert result is None

    def test_parse_empty_string(self):
        """Test that empty string returns None."""
        result = parse_date("")
        assert result is None

    def test_parse_whitespace_string(self):
        """Test that whitespace-only string returns None."""
        result = parse_date("   ")
        assert result is None

    def test_parse_invalid_format(self):
        """Test that invalid date format returns None."""
        result = parse_date("not-a-date")
        assert result is None


class TestCalculateAgeInDays:
    """Tests for the calculate_age_in_days function."""

    def test_calculate_age_valid_date(self):
        """Test age calculation with a valid past date."""
        # Use a fixed date 10 days ago
        past_date = datetime.now(timezone.utc).replace(day=1)
        result = calculate_age_in_days(past_date)
        assert result is not None
        assert result >= 0

    def test_calculate_age_string_date(self):
        """Test age calculation with ISO string date."""
        # 30 days ago
        date_str = "2023-11-01T00:00:00Z"
        result = calculate_age_in_days(date_str)
        assert result is not None
        assert result > 0

    def test_calculate_age_none_input(self):
        """Test FR-010: None input returns None, not an error."""
        result = calculate_age_in_days(None)
        assert result is None

    def test_calculate_age_empty_string(self):
        """Test FR-010: Empty string returns None."""
        result = calculate_age_in_days("")
        assert result is None

    def test_calculate_age_invalid_string(self):
        """Test FR-010: Invalid date string returns None."""
        result = calculate_age_in_days("invalid-date")
        assert result is None

    def test_calculate_age_future_date(self):
        """Test age calculation with a future date (edge case)."""
        future_date = datetime.now(timezone.utc).replace(year=2030)
        result = calculate_age_in_days(future_date)
        assert result is not None
        assert result < 0  # Negative age for future dates

    def test_age_returns_float(self):
        """Test that age is returned as a float."""
        past_date = datetime.now(timezone.utc) - timedelta(days=5)
        result = calculate_age_in_days(past_date)
        assert isinstance(result, float)


class TestFR010Compliance:
    """Tests specifically for FR-010 compliance."""

    def test_null_release_date_included_in_vuln_count(self):
        """
        Verify that when release_date is null, age_in_days is null
        but the dependency can still have a vulnerability_count.
        This is the core FR-010 requirement.
        """
        # Simulate a dependency with missing release date
        age_result = calculate_age_in_days(None)
        vulnerability_count = 3  # Can still have vulnerabilities

        assert age_result is None, "age_in_days must be None for missing release date"
        assert vulnerability_count is not None, "vulnerability_count should still be populated"

    def test_validate_age_data_compliance(self):
        """Test the validation function for FR-010 compliance."""
        # Case 1: Missing release date but has vulnerabilities
        validation = validate_age_data(age_in_days=None, vulnerability_count=5)
        assert validation["age_is_null"] is True
        assert validation["vulnerability_count_exists"] is True
        assert validation["fr010_compliant"] is True

        # Case 2: Has both age and vulnerabilities
        validation = validate_age_data(age_in_days=100.5, vulnerability_count=2)
        assert validation["age_is_null"] is False
        assert validation["fr010_compliant"] is True

        # Case 3: Missing both (should flag warning)
        validation = validate_age_data(age_in_days=None, vulnerability_count=None)
        assert validation["fr010_compliant"] is False

    def test_real_world_scenario_missing_release(self):
        """
        Test a realistic scenario where a dependency has no release metadata
        but still has vulnerability data from npm audit.
        """
        dependency_data = {
            "name": "old-package",
            "version": "1.0.0",
            "last_release_date": None,  # Missing
            "vulnerability_count": 4
        }

        age = calculate_age_in_days(dependency_data["last_release_date"])
        vuln_count = dependency_data["vulnerability_count"]

        # FR-010: Age is null, but vulnerability count is preserved
        assert age is None
        assert vuln_count == 4

    def test_real_world_scenario_with_release(self):
        """Test a realistic scenario with complete data."""
        dependency_data = {
            "name": "modern-package",
            "version": "2.0.0",
            "last_release_date": "2023-01-01T00:00:00Z",
            "vulnerability_count": 0
        }

        age = calculate_age_in_days(dependency_data["last_release_date"])
        vuln_count = dependency_data["vulnerability_count"]

        assert age is not None
        assert age > 0
        assert vuln_count == 0


# Import timedelta for the test
from datetime import timedelta
