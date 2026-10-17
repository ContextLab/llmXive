import os
import yaml
from src.config import load_config, get_config_value, DEFAULT_CONFIG

def test_load_config_returns_defaults_when_no_file(tmp_path):
    # Ensure no config file exists
    config_path = tmp_path / "config.yaml"
    if config_path.exists():
        config_path.unlink()
    # Temporarily point CONFIG_PATH to the temp location
    from src import config as cfg
    original_path = cfg.CONFIG_PATH
    cfg.CONFIG_PATH = config_path
    try:
        cfg.ensure_config_file()
        loaded = cfg.load_config()
        assert loaded == DEFAULT_CONFIG
    finally:
        cfg.CONFIG_PATH = original_path

def test_get_config_value_priority():
    # Override a value via a temporary config file
    temp_cfg = {
        "MODEL_TEMP": 0.9,
        "RANDOM_SEED": 123,
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(temp_cfg, f)
    from src import config as cfg
    original_path = cfg.CONFIG_PATH
    cfg.CONFIG_PATH = config_path
    try:
        assert cfg.get_config_value("MODEL_TEMP") == 0.9
        # Fallback to default when key missing
        assert cfg.get_config_value("NON_EXISTENT_KEY", "fallback") == "fallback"
    finally:
        cfg.CONFIG_PATH = original_path