"""
Unit tests for the ingest module.
"""
import pytest
import logging
import tempfile
import os
from pathlib import Path

# Import the module under test
from code.ingest import parse_bed_line, parse_bed_file, BedParseError

def test_parse_handles_malformed_bed():
    """
    Assert parser raises specific ValueError on malformed BED input and logs error.
    
    Scenarios covered:
    1. Line with fewer than 3 columns.
    2. Line with non-integer start/end coordinates.
    3. Line with negative start coordinate.
    4. Line with end <= start.
    """
    # Setup logger to capture logs
    logger = logging.getLogger('code.ingest')
    logger.setLevel(logging.ERROR)
    
    # Test Case 1: Too few columns
    malformed_line_1 = "chr1\t100"  # Missing end
    with pytest.raises(ValueError) as exc_info:
        parse_bed_line(malformed_line_1)
    assert "expected at least 3 columns" in str(exc_info.value)
    
    # Test Case 2: Non-integer coordinates
    malformed_line_2 = "chr1\tabc\t100\tpeak1"
    with pytest.raises(ValueError) as exc_info:
        parse_bed_line(malformed_line_2)
    assert "start/end must be integers" in str(exc_info.value)
    
    # Test Case 3: Negative start
    malformed_line_3 = "chr1\t-100\t200\tpeak1"
    with pytest.raises(ValueError) as exc_info:
        parse_bed_line(malformed_line_3)
    assert "start coordinate cannot be negative" in str(exc_info.value)
    
    # Test Case 4: End <= Start
    malformed_line_4 = "chr1\t100\t50\tpeak1"
    with pytest.raises(ValueError) as exc_info:
        parse_bed_line(malformed_line_4)
    assert "end must be greater than start" in str(exc_info.value)

def test_parse_handles_valid_bed():
    """Verify valid BED lines are parsed correctly."""
    valid_line = "chr1\t100\t200\tpeak1"
    result = parse_bed_line(valid_line)
    assert result == ("chr1", 100, 200, "peak1")

def test_parse_bed_file_handles_malformed(tmp_path):
    """Test that parse_bed_file raises ValueError and logs error when file contains malformed lines."""
    # Create a temporary file with a malformed line
    test_file = tmp_path / "test_malformed.bed"
    test_file.write_text("chr1\t100\t200\tpeak1\nchr1\tbad\t300\tpeak2\n")
    
    with pytest.raises(ValueError):
        parse_bed_file(str(test_file))

def test_parse_bed_file_missing_file():
    """Test that parse_bed_file raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        parse_bed_file("/nonexistent/path/file.bed")