"""
Unit test for the configuration loader defined in ``src.config.settings``.
It verifies that the loader returns a dictionary containing the required
top‑level keys and that missing keys raise an informative ``KeyError``.
"""

import pytest
from pathlib import Path

from src.config.settings import load_config, _CONFIG_PATH


def test_load_config_success():
    """The loader must return a dict with the expected top‑level sections."""
    cfg = load_config()
    assert isinstance(cfg, dict)
    for key in ("api", "gpr_max_runtime", "gpr_max_memory", "ocr"):
        assert key in cfg


def test_load_config_missing_file(tmp_path, monkeypatch):
    """
    If the configuration file does not exist, ``FileNotFoundError`` should be raised.
    The test temporarily points the loader at a non‑existent file.
    """
    missing_path = tmp_path / "nonexistent.yaml"
    # Monkey‑patch the internal path used by the loader
    monkeypatch.setattr("src.config.settings._CONFIG_PATH", missing_path, raising=False)

    with pytest.raises(FileNotFoundError):
        load_config()


def test_load_config_missing_key(tmp_path, monkeypatch):
    """
    A configuration file that lacks a required top‑level key must raise ``KeyError``.
    """
    bad_cfg = {
        "api": {"materials_project": {}, "nist": {}, "arxiv": {}},
        # intentionally omit gpr_max_runtime and others
    }
    bad_path = tmp_path / "bad_config.yaml"
    bad_path.write_text(
        # Use safe_dump to ensure valid YAML formatting
        __import__("yaml").safe_dump(bad_cfg), encoding="utf-8"
    )
    monkeypatch.setattr("src.config.settings._CONFIG_PATH", bad_path, raising=False)

    with pytest.raises(KeyError) as excinfo:
        load_config()
    assert "missing required keys" in str(excinfo.value).lower()