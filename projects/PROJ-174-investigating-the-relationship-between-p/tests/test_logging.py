import os
import sys
import csv
import pytest
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import LoggingContext, QUALITY_REPORT_PATH, initialize_quality_report

def test_logging_context_add_exclusion_and_write_report():
    """
    Verify that LoggingContext.add_exclusion appends to the CSV correctly
    and that results/quality_report.csv exists with the correct schema.
    """
    # Clean up existing report to ensure fresh test
    if QUALITY_REPORT_PATH.exists():
        os.remove(QUALITY_REPORT_PATH)

    # Initialize context
    ctx = LoggingContext()

    # Verify file exists with headers immediately after init
    assert QUALITY_REPORT_PATH.exists(), "quality_report.csv should exist after LoggingContext init"
    
    with open(QUALITY_REPORT_PATH, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert headers == ['exclusion_type', 'count'], f"Headers must be ['exclusion_type', 'count'], got {headers}"

    # Add exclusions
    ctx.add_exclusion("blink_loss", 10)
    ctx.add_exclusion("missing_data", 5)
    ctx.add_exclusion("blink_loss", 5) # Accumulate

    # Write report
    ctx.write_report()

    # Verify file content
    assert QUALITY_REPORT_PATH.exists(), "Report file must exist after write_report"

    with open(QUALITY_REPORT_PATH, 'r') as f:
        reader = list(csv.reader(f))

    # Check header
    assert reader[0] == ['exclusion_type', 'count']

    # Check data rows (should be 2 unique types)
    data_rows = reader[1:]
    assert len(data_rows) == 2, f"Expected 2 data rows (unique exclusion types), got {len(data_rows)}"

    # Check accumulation
    blink_row = [row for row in data_rows if row[0] == 'blink_loss'][0]
    missing_row = [row for row in data_rows if row[0] == 'missing_data'][0]

    assert int(blink_row[1]) == 15, f"blink_loss should be 15 (10+5), got {blink_row[1]}"
    assert int(missing_row[1]) == 5, f"missing_data should be 5, got {missing_row[1]}"

    # Clean up
    os.remove(QUALITY_REPORT_PATH)

def test_initialize_quality_report_schema():
    """
    Verify that initialize_quality_report creates the file with exactly 2 columns.
    """
    if QUALITY_REPORT_PATH.exists():
        os.remove(QUALITY_REPORT_PATH)

    initialize_quality_report()

    assert QUALITY_REPORT_PATH.exists()
    with open(QUALITY_REPORT_PATH, 'r') as f:
        headers = f.readline().strip().split(',')
    assert len(headers) == 2
    assert headers == ['exclusion_type', 'count']
    
    if QUALITY_REPORT_PATH.exists():
        os.remove(QUALITY_REPORT_PATH)
