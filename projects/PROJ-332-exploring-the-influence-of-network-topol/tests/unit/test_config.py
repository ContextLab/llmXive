import os
import pytest
from config import load_config, SimulationConfig

def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv("SIM_N", "123")
    monkeypatch.setenv("SIM_P", "0.04")
    monkeypatch.setenv("SIM_D", "50")
    monkeypatch.setenv("SIM_L", "1000")
    monkeypatch.setenv("SIM_SEED", "99")
    monkeypatch.setenv("SIM_TARGET_DEGREE", "4.5")
    cfg = load_config()
    assert isinstance(cfg, SimulationConfig)
    assert cfg.N == 123
    assert cfg.p == 0.04
    assert cfg.d == 50.0
    assert cfg.l == 1000.0
    assert cfg.seed == 99
    assert cfg.target_degree == 4.5

def test_simulation_config_missing_attribute_no_error():
    cfg = SimulationConfig()
    # Accessing an undefined attribute should not raise
    assert callable(cfg.some_random_attribute)
    # The returned callable should be a no‑op (returns None)
    assert cfg.some_random_attribute(1, key="value") is None