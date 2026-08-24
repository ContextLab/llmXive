import pytest
import yaml
from pathlib import Path
import sys

# Add code directory to path for imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.env_config import load_environment_config

CONFIG_DIR = Path(__file__).parent.parent / "config"

def test_genomes_yaml_exists():
    """Verify that the genomes configuration file exists."""
    path = CONFIG_DIR / "genomes.yaml"
    assert path.exists(), f"genomes.yaml not found at {path}"

def test_genomes_yaml_valid_structure():
    """Verify that genomes.yaml loads and contains expected keys."""
    path = CONFIG_DIR / "genomes.yaml"
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "assemblies" in data, "Missing 'assemblies' key in genomes.yaml"
    assert "human" in data["assemblies"], "Missing 'human' assembly"
    assert "chimp" in data["assemblies"], "Missing 'chimp' assembly"
    assert "macaque" in data["assemblies"], "Missing 'macaque' assembly"
    assert "marmoset" in data["assemblies"], "Missing 'marmoset' assembly"

def test_species_replicates_yaml_exists():
    """Verify that the species replicates configuration file exists."""
    path = CONFIG_DIR / "species_replicates.yaml"
    assert path.exists(), f"species_replicates.yaml not found at {path}"

def test_species_replicates_yaml_constraints():
    """Verify that replicate constraints are defined correctly."""
    path = CONFIG_DIR / "species_replicates.yaml"
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "replicate_constraints" in data, "Missing 'replicate_constraints'"
    constraints = data["replicate_constraints"]
    assert constraints["min_replicates"] == 3, "Min replicates must be 3"
    assert constraints["max_replicates"] == 5, "Max replicates must be 5"
    assert constraints["abort_code_min"] == 101, "Abort code min must be 101"
    assert constraints["abort_code_max"] == 102, "Abort code max must be 102"

def test_load_environment_config_integration():
    """Test that the config loader can read the new files."""
    # This tests the integration with utils.env_config
    try:
        config = load_environment_config(CONFIG_DIR / "genomes.yaml")
        assert config is not None
    except Exception as e:
        pytest.fail(f"Failed to load environment config: {e}")