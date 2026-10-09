"""
Integration test for T005-baseline-fetch.

Asserts that ``data/raw/gfm_baseline.pt`` exists and that its SHA-256
checksum matches the recorded checksum sidecar
``data/raw/gfm_baseline.pt.sha256`` written by ``code/fetch_baseline.py``.
"""

import hashlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from fetch_baseline import DEST_PATH, CHECKSUM_PATH, compute_sha256


def test_baseline_file_exists():
    assert DEST_PATH.is_file(), (
        f"Baseline model file missing: {DEST_PATH}. "
        "Run 'python code/fetch_baseline.py' to fetch it."
    )
    assert DEST_PATH.stat().st_size > 0


def test_baseline_checksum_matches():
    assert CHECKSUM_PATH.is_file(), (
        f"Checksum sidecar missing: {CHECKSUM_PATH}. "
        "Run 'python code/fetch_baseline.py' to (re)generate it."
    )
    expected = CHECKSUM_PATH.read_text(encoding="utf-8").strip()
    actual = compute_sha256(DEST_PATH)
    assert hashlib.sha256(actual.encode()).hexdigest()  # sanity
    assert actual == expected, (
        f"Checksum mismatch: expected {expected}, got {actual}"
    )
