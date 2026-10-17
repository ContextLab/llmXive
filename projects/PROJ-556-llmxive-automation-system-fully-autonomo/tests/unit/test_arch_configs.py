"""Unit tests for src/config/arch_configs.yaml and its loader.

These tests verify that the ArchConfig definitions required by task T006
exist, are structurally valid, and load through the project's config
loader (src.config.loader).
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

from src.config.loader import get_arch_config, load_arch_configs

CONFIG_PATH = pathlib.Path(__file__).resolve().parents[2] / "src" / "config" / "arch_configs.yaml"

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


def test_config_file_exists() -> None:
    assert CONFIG_PATH.is_file(), f"missing config file: {CONFIG_PATH}"


def test_yaml_parses_and_has_configs_section() -> None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict)
    assert "configs" in data
    assert len(data["configs"]) >= 5


def test_expected_config_ids_present() -> None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    ids = {c["config_id"] for c in data["configs"]}
    assert EXPECTED_CONFIG_IDS.issubset(ids)


def test_every_config_has_required_keys() -> None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    for cfg in data["configs"]:
        missing = REQUIRED_KEYS - set(cfg.keys())
        assert not missing, f"{cfg.get('config_id')} missing keys: {missing}"


def test_structural_parameters_vary() -> None:
    """Structural params must actually vary so correlation analysis (US-3) is non-degenerate."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    sizes = {c["model_size_params"] for c in data["configs"]}
    rags = {c["retrieval_augmented"] for c in data["configs"]}
    assert len(sizes) >= 2, "model_size_params must vary across configs"
    assert rags == {True, False}, "retrieval_augmented must take both values"


def test_loader_loads_all_configs() -> None:
    configs = load_arch_configs()
    assert len(configs) >= 5
    assert all(REQUIRED_KEYS.issubset(set(c.keys())) for c in configs)


def test_loader_get_single_config() -> None:
    cfg = get_arch_config("small_rag_high_temp")
    assert cfg["config_id"] == "small_rag_high_temp"
    assert cfg["retrieval_augmented"] is True


def test_loader_unknown_id_raises() -> None:
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist")