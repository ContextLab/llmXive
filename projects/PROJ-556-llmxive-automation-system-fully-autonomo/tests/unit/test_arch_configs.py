"""Unit tests for src/config/arch_configs.yaml (task T006)."""
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


def test_file_exists_and_parses():
    assert CONFIG_PATH.is_file()
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict)
    assert isinstance(data.get("configs"), list)
    assert len(data["configs"]) >= 5


def test_all_configs_have_required_structural_keys():
    for cfg in load_arch_configs(CONFIG_PATH):
        missing = REQUIRED_KEYS - set(cfg)
        assert not missing, f"{cfg.get('config_id')} missing keys: {missing}"


def test_config_ids_unique_and_expected():
    cfgs = load_arch_configs(CONFIG_PATH)
    ids = [c["config_id"] for c in cfgs]
    assert len(ids) == len(set(ids)), "config_id values must be unique"
    assert EXPECTED_CONFIG_IDS.issubset(set(ids))


def test_structural_parameters_vary():
    """Structural params must actually vary so correlation analysis is not tautological."""
    cfgs = load_arch_configs(CONFIG_PATH)
    sizes = {c["model_size_params"] for c in cfgs}
    rag = {c["retrieval_augmented"] for c in cfgs}
    ctx = {c["context_window_tokens"] for c in cfgs}
    assert len(sizes) >= 2, "model_size_params must vary across configs"
    assert rag == {True, False}, "retrieval_augmented must have both on/off"
    assert len(ctx) >= 1


def test_cpu_only_constraint():
    for cfg in load_arch_configs(CONFIG_PATH):
        assert cfg["model_size_params"] <= 500_000_000, (
            f"{cfg['config_id']} exceeds CPU-tractable model size"
        )


def test_get_arch_config():
    cfg = get_arch_config("small_rag_high_temp", CONFIG_PATH)
    assert cfg["retrieval_augmented"] is True
    assert cfg["retrieval_top_k"] == 5
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist", CONFIG_PATH)


def test_execution_and_resource_sections():
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    exec_cfg = data["execution"]
    assert exec_cfg["timeout_seconds_per_attempt"] == 60
    assert exec_cfg["memory_error_retries"] == 1
    assert exec_cfg["determinism_check_runs"] == 3
    res = data["resources"]
    assert res["device"] == "cpu"
    assert res["max_ram_gb"] <= 7
    assert res["max_disk_gb"] <= 14