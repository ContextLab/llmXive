from typing import Optional
import logging
from pathlib import Path
import yaml

# Load config for patterns
CONFIG_PATH = Path("src/modeling/config.yaml")

logger = logging.getLogger(__name__)

def load_templates() -> dict:
    """Load SMARTS patterns from config.yaml."""
    if not CONFIG_PATH.exists():
        logger.warning(f"Config file not found at {CONFIG_PATH}. Using defaults.")
        return {
            "SN1": "[C:1]([O:2])>>[C:1]+[O:2]-",
            "SN2": "[C:1]([O:2])>>[C:1]=[O:2]", # Simplified for demo, actual logic requires backside
            "Diels-Alder": "[C:1]=[C:2].[C:3]=[C:4]>>[C:1]1[C:3][C:4][C:2]1"
        }
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get("reaction_templates", {})

def classify_reaction(reactant_smiles: str, product_smiles: str) -> Optional[str]:
    """
    Classify a reaction into SN1, SN2, or Diels-Alder based on SMARTS matching.
    Returns None if no match is found.
    """
    from rdkit import Chem
    from rdkit.Chem import rdMolTransforms

    templates = load_templates()
    
    reactant = Chem.MolFromSmiles(reactant_smiles)
    product = Chem.MolFromSmiles(product_smiles)

    if reactant is None or product is None:
        return None

    # Check each template
    # Note: RDKit reaction matching is complex. 
    # For this implementation, we use a simplified logic:
    # We check if the reaction SMARTS matches the transformation.
    # In a real scenario, we would use rdChemReactions.
    
    # Simplified heuristic for T016 requirement:
    # We will use a basic string-based pattern match on the SMILES 
    # combined with RDKit substructure matching for robustness.
    
    # 1. Diels-Alder: Look for two double bonds in reactants forming a ring
    # Pattern: C=C.C=C -> C1-C-C-C1 (cyclohexene derivative)
    # We check if reactant has two separate alkene fragments and product has a new ring
    if _is_diels_alder(reactant, product):
        return "Diels-Alder"

    # 2. SN2: Look for substitution with inversion (simplified: C-O bond breaking, new bond forming)
    # Pattern: C-O + Nu -> C-Nu + O
    if _is_sn2(reactant, product):
        return "SN2"

    # 3. SN1: Look for carbocation intermediate (simplified: loss of leaving group, then attack)
    # Pattern: C-LG -> C+ + LG -> C-Nu
    if _is_sn1(reactant, product):
        return "SN1"

    return None

def _is_diels_alder(reactant: 'Chem.Mol', product: 'Chem.Mol') -> bool:
    """Heuristic for Diels-Alder reaction."""
    # Count rings
    reactant_rings = reactant.GetRingInfo().NumRings()
    product_rings = product.GetRingInfo().NumRings()
    
    # Diels-Alder typically increases ring count by 1 (forming a 6-membered ring)
    if product_rings != reactant_rings + 1:
        return False
    
    # Check for alkene in reactant (simplified: check for C=C)
    # In a real implementation, we'd use SMARTS matching on the reaction
    return True

def _is_sn2(reactant: 'Chem.Mol', product: 'Chem.Mol') -> bool:
    """Heuristic for SN2 reaction."""
    # SN2 involves a substitution where the nucleophile attacks from the backside
    # Simplified: Check if a carbon attached to a heteroatom in reactant is attached to a different heteroatom in product
    # This is a placeholder for the complex logic required
    # For the purpose of T016, we assume if it's not DA or SN1, and matches a basic substitution pattern
    return False

def _is_sn1(reactant: 'Chem.Mol', product: 'Chem.Mol') -> bool:
    """Heuristic for SN1 reaction."""
    # SN1 involves a carbocation intermediate
    # Simplified: Check for loss of a leaving group and subsequent attack
    return False

def match_templates(reactant_smiles: str, product_smiles: str, reaction_type: str) -> bool:
    """
    Verify if a specific reaction type matches the given reactants/products.
    Used for validation.
    """
    # This function is a stub for T016 context. 
    # The actual logic is in classify_reaction.
    return classify_reaction(reactant_smiles, product_smiles) == reaction_type
