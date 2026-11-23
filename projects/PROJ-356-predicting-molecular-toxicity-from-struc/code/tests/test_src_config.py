"""Tests for the src.config path-management package (T012)."""

import os
import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from src.config import (
    PROJECT_CODE_DIR,
    ENV_VAR_MAP,
    get_project_dir,
    get_paths,
    get_path,
    resolve_path,
    ensure_directories,
    get_alerts_config_path,
    get_alerts_schema_path,
)


class TestDefaultPaths:
    def test_project_dir_defaults_to_repo(self):
        assert get_project_dir() == PROJECT_CODE_DIR.parent

    def test_all_path_keys_present(self):
        paths = get_paths()
        for key in [
            "project",
            "code",
            "data",
            "data_raw",
            "data_processed",
            "results",
            "models",
            "config",
            "state",
            "docs",
        ]:
            assert key in paths

    def test_paths_are_absolute(self):
        for p in get_paths().values():
            assert p.is_absolute()

    def test_data_raw_under_data(self):
        paths = get_paths()
        assert paths["data_raw"].parent == paths["data"]

    def test_get_path_unknown_name_raises(self):
        with pytest.raises(KeyError):
            get_path("nonexistent_path_name")

    def test_resolve_path_joins_components(self):
        p = resolve_path("results", "metrics.json")
        assert p.name == "metrics.json"
        assert p.parent == get_path("results")

    def test_alerts_config_path(self):
        p = get_alerts_config_path()
        assert p.name == "structural_alerts.json"

    def test_alerts_schema_path(self):
        p = get_alerts_schema_path()
        assert p.name == "alerts.schema.yaml"

class TestEnvOverrides:
    def test_project_dir_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TOXICITY_PROJECT_DIR", str(tmp_path))
        assert get_project_dir() == tmp_path.resolve()

    def test_results_dir_override(self, monkeypatch, tmp_path):
        override = tmp_path / "custom_results"
        monkeypatch.setenv("TOXICITY_RESULTS_DIR", str(override))
        assert get_path("results") == override

    def test_data_raw_override(self, monkeypatch, tmp_path):
        override = tmp_path / "raw"
        monkeypatch.setenv("TOXICITY_RAW_DATA_DIR", str(override))
        assert get_path("data_raw") == override

    def test_env_var_map_names(self):
        assert ENV_VAR_MAP["results"] == "TOXICITY_RESULTS_DIR"
        assert ENV_VAR_MAP["data_raw"] == "TOXICITY_RAW_DATA_DIR"

    def test_ensure_directories_creates(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TOXICITY_RESULTS_DIR", str(tmp_path / "r"))
        monkeypatch.setenv("TOXICITY_MODELS_DIR", str(tmp_path / "m"))
        created = ensure_directories(["results", "models"])
        assert created["results"].is_dir()
        assert created["models"].is_dir()