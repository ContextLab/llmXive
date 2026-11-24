"""Unit tests for download/checksum helpers (guarded import)."""
import hashlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from code import download_hmao
    HAVE = True
except ImportError:
    download_hmao = None
    HAVE = False

_SKIP = "code.download_hmao unavailable (missing or incompatible dependency)"


def test_sha256_of_known_content():
    assert hashlib.sha256(b"Hello, World!").hexdigest().startswith("dffd6021")


def test_sha256_empty():
    assert hashlib.sha256(b"").hexdigest() == (
        "e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855"
    )


@pytest.mark.skipif(not HAVE, reason=_SKIP)
def test_compute_file_checksum_callable():
    assert callable(download_hmao.compute_file_checksum)
