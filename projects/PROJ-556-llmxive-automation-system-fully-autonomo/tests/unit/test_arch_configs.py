"""Unit tests for src/config/arch_configs.yaml (T006).

Verifies that the ArchConfig definitions load through the existing
``src.config.loader`` API and define the structural parameters
(context window, model size, retrieval toggle) required by the
correlation analysis in US-3.
"""
from __future__ import annotations

import pytest

from src.config.loader import get_arch_config, load_arch_configs


def test_loads_all_configs():
    configs = load_arch_configs()
    assert isinstance(configs, list)
    assert len(configs) >= 5


def test_structural_parameters_present():
    for cfg in load_arch_configs():
        assert cfg["context_window_tokens"] > 0
        assert cfg["model_size_params"] > 0
        assert isinstance(cfg["retrieval_augmented"], bool)
        assert 0.0 < cfg["temperature"] <= 2.0
        assert 0.0 < cfg["top_p"] <= 1.0


def test_unique_config_ids():
    configs = load_arch_configs()
    ids = [c["config_id"] for c in configs]
    assert len(ids) == len(set(ids))


def test_retrieval_toggle_varies():
    """RAG must be toggled across configs to serve as a fixed effect."""
    flags = {c["retrieval_augmented"] for c in load_arch_configs()}
    assert flags == {True, False}


def test_model_size_varies():
    """Model size must vary to support the model-scale correlation (SC-003)."""
    sizes = {c["model_size_params"] for c in load_arch_configs()}
    assert len(sizes) >= 2


def test_get_arch_config_known_id():
    cfg = get_arch_config("small_no_rag_high_temp")
    assert cfg["model_name"] == "distilgpt2"
    assert cfg["temperature"] == 0.7


def test_get_arch_config_unknown_id_raises():
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist")