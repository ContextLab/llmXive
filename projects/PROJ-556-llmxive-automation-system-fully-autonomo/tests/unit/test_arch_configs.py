"""Unit tests for the ArchConfig YAML definition (T006)."""
from __future__ import annotations

import pytest

from src.config.loader import get_arch_config, load_arch_configs

EXPECTED_IDS = {
    "small_no_rag_low_temp",
    "small_no_rag_high_temp",
    "small_rag_high_temp",
    "medium_no_rag_high_temp",
    "medium_rag_high_temp",
}

REQUIRED_KEYS = {
    "config_id",
    "model_name",
    "model_size_params",
    "context_window_tokens",
    "retrieval_augmented",
    "temperature",
    "top_p",
}


def test_all_configs_load_and_validate():
    configs = load_arch_configs()
    assert len(configs) == 5
    assert {c["config_id"] for c in configs} == EXPECTED_IDS


@pytest.mark.parametrize("config_id", sorted(EXPECTED_IDS))
def test_required_structural_params_present(config_id):
    cfg = get_arch_config(config_id)
    missing = REQUIRED_KEYS - set(cfg)
    assert not missing, f"{config_id} missing keys: {missing}"
    assert isinstance(cfg["context_window_tokens"], int)
    assert isinstance(cfg["model_size_params"], int)
    assert isinstance(cfg["retrieval_augmented"], bool)
    assert 0.0 < cfg["temperature"] <= 2.0


def test_rag_configs_declare_top_k():
    for cid in ("small_rag_high_temp", "medium_rag_high_temp"):
        cfg = get_arch_config(cid)
        assert cfg["retrieval_augmented"] is True
        assert isinstance(cfg["retrieval_top_k"], int) and cfg["retrieval_top_k"] > 0


def test_structural_variation_exists():
    """Model size and retrieval toggle must vary across configs (US-3 IVs)."""
    configs = load_arch_configs()
    sizes = {c["model_size_params"] for c in configs}
    rags = {c["retrieval_augmented"] for c in configs}
    assert len(sizes) >= 2, "model_size_params must vary for correlation analysis"
    assert rags == {True, False}, "retrieval_augmented must have both arms"


def test_unknown_config_raises():
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist")