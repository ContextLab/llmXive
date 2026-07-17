"""Unit tests for code/config.py"""
import pytest
from pathlib import Path
from config import get_config

def test_get_config_returns_dict():
    """Verify get_config returns a dictionary"""
    cfg = get_config()
    assert isinstance(cfg, dict)

def test_get_config_has_required_keys():
    """Verify config contains required keys"""
    cfg = get_config()
    assert "paths" in cfg
    assert "seeds" in cfg
    assert "hyperparameters" in cfg

def test_paths_are_pathlib_objects():
    """Verify path values are Path objects"""
    cfg = get_config()
    assert isinstance(cfg["paths"]["project_root"], Path)
    assert isinstance(cfg["paths"]["data_raw"], Path)
    assert isinstance(cfg["paths"]["data_derived"], Path)
    assert isinstance(cfg["paths"]["tests"], Path)

def test_seeds_are_integers():
    """Verify random seeds are integers"""
    cfg = get_config()
    assert isinstance(cfg["seeds"]["global_seed"], int)

def test_hyperparameters_have_thresholds():
    """Verify hyperparameters include collapse thresholds"""
    cfg = get_config()
    hp = cfg["hyperparameters"]
    assert "sss_threshold" in hp
    assert "wer_spike_factor" in hp
