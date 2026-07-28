"""Unit test to verify that required configuration files exist."""

import pathlib


def _project_root() -> pathlib.Path:
    """Return the absolute path to the project root directory."""
    # This file lives in <project_root>/tests/unit/
    return pathlib.Path(__file__).resolve().parents[2]


def test_species_yaml_exists():
    """Check that src/config/species.yaml is present."""
    cfg_path = _project_root() / "src" / "config" / "species.yaml"
    assert cfg_path.is_file(), f"Missing configuration file: {cfg_path}"


def test_parameters_yaml_exists():
    """Check that src/config/parameters.yaml is present."""
    cfg_path = _project_root() / "src" / "config" / "parameters.yaml"
    assert cfg_path.is_file(), f"Missing configuration file: {cfg_path}"