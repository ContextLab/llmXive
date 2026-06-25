import csv
from pathlib import Path

import pytest

# The module under test lives in ``code/parse_failure_logger.py`` and is importable
# as a top‑level module thanks to the repository's test configuration.
from parse_failure_logger import init_logger, log_parse_failure


def test_log_parse_failure_writes_to_csv(tmp_path: Path):
    """
    Verify that ``log_parse_failure`` creates (or appends to) a CSV file with the
    expected columns and values.
    """
    # Use a temporary CSV file so the test does not interfere with real project data.
    csv_path = tmp_path / "parse_failures.csv"

    # Initialise the logger with the temporary path.
    logger = init_logger(csv_path)

    # Log a synthetic parse failure.
    test_file = "example.py"
    test_error = "SyntaxError: invalid syntax"
    log_parse_failure(test_file, test_error, logger)

    # Read back the CSV and assert its contents.
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1, "Exactly one log row should have been written"
    row = rows[0]
    assert row["file_path"] == test_file
    assert test_error in row["error_message"]
    # Timestamp should be a non‑empty ISO‑8601 string.
    assert row["timestamp"]

# Additional sanity check: calling the logger a second time should append,
# not overwrite, and should not duplicate the header.
def test_multiple_log_calls_append(tmp_path: Path):
    csv_path = tmp_path / "parse_failures.csv"
    logger = init_logger(csv_path)

    log_parse_failure("first.py", "Error A", logger)
    log_parse_failure("second.py", "Error B", logger)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["file_path"] == "first.py"
    assert rows[1]["file_path"] == "second.py"
    # Ensure header appears only once (DictReader would raise if duplicated)
    # No explicit check needed; the fact that DictReader succeeded means the header is correct.