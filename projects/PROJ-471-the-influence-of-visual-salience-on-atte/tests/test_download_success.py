import json
from pathlib import Path
import pytest
from llmxive_toolkit import paths
from code.ingestion.download_data import main as download_main

def test_download_success():
    """
    Asserts that the download script completes without error and produces
    the expected dataset directory and checksum manifest.
    """
    # Run the ingestion main
    download_main()

    # 1. Verify dataset directory exists
    raw_root = paths.data("raw")
    dataset_dir = raw_root / "ds003123"
    assert dataset_dir.is_dir(), "Dataset directory ds003123 should exist."

    # 2. Verify that subject folders (sub-*) exist
    sub_folders = [p for p in dataset_dir.iterdir() if p.is_dir() and p.name.startswith("sub-")]
    assert len(sub_folders) > 0, "Dataset should contain at least one subject folder (sub-*)."

    # 3. Verify checksums.json exists and is valid JSON
    checksum_file = raw_root / "checksums.json"
    assert checksum_file.is_file(), "Checksum manifest checksums.json should exist."
    
    with open(checksum_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    assert manifest["dataset_id"] == "ds003123", "Manifest should reference dataset ds003123."
    assert len(manifest["files"]) > 0, "Manifest should contain a list of files."
    
    # Verify at least one file in manifest exists on disk
    first_file_rel_path = Path(manifest["files"][0]["path"])
    assert (raw_root / first_file_rel_path).is_file(), "File listed in manifest should exist on disk."