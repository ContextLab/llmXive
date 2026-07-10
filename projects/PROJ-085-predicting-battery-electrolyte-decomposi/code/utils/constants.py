"""
Constants and Configuration for the Battery Electrolyte Project.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, List
import sys

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_project_root


# Physical Constants
# 1 Dalton (Da) in kg
DALTON_KG = 1.66053906660e-27
# Faraday constant in C/mol (approx)
FARADAY_C_MOL = 96485.33212
# Conversion: 1 eV = 1.602176634e-19 J
EV_TO_JOULE = 1.602176634e-19

# Potentials list (V)
PHI_VALUES = [0, 2, 4]

# Target Molecules
TARGET_MOLECULES = ["EC", "DMC", "LiPF6"]


def get_reactions_schema_template() -> Dict[str, Any]:
    """
    Returns the schema template for the reactions YAML file.
    """
    return {
        "entries": [
            {
                "molecule_id": "string",
                "potential_v": "float",
                "reactants": ["list of strings"],
                "products": ["list of strings"],
                "n_electrons": "int",
                "energy_products": "float (eV)",
                "energy_reactants": "float (eV)"
            }
        ]
    }


def create_empty_reactions_yaml(output_path: Optional[str] = None) -> Path:
    """
    Creates an empty reactions YAML file with the schema structure.
    """
    if output_path is None:
        root = get_project_root()
        output_path = root / "code" / "utils" / "reactions.yaml"
    else:
        output_path = Path(output_path)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = get_reactions_schema_template()
    # Remove the 'entries' content to make it empty but structured, 
    # or keep it as a template. The task T004 says "Create empty schema structure".
    # We will create it with an empty list for entries.
    data["entries"] = []
    
    with open(output_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
        
    return output_path


if __name__ == "__main__":
    # Create the file if running directly
    path = create_empty_reactions_yaml()
    print(f"Created reactions schema at: {path}")
