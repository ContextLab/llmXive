"""Simple sanity test for the cleaning pipeline."""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("script", ["code/02_clean_data.py"])
def test_clean_data_produces_file(script):
    """Running the script should create the processed CSV."""
    # Ensure a fresh start
    processed = Path("data/processed/cleaned_data.csv")
    if processed.is_file():
        processed.unlink()

    # Execute the script
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert processed.is_file(), "cleaned_data.csv was not created"


def test_missing_raw_raises():
    """If raw data is missing, the script should exit with error code 1."""
    # Temporarily rename any existing raw file
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "survey_data.csv"
    temp_name = raw_dir / "survey_data.tmp"
    if raw_file.is_file():
        raw_file.rename(temp_name)
    try:
        result = subprocess.run(
            [sys.executable, "code/02_clean_data.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
    finally:
        # Restore the file if it was moved
        if temp_name.is_file():
            temp_name.rename(raw_file)