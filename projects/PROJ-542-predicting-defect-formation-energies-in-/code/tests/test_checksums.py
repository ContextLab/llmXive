"""
code/tests/test_checksums.py
--------------------------------

Verify that the checksum utility correctly hashes a file and writes the
expected ``<filename>.sha256`` file to the supplied output directory.
"""

import hashlib
from pathlib import Path

from src.utils.checksum import compute_checksum, write_checksum

def test_write_checksum(tmp_path: Path):
    # Create a small temporary file with known contents.
    data_file = tmp_path / "sample.txt"
    content = "llmXive checksum test"
    data_file.write_text(content, encoding="utf-8")

    # Destination directory for the checksum file.
    out_dir = tmp_path / "checksums"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use the convenience wrapper.
    write_checksum(data_file, out_dir)

    # Expected checksum filename.
    checksum_file = out_dir / "sample.txt.sha256"
    assert checksum_file.is_file(), "Checksum file was not created"

    # Verify that the checksum is a valid 64‑character hex string.
    checksum_text = checksum_file.read_text().strip()
    assert len(checksum_text) == 64
    assert all(c in "0123456789abcdefABCDEF" for c in checksum_text)

    # Compute the expected SHA‑256 digest directly.
    expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert checksum_text == expected, "Checksum does not match file contents"