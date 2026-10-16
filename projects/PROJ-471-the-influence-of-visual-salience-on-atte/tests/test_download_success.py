"""
Test that ``code/ingestion/download_data.py`` succeeds when the dataset is present
and that it creates a valid ``checksums.json`` manifest.
"""
import json
from pathlib import Path

def test_download_success(tmp_path):
    """
    Create a minimal fake dataset structure, run the ingestion script,
    and verify that a checksums manifest is produced and contains entries
    for the created files.
    """
    # Arrange: create a tiny fake dataset under the expected location
    raw_root = Path("data/raw/ds003123")
    raw_root.mkdir(parents=True, exist_ok=True)
    (raw_root / "sub-01").mkdir(exist_ok=True)
    sample_file = raw_root / "sub-01" / "sample.txt"
    sample_file.write_text("test content", encoding="utf-8")

    # Act: import and run the script's main function
    from code.ingestion.download_data import main as ingestion_main
    ingestion_main()

    # Assert: checksums.json exists and lists the sample file
    checksum_path = Path("data/raw/checksums.json")
    assert checksum_path.exists(), "checksums.json was not created"

    manifest = json.loads(checksum_path.read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "ds003123"
    file_entries = [f["path"] for f in manifest["files"]]
    expected_rel = str(sample_file.relative_to(Path("data")))
    assert expected_rel in file_entries, f"{expected_rel} not recorded in manifest"