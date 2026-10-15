import json
import hashlib
from pathlib import Path

from llmxive_toolkit import paths
from download_data import main as download_main

def test_download_and_checksum(tmp_path, monkeypatch):
    """
    End‑to‑end test for the download_data script.

    It uses the bundled example CSV (accessed via a file:// URL) and checks that:
    1. The file is copied to data/raw/example_dataset.csv.
    2. A checksums.txt file is created.
    3. The recorded checksum matches the actual file checksum.
    """
    # Ensure a clean state.
    raw_dir = paths.data("raw")
    if raw_dir.is_dir():
        for p in raw_dir.iterdir():
            p.unlink()
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Run the download script.
    download_main()

    # Verify the CSV was downloaded.
    downloaded_csv = raw_dir / "example_dataset.csv"
    assert downloaded_csv.is_file(), "CSV file was not created in data/raw"

    # Verify checksums.txt exists and contains a correct entry.
    checksums_path = raw_dir / "checksums.txt"
    assert checksums_path.is_file(), "checksums.txt was not created"

    # Compute actual checksum of the downloaded file.
    sha256 = hashlib.sha256()
    with downloaded_csv.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual_checksum = sha256.hexdigest()

    # Read the recorded checksum.
    with checksums_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) == 1, "Expected exactly one checksum line"
    recorded_checksum, recorded_name = lines[0].split(maxsplit=1)
    assert recorded_name == downloaded_csv.name, "Filename in checksum line mismatch"
    assert recorded_checksum == actual_checksum, "Recorded checksum does not match actual file checksum"