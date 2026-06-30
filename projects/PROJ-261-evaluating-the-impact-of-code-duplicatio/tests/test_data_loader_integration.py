import os
import pathlib
import subprocess
import sys

import pytest

# The integration test ensures that the data loader can be executed
# without raising an exception and that it produces the expected CSV file.
# This mirrors the expectations of the quickstart run‑book.

@pytest.mark.integration
def test_data_loader_produces_csv(tmp_path, monkeypatch):
    # Run the data loader script in a subprocess to emulate the real CLI.
    # Use a small max‑bytes limit so the test finishes quickly.
    csv_path = pathlib.Path("data/raw/github-code-sample.csv")
    if csv_path.exists():
        csv_path.unlink()

    # Build command
    cmd = [
        sys.executable,
        "code/data_loader.py",
        "--max-bytes",
        "1024",  # 1 KiB – enough for a few rows
        "--output",
        str(csv_path),
    ]

    # Execute
    result = subprocess.run(
        cmd,
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
    )
    # The script should exit cleanly.
    assert result.returncode == 0, f"stderr: {result.stderr}"

    # The CSV file must now exist and contain a header line.
    assert csv_path.is_file(), "CSV output file was not created"
    with csv_path.open("r", encoding="utf-8") as f:
        header = f.readline().strip()
    expected_header = "repo_name,file_path,content"
    assert header == expected_header, f"Unexpected CSV header: {header}"