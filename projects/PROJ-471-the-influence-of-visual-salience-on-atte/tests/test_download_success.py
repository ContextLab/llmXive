import json
import subprocess
from pathlib import Path

import pytest

from llmxive_toolkit import paths

@pytest.mark.timeout(600)
def test_download_success():
    """
    Ensure that the download script exits with code 0 and that the
    checksums manifest exists and contains at least one file entry.
    """
    script_path = Path("code/ingestion/download_data.py")
    result = subprocess.run(
        ["python", str(script_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    checksum_path = paths.data("raw") / "checksums.json"
    assert checksum_path.is_file(), "checksums.json was not created"

    with checksum_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # The manifest must contain the expected top‑level keys.
    assert "dataset_id" in manifest
    assert "files" in manifest
    assert isinstance(manifest["files"], list)
    assert len(manifest["files"]) > 0, "No files were recorded in the checksum manifest"