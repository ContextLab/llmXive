"""
Contract test for the WikiText‑2 data‑loader.

The test ensures that ``download_wikitext2`` creates a Parquet file at
``data/raw/wikitext2.parquet`` and that the SHA‑256 checksum recorded in
``data/raw/README.md`` matches the actual file.
"""

import hashlib
from pathlib import Path

import pytest

from utils.data_loader import download_wikitext2

@pytest.fixture(scope="module", autouse=True)
def ensure_data():
    # Run the downloader once for the whole test module.
    download_wikitext2()
    yield
    # No teardown needed; the file is kept for downstream tests.

def test_parquet_exists():
    parquet_path = Path("data") / "raw" / "wikitext2.parquet"
    assert parquet_path.is_file(), f"Missing {parquet_path}"

def test_checksum_matches():
    parquet_path = Path("data") / "raw" / "wikitext2.parquet"
    readme_path = Path("data") / "raw" / "README.md"
    assert readme_path.is_file(), f"Missing {readme_path}"
    # Extract the checksum from the README (the line containing backticks)
    content = readme_path.read_text(encoding="utf-8")
    import re

    match = re.search(r"`([a-f0-9]{64})`", content)
    assert match, "Checksum not found in README"
    recorded_checksum = match.group(1)

    # Compute actual checksum
    h = hashlib.sha256()
    with parquet_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    actual_checksum = h.hexdigest()
    assert actual_checksum == recorded_checksum, "Checksum mismatch"