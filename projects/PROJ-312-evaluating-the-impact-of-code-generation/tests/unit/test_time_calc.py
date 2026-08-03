import pytest
from datetime import datetime
from fetch_data import parse_iso_datetime, calculate_turnaround_hours

def test_parse_iso_datetime():
    dt = parse_iso_datetime("2023-01-01T12:00:00Z")
    assert dt.year == 2023
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 12

def test_calculate_turnaround_hours():
    created = "2023-01-01T12:00:00Z"
    merged = "2023-01-02T12:00:00Z"
    hours = calculate_turnaround_hours(created, merged)
    assert hours == 24.0
    
    merged_24h = "2023-01-01T18:00:00Z"
    hours_6 = calculate_turnaround_hours(created, merged_24h)
    assert hours_6 == 6.0
