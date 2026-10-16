import json
from pathlib import Path

from llmxive_toolkit import paths
from init_state_artifacts import ensure_state_artifact_hashes, ensure_checksums_manifest

def test_state_artifact_hashes_initialisation(tmp_path: Path, monkeypatch):
    # Redirect the platform paths to a temporary directory
    monkeypatch.setattr(paths, "state", lambda *parts: tmp_path.joinpath(*parts))
    # Ensure the file does not exist initially
    target = paths.state("artifact_hashes.json")
    if target.exists():
        target.unlink()
    ensure_state_artifact_hashes()
    assert target.exists()
    with target.open("r", encoding="utf-8") as f:
        assert json.load(f) == {}

def test_checksums_manifest_initialisation(tmp_path: Path, monkeypatch):
    # Redirect the data path to a temporary directory
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path.joinpath(*parts))
    target = paths.data("checksums.json")
    if target.exists():
        target.unlink()
    ensure_checksums_manifest()
    assert target.exists()
    with target.open("r", encoding="utf-8") as f:
        assert json.load(f) == {}