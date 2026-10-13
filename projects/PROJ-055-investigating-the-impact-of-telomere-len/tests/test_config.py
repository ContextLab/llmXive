import pytest
import yaml
from pathlib import Path

def test_config_yaml_exists_and_is_valid():
    """
    Verify that `code/config.yaml` exists and contains valid YAML.
    """
    config_path = Path("code") / "config.yaml"
    assert config_path.is_file(), "config.yaml does not exist"

    with config_path.open() as f:
        try:
            cfg = yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"config.yaml is not valid YAML: {e}")

    # Basic sanity checks for required top‑level keys
    for key in ("dryad", "anage", "random_seed", "alpha"):
        assert key in cfg, f"Missing required config key: {key}"

    # Ensure the alpha threshold is numeric and equals 0.05 (or close)
    assert isinstance(cfg["alpha"], (float, int)), "alpha must be numeric"
    assert abs(float(cfg["alpha"]) - 0.05) < 1e-8, "alpha should be 0.05"

    # Random seed should be an integer
    assert isinstance(cfg["random_seed"], int), "random_seed must be an integer"

def test_scripts_import_config():
    """
    Ensure that the ingestion and cleaning scripts import the configuration.
    """
    import importlib
    ingest = importlib.import_module("02_ingest_data")
    clean = importlib.import_module("03_clean_merge")
    
    # Both modules should have a `_config` attribute populated from get_config()
    assert hasattr(ingest, "_config"), "02_ingest_data does not expose _config"
    assert hasattr(clean, "_config"), "03_clean_merge does not expose _config"
    
    # Verify that the loaded config matches the file content
    from config import get_config
    file_cfg = get_config()
    assert ingest._config == file_cfg, "Ingestion script config mismatch"
    assert clean._config == file_cfg, "Cleaning script config mismatch"