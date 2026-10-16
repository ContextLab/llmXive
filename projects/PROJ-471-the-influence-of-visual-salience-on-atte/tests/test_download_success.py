import subprocess
import json
from pathlib import Path
import pytest
from llmxive_toolkit import paths

def test_download_script_execution():
    """
    Verify that the download_data.py script executes successfully 
    and produces the required artifacts.
    """
    # Run the download script
    result = subprocess.run(
        ["python", "code/ingestion/download_data.py"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"

    # Verify raw data directory exists
    raw_dir = paths.data("raw") / "ds003123"
    assert raw_dir.is_dir(), "Dataset directory ds003123 was not created"
    
    # Verify subject folders exist
    sub_folders = [p for p in raw_dir.iterdir() if p.is_dir() and p.name.startswith("sub-")]
    assert len(sub_folders) > 0, "No subject folders (sub-*) found in the dataset"

    # Verify checksums.json exists
    checksum_file = paths.data("raw") / "checksums.json"
    assert checksum_file.is_file(), "checksums.json was not created"

    # Verify checksums.json content
    with open(checksum_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    assert manifest["dataset_id"] == "ds003123"
    assert len(manifest["files"]) > 0, "Manifest contains no files"
    assert "timestamp" in manifest