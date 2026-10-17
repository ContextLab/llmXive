"""
Test for the T008 download script.

The test ensures that the script:
1. Executes without error (exit code 0).
2. Creates the expected parquet file at data/raw/PostsTags.parquet.
3. The created file starts with the Parquet magic bytes 'PAR1'.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # points to project root
SCRIPT_PATH = PROJECT_ROOT / "code" / "data" / "download.py"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "PostsTags.parquet"


@pytest.fixture(scope="module")
def run_download():
    """Run the download script once for the whole module."""
    # Ensure any previous artifact is removed to test fresh download
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    result = subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)
    return result


def test_script_exits_successfully(run_download):
    """The script should exit with code 0."""
    assert run_download.returncode == 0, f"Script failed: {run_download.stdout}\n{run_download.stderr}"


def test_output_file_created(run_download):
    """The expected parquet file must exist after script execution."""
    assert OUTPUT_PATH.is_file(), "PostsTags.parquet was not created."


def test_parquet_magic_bytes(run_download):
    """Validate that the file begins with the Parquet magic header."""
    with open(OUTPUT_PATH, "rb") as f:
        magic = f.read(4)
    assert magic == b"PAR1", f"File does not start with Parquet magic bytes: {magic!r}"