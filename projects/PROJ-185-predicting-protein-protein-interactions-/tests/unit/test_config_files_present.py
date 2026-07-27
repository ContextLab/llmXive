"""Unit tests for verifying required configuration files exist.

These tests correspond to task T009c. They simply assert that the YAML
configuration files created under ``src/config/`` are present in the
repository. No content validation is performed here; other tasks will
validate schema and semantics.
"""

from pathlib import Path

import pytest

# Base directory of the repository (project root)
REPO_ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture(scope="module")
def config_dir():
    """Path object pointing to the src/config directory."""
    return REPO_ROOT / "src" / "config"

def test_species_yaml_exists(config_dir):
    """Ensure that ``species.yaml`` exists."""
    species_path = config_dir / "species.yaml"
    assert species_path.is_file(), f"Missing required config file: {species_path}"

def test_parameters_yaml_exists(config_dir):
    """Ensure that ``parameters.yaml`` exists."""
    parameters_path = config_dir / "parameters.yaml"
    assert parameters_path.is_file(), f"Missing required config file: {parameters_path}"