"""
Unit tests for ``src.utils.verify_requirements``.
"""

import sys
from pathlib import Path

import pytest

from src.utils.verify_requirements import check_requirements, _sha256

# Helper to create a temporary requirements file
@pytest.fixture
def temp_requirements(tmp_path: Path, monkeypatch):
    """Create a minimal requirements.txt in the repository root."""
    repo_root = Path(__file__).resolve().parents[2]  # project root
    req_path = repo_root / "requirements.txt"
    # Backup any existing file
    backup = None
    if req_path.is_file():
        backup = req_path.read_text()
    req_path.write_text("numpy\npandas\n", encoding="utf-8")
    # Ensure a clean manifest entry for the test
    manifest_path = repo_root / "data" / "artifact_hashes.yaml"
    if manifest_path.is_file():
        manifest = yaml.safe_load(manifest_path.read_text()) or {}
    else:
        manifest = {}
    manifest["requirements.txt"] = _sha256(req_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    yield
    # Restore original file if it existed
    if backup is not None:
        req_path.write_text(backup, encoding="utf-8")
    else:
        req_path.unlink(missing_ok=True)

def test_check_requirements_success(temp_requirements):
    """The check should succeed when the file exists, is non‑empty and hash matches."""
    assert check_requirements() is True
    # Verify that the log file contains a SUCCESS line
    from llmxive_toolkit import paths
    log_path = paths.data("requirements_check.log")
    assert log_path.is_file()
    content = log_path.read_text()
    assert "SUCCESS: requirements.txt verification completed." in content

def test_check_requirements_missing(monkeypatch):
    """Missing requirements.txt should cause failure."""
    repo_root = Path(__file__).resolve().parents[2]
    req_path = repo_root / "requirements.txt"
    # Ensure the file is removed for this test
    req_path.unlink(missing_ok=True)
    assert check_requirements() is False

def test_check_requirements_empty(monkeypatch):
    """Empty requirements.txt should cause failure."""
    repo_root = Path(__file__).resolve().parents[2]
    req_path = repo_root / "requirements.txt"
    req_path.write_text("", encoding="utf-8")
    assert check_requirements() is False