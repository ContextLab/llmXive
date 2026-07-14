"""
Ensure that parse failures are logged but do not crash the pipeline.
"""
from __future__ import annotations

import pathlib
import csv

from parse_failure_logger import init_logger, log_parse_failure, get_parse_failures_path

def test_log_parse_failure_creates_entry(tmp_path: pathlib.Path):
    # Initialise logger (writes to data/parse_failures.csv)
    init_logger()
    path = get_parse_failures_path()
    # Ensure the file is empty initially
    path.unlink(missing_ok=True)

    # Log a synthetic failure
    log_parse_failure("bad_file.py", "SyntaxError: invalid syntax")

    # Verify entry exists
    assert path.exists()
    rows = list(csv.reader(path.read_text().splitlines()))
    assert rows[0] == ["file_path", "error_message"]
    assert rows[1][0] == "bad_file.py"
