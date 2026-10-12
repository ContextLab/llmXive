"""Unit tests for src/config/arch_configs.yaml (task T006)."""
from __future__ import annotations

import pathlib

import pytest
import yaml

from src.config.loader import get_arch_config, load_arch_configs

CONFIG_PATH = pathlib.Path(__file__).resolve().parents[2] / "src" / "config" / "arch_configs.yaml"

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


def test_config_file_exists():
    assert CONFIG_PATH.is_file(), f"missing {CONFIG_PATH}"


def test_load_arch_configs_returns_all_entries():
    configs = load_arch_configs(CONFIG_PATH)
    assert {c["config_id"] for c in configs} == EXPECTED_IDS


def test_every_entry_has_required_structural_keys():
    for cfg in load_arch_configs(CONFIG_PATH):
        missing = REQUIRED_KEYS - set(cfg)
        assert not missing, f"{cfg.get('config_id')} missing {missing}"


def test_structural_parameters_vary_across_configs():
    """Structural params are the independent variables (US-3); they must vary."""
    configs = load_arch_configs(CONFIG_PATH)
    sizes = {c["model_size_params"] for c in configs}
    rag = {c["retrieval_augmented"] for c in configs}
    temps = {c["temperature"] for c in configs}
    assert len(sizes) > 1, "model_size_params must vary"
    assert len(rag) > 1, "retrieval_augmented must vary"
    assert len(temps) > 1, "temperature must vary"


def test_cpu_tractable_models_only():
    for cfg in load_arch_configs(CONFIG_PATH):
        assert cfg["model_size_params"] <= 500_000_000, (
            f"{cfg['config_id']} exceeds CPU-tractable size"
        )


def test_get_arch_config_roundtrip():
    cfg = get_arch_config("small_rag_high_temp", CONFIG_PATH)
    assert cfg["retrieval_augmented"] is True
    assert cfg["retrieval_top_k"] == 5
    assert cfg["temperature"] == 0.7


def test_get_arch_config_unknown_id_raises():
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist", CONFIG_PATH)


def test_execution_constraints_match_spec():
    raw = yaml.safe_load(CONFIG_PATH.read_text())
    exec_cfg = raw["execution"]
    assert exec_cfg["timeout_seconds_per_attempt"] == 60
    assert exec_cfg["memory_error_retries"] == 1
    assert exec_cfg["determinism_check_runs"] == 3
    assert exec_cfg["max_wall_clock_seconds_per_hypothesis"] == 120
    res = raw["resources"]
    assert res["device"] == "cpu"
    assert res["max_ram_gb"] <= 7