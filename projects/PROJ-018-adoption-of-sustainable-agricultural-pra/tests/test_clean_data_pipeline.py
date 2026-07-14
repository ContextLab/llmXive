"""Smoke test for the cleaning pipeline.

The test simply runs the ``code/02_clean_data.py`` script and checks that
the expected output file exists and contains at least one row.
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.timeout(60)
def test_clean_data_produces_csv(tmp_path: Path):
    # Ensure the output directory is empty before the run
    processed_dir = Path("data/processed")
    if processed_dir.is_dir():
        for f in processed_dir.iterdir():
            f.unlink()

    # Run the script
    result = subprocess.run(
        [sys.executable, "code/02_clean_data.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    cleaned_path = processed_dir / "cleaned_data.csv"
    assert cleaned_path.is_file(), "cleaned_data.csv was not created"

    # Minimal sanity check – at least one row and a header
    with cleaned_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) > 1, "cleaned_data.csv appears empty"
    assert "," in lines[0], "Header line missing in cleaned_data.csv"