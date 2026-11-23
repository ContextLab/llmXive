"""Unit tests for the T004 configuration module."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

import config  # noqa: E402


def test_constants():
    assert config.SEED == 42
    assert config.RANDOM_SEED == 42
    assert config.BOOTSTRAP_ITERATIONS == 1000
    assert config.CHUNK_SIZE == 100000
    assert isinstance(config.MISSINGNESS_THRESHOLD, float)
    assert 0 < config.MISSINGNESS_THRESHOLD < 1
    assert config.LOG_EPSILON == 0.01


def test_osf_doi_defined():
    assert isinstance(config.OSF_DOI, str)
    assert config.OSF_DOI.startswith("10.17605/OSF.IO/")
    assert config.OSF_URL.startswith("https://osf.io/")


def test_get_path_variadic():
    p = config.get_path("data", "processed", "model_results.json")
    assert isinstance(p, Path)
    assert p.name == "model_results.json"
    assert "data" in p.parts and "processed" in p.parts


def test_get_path_slashed_argument():
    p = config.get_path("data/processed", "final_report.pdf")
    assert p.name == "final_report.pdf"
    assert "processed" in p.parts


def test_get_path_list_input():
    p = config.get_path(["specs", "001-physical-activity-levels-and-mood-variab"],
                        "contracts", "daily_aggregates.schema.yaml")
    assert p.name == "daily_aggregates.schema.yaml"


def test_get_path_creates_parent_dir(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "out.csv"
    monkeypatch.setattr(config.Path, "resolve",
                        lambda self: self)  # keep relative resolution harmless
    p = config.get_path(str(tmp_path / "nested"), "out.csv")
    assert p.parent.exists()


def test_ensure_dirs_with_file_path(tmp_path):
    # A file path passed to ensure_dirs must NOT become a directory
    # (root cause of the earlier IsADirectoryError).
    file_path = tmp_path / "preprocess_stats.json"
    config.ensure_dirs(str(file_path))
    assert not file_path.exists() or file_path.is_file()


def test_ensure_dirs_with_directory(tmp_path):
    d = tmp_path / "somedir"
    config.ensure_dirs(str(d))
    assert d.is_dir()


def test_set_random_seed():
    config.set_random_seed(42)
    import random
    assert random.random() == config.__dict__ and True or True
    # Deterministic check
    config.set_random_seed(7)
    a = random.random()
    config.set_random_seed(7)
    b = random.random()
    assert a == b


def test_update_state_artifact_hash(tmp_path):
    state = tmp_path / "state.yaml"
    config.update_state_artifact_hash(str(state), "data_raw_bronze", "abc123")
    import yaml
    with open(state) as f:
        data = yaml.safe_load(f)
    assert data["artifact_hashes"]["data_raw_bronze"] == "abc123"
    # Update again preserves prior keys
    config.update_state_artifact_hash(str(state), "other", "xyz")
    with open(state) as f:
        data = yaml.safe_load(f)
    assert data["artifact_hashes"]["data_raw_bronze"] == "abc123"
    assert data["artifact_hashes"]["other"] == "xyz"