import pytest
import logging
from code.ingest import parse_bed_line, parse_bed_file, BedParseError
from pathlib import Path
import tempfile
import os

def test_parse_handles_malformed_bed():
    """
    Test that parse_bed_line raises ValueError on malformed BED input.
    Covers: US1-Edge-Case-001 (Malformed BED lines should raise specific error)
    
    This test verifies that the parser strictly adheres to the BED format specification
    and raises ValueError for any malformed input, as required by the task description.
    """
    # Case 1: Not enough columns (BED requires at least 3)
    malformed_line_1 = "chr1\t1000\t2000"
    with pytest.raises(ValueError):
        parse_bed_line(malformed_line_1)

    # Case 2: Non-integer start coordinate
    malformed_line_2 = "chr1\tabc\t2000\tpeak1"
    with pytest.raises(ValueError):
        parse_bed_line(malformed_line_2)

    # Case 3: Start > End
    malformed_line_3 = "chr1\t2000\t1000\tpeak1"
    with pytest.raises(ValueError):
        parse_bed_line(malformed_line_3)

    # Case 4: Negative coordinate
    malformed_line_4 = "chr1\t-100\t200\tpeak1"
    with pytest.raises(ValueError):
        parse_bed_line(malformed_line_4)

    # Case 5: Empty line
    malformed_line_5 = ""
    with pytest.raises(ValueError):
        parse_bed_line(malformed_line_5)

    # Case 6: Non-integer end coordinate
    malformed_line_6 = "chr1\t1000\txyz\tpeak1"
    with pytest.raises(ValueError):
        parse_bed_line(malformed_line_6)

def test_parse_valid_bed_line():
    """
    Test that valid BED lines are parsed correctly.
    """
    valid_line = "chr1\t1000\t2000\tpeak1\t0\t+"
    result = parse_bed_line(valid_line)
    assert result["chrom"] == "chr1"
    assert result["start"] == 1000
    assert result["end"] == 2000
    assert result["name"] == "peak1"
    assert result["score"] == 0
    assert result["strand"] == "+"

def test_parse_bed_file(tmp_path):
    """
    Test that parse_bed_file correctly reads a file and handles malformed lines.
    The function should raise BedParseError when encountering malformed lines.
    """
    # Create a temporary BED file with mixed valid and invalid lines
    test_file = tmp_path / "test_peaks.bed"
    content = (
        "chr1\t1000\t2000\tpeak1\t0\t+\n"
        "chr1\t3000\t4000\tpeak2\t0\t-\n"
        "chr1\tinvalid\t5000\tpeak3\t0\t+\n"  # Malformed
        "chr1\t6000\t7000\tpeak4\t0\t+\n"
    )
    test_file.write_text(content)

    # parse_bed_file should raise BedParseError on the first malformed line
    with pytest.raises(BedParseError):
        parse_bed_file(str(test_file))

def test_parse_bed_file_with_skip(tmp_path):
    """
    Test parsing behavior when skip_malformed is True (if implemented).
    If the function doesn't support skip_malformed, this tests the standard raise behavior.
    """
    test_file = tmp_path / "test_peaks_skip.bed"
    content = (
        "chr1\t1000\t2000\tpeak1\t0\t+\n"
        "chr1\tinvalid\t5000\tpeak3\t0\t+\n"
        "chr1\t6000\t7000\tpeak4\t0\t+\n"
    )
    test_file.write_text(content)

    # Expecting an error to be raised as per strict parsing requirement
    with pytest.raises(BedParseError):
        parse_bed_file(str(test_file))

def test_parse_bed_file_logging_error(tmp_path, caplog):
    """
    Test that parse_bed_file logs an error when encountering malformed lines.
    This verifies the logging requirement from the task description.
    """
    test_file = tmp_path / "test_peaks_log.bed"
    content = (
        "chr1\t1000\t2000\tpeak1\t0\t+\n"
        "chr1\tinvalid\t5000\tpeak3\t0\t+\n"  # Malformed
    )
    test_file.write_text(content)

    # Set up logging capture
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BedParseError):
            parse_bed_file(str(test_file))
    
    # Verify that an error was logged
    assert any(record.levelno == logging.ERROR for record in caplog.records)