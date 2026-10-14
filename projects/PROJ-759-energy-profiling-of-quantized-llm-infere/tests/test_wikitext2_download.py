"""
Test that the WikiText-2 dataset downloader creates the parquet file
and writes a correct SHA‑256 checksum to the accompanying README.
"""

import re
import hashlib
from pathlib import Path

from utils.data_loader import download_wikitext2


def _compute_sha256(file_path: Path) -> str:
    """Helper to compute SHA‑256 of a file (mirrors internal implementation)."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_wikitext2_download(tmp_path, monkeypatch):
    """
    Verify that download_wikitext2 writes the parquet file and a README
    containing the correct checksum.

    The function is exercised with its default location (project data folder).
    """
    # Ensure a clean state: remove any existing files in the data/raw directory
    raw_dir = Path("data") / "raw"
    parquet_path = raw_dir / "wikitext2.parquet"
    readme_path = raw_dir / "README.md"

    if parquet_path.is_file():
        parquet_path.unlink()
    if readme_path.is_file():
        readme_path.unlink()

    # Run the downloader (uses the real dataset source)
    result_path = download_wikitext2()

    # The function should return the exact parquet path
    assert result_path == parquet_path
    assert result_path.is_file(), f"Parquet file not found at {result_path}"

    # Verify README exists
    assert readme_path.is_file(), "README.md not created"

    # Extract checksum from README
    readme_text = readme_path.read_text(encoding="utf-8")
    match = re.search(r"`([a-f0-9]{64})`", readme_text)
    assert match, "Checksum not found in README"
    recorded_checksum = match.group(1)

    # Compute actual checksum of the parquet file
    actual_checksum = _compute_sha256(parquet_path)

    assert recorded_checksum == actual_checksum, (
        "Recorded checksum does not match computed checksum"
    )

    # Clean up (optional, leave files for downstream tasks)
    # parquet_path.unlink()
    # readme_path.unlink()