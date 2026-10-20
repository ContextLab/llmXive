"""Tests for src/config/arch_configs.yaml and its loader (T006)."""
from __future__ import annotations

import pathlib

import pytest
import yaml

from src.config.loader import get_arch_config, load_arch_configs

CONFIG_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "src" / "config" / "arch_configs.yaml"
)

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

def test_yaml_parses_and_has_configs_section():
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    assert isinstance(doc, dict)
    assert isinstance(doc.get("configs"), list)
    assert len(doc["configs"]) >= 4  # enough for multiple-comparison correction (FR-007)

def test_every_config_has_required_structural_keys():
    for cfg in load_arch_configs(CONFIG_PATH):
        missing = REQUIRED_KEYS - set(cfg)
        assert not missing, f"{cfg.get('config_id')} missing keys: {missing}"

def test_structural_parameters_vary_across_configs():
    """Structural params must vary so the correlation analysis is not tautological."""
    cfgs = load_arch_configs(CONFIG_PATH)
    sizes = {c["model_size_params"] for c in cfgs}
    rag = {c["retrieval_augmented"] for c in cfgs}
    temps = {c["temperature"] for c in cfgs}
    assert len(sizes) >= 2, "model_size_params must vary"
    assert len(rag) >= 2, "retrieval_augmented must vary"
    assert len(temps) >= 2, "temperature must vary"

def test_cpu_only_models():
    for cfg in load_arch_configs(CONFIG_PATH):
        assert cfg["model_size_params"] <= 500_000_000, (
            f"{cfg['config_id']} exceeds CPU-tractable model size"
        )

def test_get_arch_config_roundtrip():
    cfg = get_arch_config("small_no_rag_high_temp", CONFIG_PATH)
    assert cfg["config_id"] == "small_no_rag_high_temp"
    assert cfg["temperature"] == 0.7

def test_get_arch_config_unknown_raises():
    with pytest.raises(KeyError):
        get_arch_config("does_not_exist", CONFIG_PATH)