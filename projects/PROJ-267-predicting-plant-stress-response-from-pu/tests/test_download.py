"""
Integration test for the real‑data ingestion script.

The test executes ``code/data/download.py`` and verifies that:
1. At least one file (the GEO XML) is downloaded into ``data/raw/``.
2. A non‑empty ``checksums.sha256`` file is created alongside the data.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_download_script_runs_successfully():
    # Ensure a clean ``data/raw`` directory before the test.
    raw_dir: Path = paths.data("raw")
    if raw_dir.exists():
        for child in raw_dir.iterdir():
            child.unlink()
    else:
        raw_dir.mkdir(parents=True, exist_ok=True)

    # Run the download script as a subprocess.
    script_path = paths.code("data", "download.py")
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)

    # The script must exit with status 0.
    assert result.returncode == 0, f"Script exited with {result.returncode}. Stderr: {result.stderr}"

    # Verify that a GEO XML file (ending with .xml) exists in ``data/raw``.
    downloaded_files = list(raw_dir.glob("*.xml"))
    assert downloaded_files, "No XML file was downloaded to data/raw."

    # Verify that the checksum manifest exists and contains at least one entry.
    checksum_file = raw_dir / "checksums.sha256"
    assert checksum_file.is_file(), "Checksum file was not created."
    content = checksum_file.read_text().strip()
    assert content, "Checksum file is empty."
    # Simple sanity: each line should contain two whitespace‑separated fields.
    for line in content.splitlines():
        parts = line.split()
        assert len(parts) == 2, f"Malformed checksum line: {line}"