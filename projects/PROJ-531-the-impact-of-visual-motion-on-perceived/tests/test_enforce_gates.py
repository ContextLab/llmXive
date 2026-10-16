"""
Unit tests for ``code/enforce_gates.py``.

The tests verify that the gate behaves correctly for both a passing and a
failing configuration.
"""

import json
from pathlib import Path
import pytest

# Import the functions from the script under test.
from enforce_gates import enforce_gates, load_config, main, DEFAULT_CONFIG_PATH


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary ``modeling_config.json`` file."""
    cfg_path = tmp_path / "modeling_config.json"
    return cfg_path


def write_cfg(path: Path, abort_flag: bool):
    """Helper to write a minimal modelling config."""
    cfg = {
        "abort_flag": abort_flag,
        "effective_n": 150,
        "detectable_f2": 1.0,
        "power": 0.8,
        "power_pass": True,
        "sc001_pass": True
    }
    path.write_text(json.dumps(cfg, indent=2))


def test_gate_passes(tmp_path):
    """When ``abort_flag`` is False the gate should return True."""
    cfg_path = tmp_path / "modeling_config.json"
    write_cfg(cfg_path, abort_flag=False)

    assert enforce_gates(cfg_path) is True
    # The ``main`` function should return exit code 0.
    assert main() == 0


def test_gate_fails(tmp_path):
    """When ``abort_flag`` is True the gate should return False."""
    cfg_path = tmp_path / "modeling_config.json"
    write_cfg(cfg_path, abort_flag=True)

    assert enforce_gates(cfg_path) is False
    # The ``main`` function should return exit code 1.
    assert main() == 1


def test_load_config_missing_file(tmp_path):
    """Loading a non‑existent config should raise FileNotFoundError."""
    missing_path = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        load_config(missing_path)


def test_load_config_invalid_json(tmp_path):
    """Loading a file with invalid JSON should raise json.JSONDecodeError."""
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("not a json")
    with pytest.raises(json.JSONDecodeError):
        load_config(bad_path)