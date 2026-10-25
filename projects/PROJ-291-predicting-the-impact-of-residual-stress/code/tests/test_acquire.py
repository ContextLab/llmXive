"""
test_acquire.py
----------------
Integration test for the external‑dataset acquisition script (task T014).
"""

import json
from pathlib import Path
import pytest
from src.acquire_external import main as acquire_main

CHECKSUMS_PATH = Path("data/raw/checksums.json")
LOG_PATH = Path("data/external/acquisition_log.json")

@pytest.fixture(scope="module")
def run_acquisition():
    acquire_main()
    assert LOG_PATH.is_file(), "Acquisition log was not created"
    assert CHECKSUMS_PATH.is_file(), "Checksums file was not created"
    return {
        "log": json.loads(LOG_PATH.read_text(encoding="utf-8")),
        "checksums": json.loads(CHECKSUMS_PATH.read_text(encoding="utf-8")),
    }

def _file_checksum(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def test_acquisition_log_structure(run_acquisition):
    log = run_acquisition["log"]
    assert "openml" in log and "uci" in log
    for section in ("openml", "uci"):
        assert isinstance(log[section]["candidates"], list)
        assert isinstance(log[section]["acquired"], list)

def test_checksums_match_acquired_files(run_acquisition):
    log = run_acquisition["log"]
    checksums = run_acquisition["checksums"]
    for source in ("openml", "uci"):
        for entry in log[source]["acquired"]:
            if entry.get("status") != "success":
                continue
            file_path = Path(entry["file"])
            assert file_path.is_file()
            actual = _file_checksum(file_path)
            stored = checksums.get(str(file_path))
            assert stored is not None
            assert actual == stored