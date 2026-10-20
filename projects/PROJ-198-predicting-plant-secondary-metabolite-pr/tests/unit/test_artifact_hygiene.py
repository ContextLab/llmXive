"""
Unit tests for the artifact‑hygiene utilities.
"""

import hashlib
from pathlib import Path

import pytest

from utils.artifact import record_artifacts, STATE_FILE, _load_state, track_path

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known contents."""
    p = tmp_path / "sample.txt"
    p.write_text("llmXive artifact test")
    return p

def test_compute_sha256_matches_manual(temp_file):
    """The internal SHA‑256 computation must match hashlib directly."""
    # Import the private helper via attribute access
    compute = getattr(__import__("code.utils.artifact", fromlist=["_compute_sha256"]), "_compute_sha256")
    manual = hashlib.sha256(b"llmXive artifact test").hexdigest()
    assert compute(temp_file) == manual

def test_record_and_load_state(temp_file):
    """record_artifacts should write a correct entry and _load_state should read it."""
    # Ensure a clean state file
    if STATE_FILE.is_file():
        STATE_FILE.unlink()
    record_artifacts([temp_file])
    state = _load_state()
    rel = temp_file.resolve().relative_to(Path(__file__).parents[3])
    assert str(rel) in state
    # Verify stored hash matches manual hash
    expected = hashlib.sha256(temp_file.read_bytes()).hexdigest()
    assert state[str(rel)] == expected

def test_track_path_and_atexit(tmp_path, monkeypatch):
    """track_path should register the path for atexit flushing."""
    p = tmp_path / "deferred.txt"
    p.write_text("deferred")
    # Monkey‑patch the atexit registry to call our flush directly
    from utils.artifact import _flush_pending
    track_path(p)
    _flush_pending()  # force write
    state = _load_state()
    rel = p.resolve().relative_to(Path(__file__).parents[3])
    assert str(rel) in state
