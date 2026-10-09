"""
test_setup_structure.py
-----------------------

Simple sanity test that verifies the ``data/setup_log.json`` file created
by ``create_project_structure.py`` exists and contains a successful status.
"""

import json
from pathlib import Path

def _repo_root() -> Path:
    # This test resides in ``tests/`` at the repository root.
    # Going up two levels reaches the repository root.
    return Path(__file__).resolve().parents[2]

def test_setup_log_exists_and_successful():
    root = _repo_root()
    log_path = root / "data" / "setup_log.json"

    assert log_path.is_file(), f"Expected setup log at {log_path}"

    with log_path.open(encoding="utf-8") as f:
        content = json.load(f)

    assert content.get("status") == "SUCCESS", "Setup log status should be SUCCESS"
    assert isinstance(content.get("paths_verified"), list), "paths_verified should be a list"
    assert "timestamp" in content, "setup log must contain a timestamp"