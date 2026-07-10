"""
Target Calculation Module.

Calculates the decomposition energy (E_decomp) using stoichiometry and
reaction data from the YAML configuration.
"""
import yaml
import math
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import pandas as pd

# Add project root to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import get_reactions_schema_template
from config import get_project_root, get_data_dir


def load_reactions_yaml(yaml_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the reactions YAML file containing reaction data.
    """
    if yaml_path is None:
        # Default path based on project structure
        root = get_project_root()
        yaml_path = root / "code" / "utils" / "reactions.yaml"
        
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Reactions YAML not found at {path}")
        
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
        
    return data


def get_reaction_entry(reactions: Dict[str, Any], molecule_id: str, potential_v: float) -> Optional[Dict[str, Any]]:
    """
    Retrieve the specific reaction entry for a molecule and potential.
    
    Args:
        reactions: The full reactions dictionary.
        molecule_id: The ID of the molecule (e.g., 'EC').
        potential_v: The potential in Volts.
        
    Returns:
        The reaction entry dict or None.
    """
    # The YAML structure is expected to be a list of entries or a dict of lists
    entries = reactions.get('entries', []) if isinstance(reactions, dict) else reactions
    
    for entry in entries:
        if str(entry.get('molecule_id')) == str(molecule_id):
            # Check potential
            entry_pot = float(entry.get('potential_v', -1))
            if math.isclose(entry_pot, potential_v, rel_tol=1e-3):
                return entry
                
    return None


def calculate_decomposition_energy(reactant_energy: float, product_energy: float, n_electrons: int, potential_v: float) -> float:
    """
    Calculate E_decomp = E_products - E_reactants - n * F * phi
    
    Note: F (Faraday constant) is ~96485 C/mol. 
    Energy in eV: 1 eV = 96485 J/mol (approx, since 1 eV = 1.602e-19 J and 1 mol = 6.022e23)
    Actually: E(eV) = E(J) / (1.602e-19)
    n * F * V (J/mol) -> n * V (eV) because F/e = 1 (approx in eV units per volt)
    Wait: 1 eV is the energy of 1 electron moved through 1V.
    So n electrons * V volts = n * V eV.
    The term n*F*phi in Joules converts to n*phi in eV directly if energies are in eV.
    
    Formula: E_decomp (eV) = E_products (eV) - E_reactants (eV) - n * phi (V)
    """
    # F in eV/V is effectively 1 for this unit system (n electrons * V volts = n*V eV)
    return product_energy - reactant_energy - (n_electrons * potential_v)


def calculate_decomposition_energy_from_yaml(row: Dict[str, Any], reactions: Dict[str, Any]) -> Optional[float]:
    """
    Calculate E_decomp for a single row using the YAML data.
    """
    mol_id = row.get('molecule_id')
    pot = row.get('potential_v')
    
    if mol_id is None or pot is None:
        return None
        
    entry = get_reaction_entry(reactions, mol_id, pot)
    
    if entry is None:
        # Check if we have energies in the row itself (fallback from ingestion)
        # If the ingestion didn't provide the reaction entry, we might have raw energies
        if 'energy_reactants' in row and 'energy_products' in row and 'n_electrons' in row:
            return calculate_decomposition_energy(
                row['energy_reactants'],
                row['energy_products'],
                row['n_electrons'],
                pot
            )
        return None
        
    # Extract values from entry
    e_react = entry.get('energy_reactants')
    e_prod = entry.get('energy_products')
    n_el = entry.get('n_electrons')
    
    if e_react is None or e_prod is None or n_el is None:
        return None
        
    return calculate_decomposition_energy(e_react, e_prod, n_el, pot)


def run_target_calculation_pipeline(df: pd.DataFrame, reactions: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Apply target calculation to the entire DataFrame.
    """
    if reactions is None:
        reactions = load_reactions_yaml()
        
    results = []
    for idx, row in df.iterrows():
        e_decomp = calculate_decomposition_energy_from_yaml(row.to_dict(), reactions)
        new_row = row.to_dict()
        new_row['e_decomp_ev'] = e_decomp
        results.append(new_row)
        
    return pd.DataFrame(results)


if __name__ == "__main__":
    # Example usage
    print("Target Calculation Module Loaded")
