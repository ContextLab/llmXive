"""Unit tests for the ArchConfig definitions in src/config/arch_configs.yaml."""

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
    assert isinstance(configs, list)
    assert len(configs) >= 5


def test_every_config_has_required_keys():
    for cfg in load_arch_configs():
        missing = REQUIRED_KEYS - set(cfg)
        assert not missing, f"{cfg.get('config_id')} missing keys: {missing}"


def test_structural_parameters_vary():
    """Structural parameters must actually vary to support the US-3 correlation."""
    configs = load_arch_configs()
    sizes = {c["model_size_params"] for c in configs}
    rag = {c["retrieval_augmented"] for c in configs}
    assert len(sizes) >= 2, "model_size_params must vary across configs"
    assert rag == {True, False}, "retrieval_augmented must include both on/off"


def test_cpu_tractable_models():
    for cfg in load_arch_configs():
        assert cfg["model_size_params"] <= 500_000_000, (
            f"{cfg['config_id']} exceeds CPU-tractable size"
        )
        assert cfg["context_window_tokens"] <= 4096


def test_get_arch_config_known_id():
    cfg = get_arch_config("small_no_rag_high_temp")
    assert cfg["model_name"] == "distilgpt2"
    assert cfg["temperature"] == 0.7


def test_get_arch_config_unknown_id_raises():
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist")