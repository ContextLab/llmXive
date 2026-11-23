"""
Unit test for the download_dr25 script.

This test checks that the script runs without raising an exception and that
the expected output file exists after execution. It does not validate the
contents of the file (that would require network access and large data
handling), but ensures the pipeline creates the CSV at the correct location.
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on the path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.ingest.download_dr25 import main as download_main
from llmxive_toolkit import paths

def test_download_dr25_creates_file(tmp_path, monkeypatch):
    """
    Run the download script and verify that the output CSV exists.

    The test uses a temporary directory for the data/raw location to avoid
    polluting the real repository data directory. The script itself determines
    its output path via the constant DATA_RAW_DIR; we monkeypatch that constant
    to point inside the temporary directory.
    """
    # Patch the DATA_RAW_DIR constant to point to a temp directory
    monkeypatch.setattr(
        "code.ingest.download_dr25.DATA_RAW_DIR",
        str(tmp_path / "raw")
    )

    # Ensure the temporary raw directory exists
    (tmp_path / "raw").mkdir(parents=True, exist_ok=True)

    # Run the script – it will attempt to download the real DR25 file.
    # If the internet is unavailable, the test will raise, which is
    # appropriate because the task requires real data.
    download_main()

    # Verify the expected output file exists
    output_path = Path(str(tmp_path / "raw")) / "dr25_raw.csv"
    assert output_path.is_file(), f"Expected output CSV not found at {output_path}"