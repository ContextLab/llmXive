import yaml
import os
from pathlib import Path

def test_config_load_and_key_types():
    """
    Load ``code/config.yaml`` and verify that required top‑level keys exist
    and have the expected Python types.
    """
    config_path = Path(__file__).resolve().parents[2] / "code" / "config.yaml"
    assert config_path.is_file(), f"Config file not found at {config_path}"

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    # Required keys and their expected types
    expected = {
        "random_seed": int,
        "tipping_angle": (float, int),  # yaml may parse as int if .0 omitted
        "slippage_distance": (float, int),
        "simulation": dict,
        "data_generation": dict,
        "paths": dict,
    }

    for key, typ in expected.items():
        assert key in cfg, f"Missing required key '{key}' in config.yaml"
        assert isinstance(cfg[key], typ), f"Key '{key}' should be of type {typ}, got {type(cfg[key])}"

    # Spot‑check nested entries
    assert isinstance(cfg["simulation"]["gravity"], (float, int))
    assert isinstance(cfg["simulation"]["num_episodes"], int)
    assert isinstance(cfg["data_generation"]["object_geometries"], list)
