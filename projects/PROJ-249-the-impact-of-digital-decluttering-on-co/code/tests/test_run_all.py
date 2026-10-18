"""Tests for the T001 pipeline entry point and config validation."""

import copy
from pathlib import Path

import pytest
import yaml

from code.pipeline.run_all import (
    REQUIRED_KEYS,
    REQUIRED_METRICS,
    load_and_validate_config,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
    # tests live at <root>/code/tests/test_run_all.py -> parents[2] is root
CONFIG_PATH = PROJECT_ROOT / "code" / "config" / "study_config.yaml"


def _load_raw():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_config_file_exists():
    assert CONFIG_PATH.exists(), "study_config.yaml is missing"


def test_config_has_exactly_required_keys():
    cfg = _load_raw()
    assert set(cfg.keys()) == set(REQUIRED_KEYS.keys())
    assert set(cfg["effect_sizes"].keys()) == set(REQUIRED_METRICS)
    assert [float(g) for g in cfg["practice_effect_grid"]] == [0.0, 0.2, 0.4]
    assert cfg["bootstrap_resamples"] == 10000
    assert cfg["pilot_n"] == 5


def test_valid_config_passes():
    cfg = load_and_validate_config(str(CONFIG_PATH))
    assert cfg["seed"] == 20240521
    assert isinstance(cfg["dropout_rate"], float)


def test_missing_key_raises():
    cfg = _load_raw()
    del cfg["seed"]
    tmp = PROJECT_ROOT / "code" / "tests" / "_tmp_bad_config.yaml"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)
    try:
        with pytest.raises(ValueError, match="seed"):
            load_and_validate_config(str(tmp))
    finally:
        tmp.unlink()


def test_wrong_type_raises():
    cfg = _load_raw()
    cfg["n_participants"] = "forty"
    tmp = PROJECT_ROOT / "code" / "tests" / "_tmp_bad_config.yaml"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)
    try:
        with pytest.raises(ValueError, match="n_participants"):
            load_and_validate_config(str(tmp))
    finally:
        tmp.unlink()


def test_bad_grid_raises():
    cfg = _load_raw()
    cfg["practice_effect_grid"] = [0.0, 0.1]
    tmp = PROJECT_ROOT / "code" / "tests" / "_tmp_bad_config.yaml"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)
    try:
        with pytest.raises(ValueError, match="practice_effect_grid"):
            load_and_validate_config(str(tmp))
    finally:
        tmp.unlink()


def test_bad_date_raises():
    cfg = _load_raw()
    cfg["start_date"] = "21-05-2024"
    tmp = PROJECT_ROOT / "code" / "tests" / "_tmp_bad_config.yaml"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)
    try:
        with pytest.raises(ValueError, match="start_date"):
            load_and_validate_config(str(tmp))
    finally:
        tmp.unlink()
