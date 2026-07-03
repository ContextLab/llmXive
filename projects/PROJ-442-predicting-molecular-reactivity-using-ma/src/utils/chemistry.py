import logging
from typing import Optional
from pathlib import Path
import yaml

try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
except ImportError:
    Chem = None
    rdMolDescriptors = None

CONFIG_PATH = Path("src/modeling/config.yaml")

def load_reaction_templates() -> dict:
    """Load SMARTS patterns from config.yaml."""
    if not CONFIG_PATH.exists():
        logging.getLogger(__name__).warning(f"Config file not found at {CONFIG_PATH}. Using defaults.")
        return {
            "SN1": "[C:1]([O:2])>>[C:1]+[O:2]-",
            "SN2": "[C:1]([O:2])>>[C:1]=[O:2]",
            "Diels-Alder": "[C:1]=[C:2].[C:3]=[C:4]>>[C:1]1[C:3][C:4][C:2]1"
        }
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('reaction_templates', {})
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load config: {e}")
        return {
            "SN1": "[C:1]([O:2])>>[C:1]+[O:2]-",
            "SN2": "[C:1]([O:2])>>[C:1]=[O:2]",
            "Diels-Alder": "[C:1]=[C:2].[C:3]=[C:4]>>[C:1]1[C:3][C:4][C:2]1"
        }

def classify_reaction(smiles: str) -> Optional[str]:
    """
    Classify a reaction based on SMARTS patterns.
    Returns 'SN1', 'SN2', 'Diels-Alder', or None if no match.
    """
    if Chem is None:
        raise ImportError("RDKit is required for chemistry operations")

    templates = load_reaction_templates()
    mol = Chem.MolFromSmiles(smiles)
    
    if mol is None:
        return None

    for reaction_type, pattern in templates.items():
        try:
            smarts = Chem.MolFromSmarts(pattern)
            if smarts and mol.HasSubstructMatch(smarts):
                return reaction_type
        except Exception:
            continue

    return None
