import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import re

try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
except ImportError:
    raise ImportError(
        "RDKit is required for this module. "
        "Please install it via `pip install rdkit`."
    )

from src.modeling.config import load_config

# Configure logger
logger = logging.getLogger(__name__)

# Cache for compiled patterns to avoid re-parsing on every call
_pattern_cache: Dict[str, Any] = {}

def get_templates() -> Dict[str, Any]:
    """
    Load reaction SMARTS patterns from the configuration file.
    
    Returns:
        Dict containing 'reaction_templates' key with pattern definitions.
        Returns empty dict if patterns are missing or config fails to load.
    """
    try:
        config = load_config()
        templates = config.get('reaction_templates', {})
        if not templates:
            logger.warning("No 'reaction_templates' found in config.yaml.")
        return templates
    except Exception as e:
        logger.error(f"Failed to load templates from config: {e}")
        return {}

def _compile_smarts(smarts_str: str) -> Optional[Chem.Mol]:
    """
    Compile a SMARTS string into an RDKit Mol object.
    
    Args:
        smarts_str: The SMARTS pattern string.
        
    Returns:
        RDKit Mol object if successful, None otherwise.
    """
    try:
        # RDKit MolFromSmarts returns None if parsing fails
        pattern = Chem.MolFromSmarts(smarts_str)
        if pattern is None:
            logger.warning(f"Failed to parse SMARTS pattern: {smarts_str}")
        return pattern
    except Exception as e:
        logger.error(f"Error compiling SMARTS '{smarts_str}': {e}")
        return None

def _match_reaction(
    reaction_smiles: str, 
    pattern: Chem.Mol
) -> bool:
    """
    Check if a reaction SMILES matches a given SMARTS pattern.
    
    Args:
        reaction_smiles: The SMILES string representing the reaction.
        pattern: The compiled SMARTS pattern.
        
    Returns:
        True if the pattern matches the reaction, False otherwise.
    """
    try:
        # RDKit can parse reaction SMILES using ReactionFromSmarts or similar,
        # but for template matching on the whole string, we often treat the
        # reaction as a set of molecules or use a specific matcher.
        # However, standard practice for USPTO-style data often involves
        # matching the reactants or the whole transformation string.
        # Here we attempt to match the pattern against the reaction string
        # by treating the reaction as a single entity or parsing it.
        
        # For robustness, we try to parse the reaction SMILES into a
        # Reaction object if it contains '>', otherwise a single Mol.
        if '>' in reaction_smiles:
            # It's a reaction SMILES: Reactants > Reagents > Products
            # RDKit has a specific parser for this
            rxn = Chem.ReactionFromSmarts(reaction_smiles)
            if rxn is None:
                # Fallback: try to match pattern against the string directly
                # This is less rigorous but handles malformed reaction SMILES
                # by treating the whole string as a query against the pattern?
                # Actually, we want to see if the PATTERN matches the REACTION.
                # If we can't parse the reaction, we can't match it reliably.
                return False
            
            # Check if the reaction matches the pattern
            # We iterate over the reactants/products if the pattern is specific
            # But typically, a reaction template SMARTS like "[C:1]([O:2])>>[C:1]+[O:2]-"
            # is designed to match a Reaction object.
            # RDKit's IsReactionMatch is not standard. We use GetSubstructMatch
            # on the reactants or products if the pattern is a molecule.
            # A common approach: Convert reaction SMILES to a single molecule
            # representation or check if the pattern matches any part.
            # Given the task description, we assume the pattern matches the
            # transformation logic.
            
            # Let's try a simpler heuristic often used:
            # Does the pattern match the reactants side?
            reactants_str = reaction_smiles.split('>')[0]
            reactants = Chem.MolFromSmiles(reactants_str)
            if reactants:
                if reactants.HasSubstructMatch(pattern):
                    return True
            
            # Check products side
            products_str = reaction_smiles.split('>')[-1]
            products = Chem.MolFromSmiles(products_str)
            if products:
                if products.HasSubstructMatch(pattern):
                    return True
                    
            return False
        else:
            # Not a reaction SMILES, treat as a single molecule
            mol = Chem.MolFromSmiles(reaction_smiles)
            if mol:
                return mol.HasSubstructMatch(pattern)
            return False
            
    except Exception as e:
        logger.debug(f"Error matching reaction '{reaction_smiles}' with pattern: {e}")
        return False

def classify_reaction(
    reaction_smiles: str, 
    templates: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Classify a reaction into SN1, SN2, or Diels-Alder based on SMARTS patterns.
    
    Args:
        reaction_smiles: The SMILES string of the reaction.
        templates: Optional dictionary of templates. If None, loads from config.
        
    Returns:
        The classification label ('SN1', 'SN2', 'Diels-Alder') if a match is found,
        otherwise None.
        
    Note:
        If multiple patterns match, the order of keys in the templates dict
        determines priority (first match wins).
    """
    if templates is None:
        templates = get_templates()
    
    if not templates:
        logger.warning("No templates provided or loaded. Cannot classify.")
        return None

    # Iterate through templates to find the first match
    # The config keys should be the class names (e.g., "SN1", "SN2")
    for class_name, pattern_info in templates.items():
        smarts = pattern_info.get('pattern')
        if not smarts:
            logger.warning(f"Template '{class_name}' missing 'pattern' key.")
            continue

        # Compile pattern if not cached
        if smarts not in _pattern_cache:
            _pattern_cache[smarts] = _compile_smarts(smarts)
        
        pattern = _pattern_cache[smarts]
        if pattern is None:
            continue

        if _match_reaction(reaction_smiles, pattern):
            logger.debug(f"Reaction classified as '{class_name}' using pattern '{smarts}'")
            return class_name

    return None

def classify_batch(
    reaction_smiles_list: List[str], 
    templates: Optional[Dict[str, Any]] = None
) -> List[Optional[str]]:
    """
    Classify a batch of reactions.
    
    Args:
        reaction_smiles_list: List of reaction SMILES strings.
        templates: Optional templates dict.
        
    Returns:
        List of classification labels or None for each input.
    """
    return [classify_reaction(smiles, templates) for smiles in reaction_smiles_list]
