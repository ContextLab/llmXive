"""Unit tests for the ArchConfig definitions in src/config/arch_configs.yaml."""

from __future__ import annotations

import pytest
import yaml

from src.config.loader import get_arch_config, load_arch_configs

CONFIG_PATH = "src/config/arch_configs.yaml"

EXPECTED_CONFIG_IDS = {
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


def test_configs_load_and_validate():
    configs = load_arch_configs(CONFIG_PATH)
    assert {c["config_id"] for c in configs} == EXPECTED_CONFIG_IDS


@pytest.mark.parametrize("config_id", sorted(EXPECTED_CONFIG_IDS))
def test_required_keys_present(config_id):
    entry = get_arch_config(config_id, CONFIG_PATH)
    for key in REQUIRED_KEYS:
        assert key in entry, f"missing key {key} in {config_id}"
    assert isinstance(entry["retrieval_augmented"], bool)
    assert 0.0 < entry["temperature"] <= 2.0
    assert 0.0 < entry["top_p"] <= 1.0
    assert entry["model_size_params"] > 0
    assert entry["context_window_tokens"] > 0


def test_structural_variation_exists():
    """Structural parameters must vary across configs (avoids tautology)."""
    configs = load_arch_configs(CONFIG_PATH)
    sizes = {c["model_size_params"] for c in configs}
    rags = {c["retrieval_augmented"] for c in configs}
    assert len(sizes) >= 2, "model size must vary"
    assert rags == {True, False}, "retrieval toggle must vary"


def test_execution_and_resource_constraints():
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    assert raw["execution"]["timeout_seconds_per_attempt"] == 60
    assert raw["execution"]["memory_error_retries"] == 1
    assert raw["execution"]["determinism_check_runs"] == 3
    assert raw["resources"]["device"] == "cpu"
    assert raw["resources"]["max_ram_gb"] <= 7