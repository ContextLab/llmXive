import pytest
import math
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.target_calc import load_reactions_yaml, get_reaction_entry, calculate_decomposition_energy

@pytest.fixture
def sample_reactions_yaml(tmp_path):
    """Create a temporary reactions.yaml file for testing."""
    yaml_content = """
    - molecule_id: EC-001
      potential_v: 0
      reactants: ["EC"]
      products: ["C2H4", "CO2"]
      n_electrons: 2
      energy_products: -10.5
      energy_reactants: -12.0
    - molecule_id: EC-001
      potential_v: 2
      reactants: ["EC"]
      products: ["C2H4", "CO2"]
      n_electrons: 2
      energy_products: -10.5
      energy_reactants: -12.0
    - molecule_id: DMC-001
      potential_v: 4
      reactants: ["DMC"]
      products: ["CH3OCH3", "CO2"]
      n_electrons: 1
      energy_products: -8.2
      energy_reactants: -9.5
    """
    file_path = tmp_path / "reactions.yaml"
    with open(file_path, 'w') as f:
        f.write(yaml_content)
    return file_path

def test_load_reactions_yaml(sample_reactions_yaml):
    """Test that reactions YAML is loaded correctly."""
    reactions = load_reactions_yaml(sample_reactions_yaml)
    assert len(reactions) == 3
    assert reactions[0]['molecule_id'] == 'EC-001'
    assert reactions[0]['potential_v'] == 0

def test_get_reaction_entry(sample_reactions_yaml):
    """Test retrieving a specific reaction entry."""
    reactions = load_reactions_yaml(sample_reactions_yaml)
    
    # Test valid entry
    entry = get_reaction_entry(reactions, "EC-001", 0)
    assert entry is not None
    assert entry['molecule_id'] == 'EC-001'
    assert entry['potential_v'] == 0
    
    # Test non-existent entry
    entry_missing = get_reaction_entry(reactions, "EC-001", 4)
    assert entry_missing is None

def test_calculate_decomposition_energy():
    """
    Test the decomposition energy calculation formula:
    E_decomp = E_products - E_reactants - n * F * phi
    
    Where F is Faraday's constant in eV/V (approx 1 eV/V for simplified units in this context)
    or simply n * phi if energies are already in eV and phi in V.
    
    Formula used in code: E_decomp = (E_products - E_reactants) - (n_electrons * potential_v)
    """
    # Case 1: Standard calculation
    # E_products = -10.5, E_reactants = -12.0, n = 2, phi = 0
    # E_decomp = (-10.5 - (-12.0)) - (2 * 0) = 1.5 - 0 = 1.5
    e_decomp = calculate_decomposition_energy(-10.5, -12.0, 2, 0)
    expected = 1.5
    assert math.isclose(e_decomp, expected, abs_tol=0.01)
    
    # Case 2: With potential
    # E_products = -10.5, E_reactants = -12.0, n = 2, phi = 2
    # E_decomp = 1.5 - (2 * 2) = 1.5 - 4 = -2.5
    e_decomp_2 = calculate_decomposition_energy(-10.5, -12.0, 2, 2)
    expected_2 = -2.5
    assert math.isclose(e_decomp_2, expected_2, abs_tol=0.01)
    
    # Case 3: Different values
    # E_products = -8.2, E_reactants = -9.5, n = 1, phi = 4
    # E_decomp = 1.3 - (1 * 4) = -2.7
    e_decomp_3 = calculate_decomposition_energy(-8.2, -9.5, 1, 4)
    expected_3 = -2.7
    assert math.isclose(e_decomp_3, expected_3, abs_tol=0.01)

def test_calculate_decomposition_energy_from_yaml(sample_reactions_yaml):
    """Test the full pipeline from YAML to energy calculation."""
    reactions = load_reactions_yaml(sample_reactions_yaml)
    
    # Test for EC-001 at 0V
    e_decomp = calculate_decomposition_energy_from_yaml(reactions, "EC-001", 0)
    # Expected: 1.5 (from manual calc above)
    assert math.isclose(e_decomp, 1.5, abs_tol=0.01)
    
    # Test for DMC-001 at 4V
    e_decomp_2 = calculate_decomposition_energy_from_yaml(reactions, "DMC-001", 4)
    # Expected: (-8.2 - (-9.5)) - (1 * 4) = 1.3 - 4 = -2.7
    assert math.isclose(e_decomp_2, -2.7, abs_tol=0.01)
    
    # Test missing entry
    e_decomp_missing = calculate_decomposition_energy_from_yaml(reactions, "EC-001", 4)
    assert e_decomp_missing is None
