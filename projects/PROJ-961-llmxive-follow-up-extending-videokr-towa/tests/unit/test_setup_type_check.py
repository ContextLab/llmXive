"""
Unit test for ``code/setup_type_check.py``.

The purpose of this test is to verify that the MyPy log file
``data/processed/type_log.txt`` is written **even when MyPy reports
type errors**.  We deliberately create a Python file with a type error
and then invoke ``run_mypy_check``.  After execution we assert that
the log file exists and contains non‑empty content.
"""

import os
import sys
from pathlib import Path

import pytest

# Import the function under test.
from setup_type_check import run_mypy_check
from utils.config import get_path, ensure_dir

@pytest.fixture(scope="function")
def temporary_bad_file(tmp_path: Path):
    """
    Create a temporary Python file with a clear type error.
    """
    bad_file_path = tmp_path / "bad_file.py"
    # Example: function annotated to return ``int`` but returns a ``str``.
    bad_file_path.write_text(
        "def foo() -> int:\n"
        "    return 'this is a string, not an int'\n",
        encoding="utf-8",
    )
    # Copy the file into the project's ``code/`` directory so that MyPy
    # will analyse it.
    target_path = Path(__file__).resolve().parents[2] / "code" / "bad_file.py"
    ensure_dir(target_path.parent)
    target_path.write_text(bad_file_path.read_text(encoding="utf-8"), encoding="utf-8")
    yield target_path
    # Cleanup after the test.
    if target_path.exists():
        target_path.unlink()


def test_type_check_log_is_written_even_on_failure(tmp_path, temporary_bad_file):
    """
    Run MyPy on the project (which now contains a deliberate type error)
    and verify that ``type_log.txt`` is created and contains output.
    """
    # Ensure the log destination directory exists.
    log_path = get_path("data/processed/type_log.txt")
    ensure_dir(log_path.parent)

    # Remove any pre‑existing log file to avoid false positives.
    if log_path.exists():
        log_path.unlink()

    # Execute the MyPy check.  The function returns the MyPy exit code.
    exit_code = run_mypy_check()

    # MyPy should report at least one error because of the deliberately
    # introduced type mismatch, so the exit code must be non‑zero.
    assert exit_code != 0, "MyPy unexpectedly succeeded on a file with a type error."

    # The log file must exist and be non‑empty.
    assert log_path.is_file(), "type_log.txt was not created."
    assert log_path.stat().st_size > 0, "type_log.txt is empty despite MyPy failure."

    # Optional sanity check: the log should contain the name of the bad file.
    log_contents = log_path.read_text(encoding="utf-8")
    assert "bad_file.py" in log_contents, "Log does not reference the file with the type error."

    # Cleanup the temporary bad file from the project source tree.
    if temporary_bad_file.exists():
        temporary_bad_file.unlink()