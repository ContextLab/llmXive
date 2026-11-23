"""
Tests for the parse_slr_file function in data/ingestion.py.
"""
import pytest
from data.ingestion import parse_slr_file, NormalPoint, DataIngestionError


def test_parse_slr_file_valid_content():
    """Test parsing a valid SLR file content string."""
    # Simulate a standard SLR normal point line
    # Format: YYYY MM DD HH MM SS.mmm Range(m) Res(m)
    raw_content = b"""# Header comment
    2023 01 15 12 30 45.123 1234567.890 0.012 GOOD
    2023 01 15 12 31 00.456 1234568.100 -0.005 GOOD
    """
    
    points = parse_slr_file(raw_content)
    
    assert len(points) == 2
    
    p1 = points[0]
    assert p1.timestamp == "2023-01-15T12:30:45.123000"
    assert abs(p1.range - 1234567.890) < 1e-6
    assert abs(p1.residual - 0.012) < 1e-6
    assert p1.quality_flag == "GOOD"
    
    p2 = points[1]
    assert p2.timestamp == "2023-01-15T12:31:00.456000"
    assert abs(p2.residual - (-0.005)) < 1e-6


def test_parse_slr_file_large_residual():
    """Test that large residuals are flagged as BAD."""
    raw_content = b"""2023 01 15 12 30 45.123 1234567.890 0.050 GOOD
    """
    
    points = parse_slr_file(raw_content)
    assert len(points) == 1
    # 0.050m = 5cm > 2cm threshold
    assert points[0].quality_flag == "BAD"


def test_parse_slr_file_empty():
    """Test that empty content raises an error."""
    with pytest.raises(DataIngestionError):
        parse_slr_file(b"")


def test_parse_slr_file_no_valid_points():
    """Test that content with no valid numeric lines raises an error."""
    raw_content = b"""# Only comments
    # Another comment
    """
    with pytest.raises(DataIngestionError):
        parse_slr_file(raw_content)


def test_parse_slr_file_malformed_lines():
    """Test that malformed lines are skipped but valid ones are parsed."""
    raw_content = b"""
    # Header
    invalid line
    2023 01 15 12 30 45.123 1234567.890 0.012 GOOD
    also invalid
    """
    
    points = parse_slr_file(raw_content)
    assert len(points) == 1
    assert points[0].timestamp.startswith("2023-01-15")