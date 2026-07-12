"""Contract test for the ``download_file`` utility.

The test verifies two behaviours:

1. A file is correctly downloaded when the supplied checksum matches.
2. A ``ValueError`` is raised when the checksum does not match.
"""

import hashlib
import urllib.request
from pathlib import Path

import pytest

from src.data.download import download_file

def _sha256(path: Path) -> str:
    """Helper to compute SHA‑256 of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def test_download_and_checksum_verification(tmp_path: Path):
    # Small, stable file hosted on GitHub – suitable for CI.
    url = "https://raw.githubusercontent.com/physionet/physionet.github.io/master/README.md"
    dest = tmp_path / "README.md"

    # First, obtain the correct checksum using a direct download.
    urllib.request.urlretrieve(url, dest)
    expected_checksum = _sha256(dest)

    # Remove the file so that ``download_file`` performs the download itself.
    dest.unlink()

    # The function should download the file and verify the checksum.
    result_path = download_file(url, dest, expected_checksum)
    assert result_path == dest
    assert result_path.is_file()
    assert _sha256(result_path) == expected_checksum

    # Supplying an incorrect checksum must raise ``ValueError``.
    with pytest.raises(ValueError):
        download_file(url, dest, "0" * 64)