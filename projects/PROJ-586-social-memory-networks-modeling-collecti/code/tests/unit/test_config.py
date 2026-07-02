import os
import tempfile
from pathlib import Path
from utils.config import load_config, save_config, DEFAULT_CONFIG_PATH

def test_save_and_load_config(tmp_path: Path):
    cfg = {"seed": 123, "device": "cpu"}
    cfg_path = tmp_path / "cfg.yaml"
    save_config(cfg, cfg_path)
    loaded = load_config(cfg_path)
    assert loaded == cfg

def test_load_missing_config_returns_empty(tmp_path: Path):
    missing = tmp_path / "does_not_exist.yaml"
    cfg = load_config(missing)
    assert cfg == {}
