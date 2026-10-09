"""Unit tests for the ArchConfig YAML definitions and loader."""

import pytest

from src.config.loader import CONFIG_PATH, get_arch_config, load_arch_configs


def test_config_file_exists():
    assert CONFIG_PATH.exists()


def test_load_all_configs():
    configs = load_arch_configs()
    assert len(configs) >= 5  # enough variations for FR-007 multiple comparisons
    ids = [c["config_id"] for c in configs]
    assert len(ids) == len(set(ids)), "config_ids must be unique"


def test_structural_parameters_present():
    for cfg in load_arch_configs():
        assert isinstance(cfg["context_window_tokens"], int)
        assert cfg["context_window_tokens"] > 0
        assert isinstance(cfg["model_size_params"], int)
        assert cfg["model_size_params"] > 0
        assert isinstance(cfg["retrieval_augmented"], bool)
        assert 0.0 < cfg["temperature"] <= 2.0


def test_get_arch_config():
    cfg = get_arch_config("small_no_rag_high_temp")
    assert cfg["model_name"] == "distilgpt2"
    assert cfg["temperature"] == 0.7
    assert cfg["retrieval_augmented"] is False


def test_get_arch_config_unknown_raises():
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist")