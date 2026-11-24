"""Tests for T004: configuration loader, logging setup, and data models."""

import importlib.util
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"


def _import(name: str):
    """Import a module from code/ by file path (code/ is not a package)."""
    spec = importlib.util.spec_from_file_location(name, CODE_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def config_mod():
    return _import("t004_config")


@pytest.fixture(scope="module")
def models_mod():
    return _import("t004_models")


def test_setup_logging_creates_log_file_in_artifacts_logs(config_mod):
    logger = config_mod.setup_logging()
    logger.info("test log entry")
    log_path = PROJECT_ROOT / config_mod.get_config()["LOG_PATH"]
    assert log_path.exists()
    assert log_path.parent == PROJECT_ROOT / "artifacts" / "logs"
    for handler in logger.handlers:
        handler.flush()

def test_get_config_provides_standard_keys(config_mod):
    cfg = config_mod.get_config()
    for key in [
        "DATA_PATH",
        "PROCESSED_PATH",
        "ARTIFACTS_PATH",
        "LOGS_PATH",
        "LOG_PATH",
        "LOG_LEVEL",
        "SEED",
    ]:
        assert key in cfg, f"missing key: {key}"
    assert isinstance(cfg["SEED"], int)

def test_models_expose_required_dataclasses(models_mod):
    assert hasattr(models_mod, "RootPhenotypeRecord")
    assert hasattr(models_mod, "SoilNutrientRecord")

def test_record_behaviour(models_mod):
    rec = models_mod.RootPhenotypeRecord(species="Arabidopsis thaliana")
    assert not rec.is_valid_for_analysis()
    rec.root_length = 10.0
    assert rec.is_valid_for_analysis()

    soil = models_mod.SoilNutrientRecord(phosphorus=2.0)
    assert not soil.is_complete_for_analysis()
    soil.nitrogen = 1.0
    assert soil.is_complete_for_analysis()

    merged = models_mod.MergedPhenotypeNutrientRecord(root=rec, soil=soil)
    assert merged.has_nutrient_data
    d = merged.to_dict()
    assert d["species"] == "Arabidopsis thaliana"
    assert d["phosphorus"] == 2.0

def test_config_template_exists():
    template = PROJECT_ROOT / "config.yaml.template"
    assert template.exists(), f"missing {template}"
    assert template.stat().st_size > 0