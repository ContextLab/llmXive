"""Tests for the configuration utilities."""
import os
import tempfile
from pathlib import Path

from utils.config import load_config, save_config, DEFAULT_CONFIG_PATH

def test_save_and_load_config(tmp_path: Path):
    cfg = {"seed": 123, "device": "cpu"}
    path = tmp_path / "my_config.yaml"
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded == cfg

def test_load_missing_config_returns_empty():
    with tempfile.TemporaryDirectory() as td:
        missing = Path(td) / "does_not_exist.yaml"
        cfg = load_config(missing)
        assert cfg == {}