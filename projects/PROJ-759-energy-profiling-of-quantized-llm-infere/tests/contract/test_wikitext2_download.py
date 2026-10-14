"""
Contract test for the WikiText‑2 downloader.

This test mirrors the logic in the main test suite but lives under the
``tests/contract`` namespace as required by the quickstart verification step.
"""

import re
import hashlib
from pathlib import Path

from utils.data_loader import download_wikitext2


def _compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_wikitext2_download_contract():
    # Ensure a clean state
    raw_dir = Path("data") / "raw"
    parquet_path = raw_dir / "wikitext2.parquet"
    readme_path = raw_dir / "README.md"

    if parquet_path.is_file():
        parquet_path.unlink()
    if readme_path.is_file():
        readme_path.unlink()

    # Run download
    result = download_wikitext2()
    assert result == parquet_path
    assert parquet_path.is_file()
    assert readme_path.is_file()

    # Verify checksum in README matches actual file checksum
    readme_text = readme_path.read_text(encoding="utf-8")
    match = re.search(r"`([a-f0-9]{64})`", readme_text)
    assert match, "Checksum not found in README"
    recorded = match.group(1)
    actual = _compute_sha256(parquet_path)
    assert recorded == actual, "Checksum mismatch"