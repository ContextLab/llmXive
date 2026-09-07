import pytest
from datetime import datetime, timedelta
from feature_extraction.timestamps import parse_iso_date_safe, calculate_review_duration

def test_parse_iso_date_safe_valid():
    """Test parsing valid ISO date."""
    date_str = "2023-01-15T10:30:00Z"
    result = parse_iso_date_safe(date_str)
    
    assert result is not None
    assert result.year == 2023
    assert result.month == 1
    assert result.day == 15

def test_parse_iso_date_safe_invalid():
    """Test parsing invalid ISO date returns None."""
    date_str = "not-a-date"
    result = parse_iso_date_safe(date_str)
    
    assert result is None

def test_calculate_review_duration():
    """Test review duration calculation."""
    opened = datetime(2023, 1, 1, 10, 0, 0)
    first_comment = datetime(2023, 1, 1, 12, 30, 0)
    
    duration = calculate_review_duration(opened, first_comment)
    
    assert duration == 150  # 2.5 hours in minutes

def test_calculate_review_duration_no_comment():
    """Test review duration when no comment exists."""
    opened = datetime(2023, 1, 1, 10, 0, 0)
    
    duration = calculate_review_duration(opened, None)
    
    assert duration is None