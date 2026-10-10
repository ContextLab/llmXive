"""
Unit tests for the sanity‑check added in ``code/build_graphs.py``.
The tests create a temporary CSV with a mixture of valid and invalid Q
values, invoke the ``sanity_check_modularity`` function, and verify that
appropriate warning messages are emitted to the log file.
"""

import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test
from code.build_graphs import sanity_check_modularity, MODULARITY_CSV, LOG_FILE

@pytest.fixture
def temp_csv(tmp_path: Path):
    """Create a temporary ``subject_modularity.csv`` for the test."""
    df = pd.DataFrame(
        {
            "subject_id": ["sub-001", "sub-002", "sub-003", "sub-004"],
            "modularity_q": [0.45, 1.12, -0.05, 0.78],
        }
    )
    csv_path = tmp_path / "subject_modularity.csv"
    df.to_csv(csv_path, index=False)
    # Patch the module‑level constant to point at the temporary file
    original_path = MODULARITY_CSV
    try:
        # Monkey‑patch the constant used by the module
        code.build_graphs.MODULARITY_CSV = csv_path  # type: ignore
        yield csv_path
    finally:
        code.build_graphs.MODULARITY_CSV = original_path  # restore

def test_sanity_check_logs_warnings(caplog, tmp_path):
    """
    Verify that out‑of‑bounds Q values generate WARNING log entries and that
    in‑range values do not.
    """
    # Prepare a DataFrame with known out‑of‑bounds values
    df = pd.DataFrame(
        {
            "subject_id": ["sub-A", "sub-B", "sub-C"],
            "modularity_q": [0.30, 1.05, -0.10],
        }
    )

    # Run the sanity check while capturing log output
    with caplog.at_level(logging.WARNING):
        sanity_check_modularity(df)

    # Expected warnings for sub-B and sub-C
    warning_messages = [rec.message for rec in caplog.records if rec.levelno == logging.WARNING]
    assert any("sub-B" in msg and "1.05" in msg for msg in warning_messages)
    assert any("sub-C" in msg and "-0.10" in msg for msg in warning_messages)
    # sub-A should not appear in warnings
    assert not any("sub-A" in msg for msg in warning_messages)

def test_main_writes_csv_and_logs(tmp_path, caplog):
    """
    End‑to‑end test of the ``main`` function: it should read the temporary CSV,
    perform the sanity check, and rewrite the CSV without altering the data.
    """
    # Create a temporary CSV with a mix of values
    df = pd.DataFrame(
        {
            "subject_id": ["s1", "s2"],
            "modularity_q": [0.6, 1.2],
        }
    )
    csv_path = tmp_path / "subject_modularity.csv"
    df.to_csv(csv_path, index=False)

    # Patch module constants to point at the temporary locations
    orig_csv = MODULARITY_CSV
    orig_log = LOG_FILE
    try:
        code.build_graphs.MODULARITY_CSV = csv_path  # type: ignore
        code.build_graphs.LOG_FILE = tmp_path / "build_graphs.log"  # type: ignore

        # Re‑configure logging to use the new log file
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            handlers=[
                logging.FileHandler(code.build_graphs.LOG_FILE, mode="a"),
                logging.StreamHandler(),
            ],
        )

        # Execute the script's main routine
        code.build_graphs.main()

        # Verify the CSV still exists and contains the original rows
        assert csv_path.is_file()
        df_out = pd.read_csv(csv_path)
        pd.testing.assert_frame_equal(df_out, df)

        # Verify that a warning about the out‑of‑bounds value was logged
        with open(code.build_graphs.LOG_FILE, "r") as f:
            log_contents = f.read()
        assert "has modularity Q = 1.20000 which is outside the expected range" in log_contents
    finally:
        # Restore original constants
        code.build_graphs.MODULARITY_CSV = orig_csv  # type: ignore
        code.build_graphs.LOG_FILE = orig_log  # type: ignore