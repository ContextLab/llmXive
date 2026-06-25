import csv
import pytest
from pathlib import Path

# The module under test lives at the repository root and is imported
# directly as ``parse_failure_logger`` according to the defined API surface.
from parse_failure_logger import init_logger, log_parse_failure


def test_log_parse_failure_writes_correct_row(tmp_path: Path):
    """
    Verify that ``log_parse_failure`` creates a CSV file with the expected
    header and a single data row containing the supplied information.
    """
    # Arrange – a temporary CSV file for the logger to write to
    log_file = tmp_path / "parse_failures.csv"
    init_logger(log_file)

    # Simulate a parsing exception
    sample_error = SyntaxError("invalid syntax")
    sample_path = "example.py"

    # Act – record the failure
    log_parse_failure(sample_path, sample_error)

    # Assert – CSV contains header + one data row with correct values
    with log_file.open(newline="") as f:
        rows = list(csv.reader(f))

    # Header row
    assert rows[0] == ["timestamp", "file_path", "error_type", "error_message"]
    # Exactly one data row follows
    assert len(rows) == 2

    _, logged_path, error_type, error_msg = rows[1]
    assert logged_path == sample_path
    assert error_type == "SyntaxError"
    assert error_msg == "invalid syntax"