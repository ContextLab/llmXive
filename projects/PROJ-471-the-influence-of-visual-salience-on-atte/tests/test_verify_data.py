import json
import os
import subprocess
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Helper to run the verification script
def run_verify():
    result = subprocess.run(
        ["python", "-m", "code.ingestion.verify_data"],
        cwd=Path(__file__).parents[2],  # project root
        capture_output=True,
        text=True,
    )
    return result

def test_verify_success(tmp_path, monkeypatch):
    """
    Create a minimal dummy dataset structure, run the verification script,
    and assert that it exits cleanly and writes a correct checksums.json.
    """
    # Setup dummy dataset under data/raw/ds003123
    raw_root = paths.data("raw")
    dataset_dir = raw_root / "ds003123"
    (dataset_dir / "sub-01").mkdir(parents=True, exist_ok=True)
    (dataset_dir / "stimuli").mkdir(parents=True, exist_ok=True)

    # Create a couple of small files
    file1 = dataset_dir / "sub-01" / "eye_tracking.txt"
    file1.write_text("dummy eye tracking data")
    file2 = dataset_dir / "stimuli" / "image1.png"
    file2.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG header

    # Ensure no pre‑existing checksum file
    checksum_path = raw_root / "checksums.json"
    if checksum_path.is_file():
        checksum_path.unlink()

    # Run verification
    result = run_verify()
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "Dataset verification succeeded" in result.stdout

    # Validate checksums.json content
    with checksum_path.open() as f:
        manifest = json.load(f)
    assert "files" in manifest
    paths_in_manifest = {Path(entry["path"]) for entry in manifest["files"]}
    expected_paths = {
        Path("ds003123/sub-01/eye_tracking.txt"),
        Path("ds003123/stimuli/image1.png"),
    }
    assert paths_in_manifest == expected_paths

def test_missing_dataset_raises():
    """
    Ensure that the script raises the correct error when the dataset
    directory is absent.
    """
    raw_root = paths.data("raw")
    # Remove any existing ds003123 directory
    ds_dir = raw_root / "ds003123"
    if ds_dir.is_dir():
        for child in ds_dir.rglob("*"):
            child.unlink()
        ds_dir.rmdir()

    # Run verification – should exit non‑zero and contain the error phrase
    result = run_verify()
    assert result.returncode != 0
    assert "DATA_MISSING_001" in result.stderr