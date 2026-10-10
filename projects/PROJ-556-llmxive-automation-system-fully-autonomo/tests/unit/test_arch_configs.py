"""Unit tests for src/config/arch_configs.yaml (T006).

Validates that the ArchConfig definitions file loads through the
existing loader API and defines the structural parameters required
by the spec (context window, model size, retrieval toggle).
"""
from __future__ import annotations

import pytest

from src.config.loader import get_arch_config, load_arch_configs

REQUIRED_KEYS = {
    "config_id",
    "model_name",
    "model_size_params",
    "context_window_tokens",
    "retrieval_augmented",
    "temperature",
    "top_p",
}


def test_load_arch_configs_returns_entries():
    configs = load_arch_configs()
    assert len(configs) >= 5, "expected at least 5 ArchConfig variations"
    for cfg in configs:
        missing = REQUIRED_KEYS - set(cfg.keys())
        assert not missing, f"{cfg.get('config_id')} missing keys: {missing}"


def test_structural_parameters_vary():
    """Structural params must vary across configs to support the
    correlation analysis (US-3); otherwise the study is tautological."""
    configs = load_arch_configs()
    sizes = {c["model_size_params"] for c in configs}
    windows = {c["context_window_tokens"] for c in configs}
    rag = {c["retrieval_augmented"] for c in configs}
    assert len(sizes) >= 2, "model_size_params must vary"
    assert len(windows) >= 1
    assert rag == {True, False}, "retrieval_augmented must be toggled"


def test_get_arch_config_by_id():
    cfg = get_arch_config("small_rag_high_temp")
    assert cfg["config_id"] == "small_rag_high_temp"
    assert cfg["retrieval_augmented"] is True
    assert cfg["temperature"] == 0.7


def test_get_arch_config_unknown_id_raises():
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist")


def test_execution_constraints_present():
    import pathlib

    import yaml

    path = pathlib.Path("src/config/arch_configs.yaml")
    data = yaml.safe_load(path.read_text())
    exec_cfg = data["execution"]
    assert exec_cfg["timeout_seconds_per_attempt"] == 60
    assert exec_cfg["memory_error_retries"] == 1
    assert exec_cfg["determinism_check_runs"] == 3
    assert data["resources"]["device"] == "cpu"
    assert data["resources"]["max_ram_gb"] <= 7