"""Tests for the ``src.config.loader`` module."""

import pathlib

import pytest

from src.config.loader import load_arch_configs, get_arch_config, CONFIG_PATH


def test_load_arch_configs_returns_list():
    """The loader should return a non‑empty list of dicts."""
    configs = load_arch_configs()
    assert isinstance(configs, list)
    assert len(configs) > 0
    for cfg in configs:
        assert isinstance(cfg, dict)
        assert "config_id" in cfg


def test_get_arch_config_valid_id():
    """Retrieving a known config_id should return the matching dict."""
    # Use the first config id from the default file
    first_cfg = load_arch_configs()[0]
    cfg_id = first_cfg["config_id"]
    retrieved = get_arch_config(cfg_id)
    assert retrieved == first_cfg


def test_get_arch_config_invalid_id_raises():
    """Requesting a non‑existent config_id must raise KeyError."""
    with pytest.raises(KeyError):
        get_arch_config("non_existent_config_id")


def test_load_arch_configs_missing_file(tmp_path: pathlib.Path):
    """If the YAML file does not exist, a FileNotFoundError should be raised."""
    missing_path = tmp_path / "does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        load_arch_configs(missing_path)