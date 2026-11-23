"""Tests for the project-owned artifact hash registry (T007)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from utils import update_state as us


def test_compute_file_hash_roundtrip(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    h = us.compute_file_hash(f)
    assert len(h) == 64
    assert us.get_artifact_hash(f) == h


def test_update_state_writes_project_owned_registry(tmp_path, monkeypatch):
    # Redirect registry into tmp so the test doesn't touch real data/
    monkeypatch.setattr(us, "ARTIFACT_REGISTRY_PATH", tmp_path / "data" / "processed" / "artifact_hashes.yaml")
    monkeypatch.setattr(us, "PROJECT_ROOT", tmp_path)

    art = tmp_path / "x.csv"
    art.write_text("a,b\n1,2\n")

    us.update_state("PROJ-066-investigating-correlations-between-molec",
                    [{"artifact_path": "x.csv", "source": "test"}])

    state = us.load_state_file("PROJ-066-investigating-correlations-between-molec")
    assert state["last_updated"] is not None
    assert len(state["artifacts"]) == 1
    entry = state["artifacts"][0]
    assert entry["artifact_path"] == "x.csv"
    assert entry["hash"] == us.compute_file_hash(art)

    # Idempotent update: same path updates, does not duplicate
    us.update_state("PROJ-066-investigating-correlations-between-molec",
                    [{"artifact_path": "x.csv", "source": "test2"}])
    state = us.load_state_file("PROJ-066-investigating-correlations-between-molec")
    assert len(state["artifacts"]) == 1
    assert state["artifacts"][0]["source"] == "test2"

    # Registry must be inside project-owned data/, never state/
    assert "state" not in str(us.ARTIFACT_REGISTRY_PATH)
    assert us.ARTIFACT_REGISTRY_PATH.exists()


def test_verify_artifact_integrity(tmp_path, monkeypatch):
    monkeypatch.setattr(us, "PROJECT_ROOT", tmp_path)
    art = tmp_path / "y.bin"
    art.write_bytes(b"data")
    h = us.compute_file_hash(art)
    assert us.verify_artifact_integrity("p", "y.bin", h) is True
    assert us.verify_artifact_integrity("p", "y.bin", "0" * 64) is False
    assert us.verify_artifact_integrity("p", "missing.bin", h) is False


def test_update_state_requires_path():
    import pytest
    with pytest.raises(ValueError):
        us.update_state("p", [{"hash": "abc"}])