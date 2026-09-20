"""Chemistry utilities for reaction classification using RDKit and SMARTS patterns."""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdChemReactions

from src.modeling.config import load_config

logger = logging.getLogger(__name__)


def get_templates(config_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load SMARTS patterns for reaction templates from config.yaml.

    Args:
        config_path: Optional path to config.yaml. If None, uses default location.

    Returns:
        Dictionary mapping reaction type names to their SMARTS patterns.

    Raises:
        KeyError: If the 'reaction_templates' section is missing or malformed.
        FileNotFoundError: If config file does not exist.
    """
    config = load_config(config_path)
    
    if 'reaction_templates' not in config:
        raise KeyError(
            "Config missing 'reaction_templates' section. "
            "Please define SMARTS patterns for SN1, SN2, and Diels-Alder in config.yaml."
        )
    
    templates = config['reaction_templates']
    
    # Validate required keys
    required_keys = ['SN1', 'SN2', 'Diels-Alder']
    for key in required_keys:
        if key not in templates:
            raise KeyError(f"Missing required reaction template: {key}")
        
    return templates


def _match_reaction(smiles: str, pattern_smarts: str) -> bool:
    """
    Check if a reaction SMILES matches a given SMARTS pattern.

    Args:
        smiles: Reaction SMILES string.
        pattern_smarts: SMARTS pattern to match against.

    Returns:
        True if the pattern matches the reaction, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    
    if not pattern_smarts or not isinstance(pattern_smarts, str):
        return False

    try:
        reaction = Chem.MolFromSmiles(smiles)
        if reaction is None:
            return False
        
        pattern = Chem.MolFromSmarts(pattern_smarts)
        if pattern is None:
            logger.warning(f"Invalid SMARTS pattern: {pattern_smarts}")
            return False
        
        # Match the pattern against the reaction molecule
        matches = reaction.GetSubstructMatches(pattern)
        return len(matches) > 0
        
    except Exception as e:
        logger.debug(f"Error matching pattern {pattern_smarts} to {smiles}: {e}")
        return False


def classify_reaction(smiles: str, templates: Optional[Dict[str, str]] = None, 
                      config_path: Optional[Path] = None) -> Optional[str]:
    """
    Classify a reaction based on its SMILES string using SMARTS patterns.

    Args:
        smiles: Reaction SMILES string.
        templates: Optional dictionary of SMARTS patterns. If None, loads from config.
        config_path: Optional path to config.yaml.

    Returns:
        The reaction type (e.g., 'SN1', 'SN2', 'Diels-Alder') if a match is found,
        None otherwise. If multiple patterns match, returns the first match in order.
    """
    if templates is None:
        try:
            templates = get_templates(config_path)
        except (KeyError, FileNotFoundError) as e:
            logger.error(f"Failed to load templates: {e}")
            return None

    # Define order of precedence for matching
    reaction_order = ['SN1', 'SN2', 'Diels-Alder']
    
    for reaction_type in reaction_order:
        if reaction_type in templates:
            pattern = templates[reaction_type]
            if _match_reaction(smiles, pattern):
                logger.debug(f"Reaction classified as {reaction_type}")
                return reaction_type
    
    return None


def classify_batch(smiles_list: List[str], config_path: Optional[Path] = None) -> List[Optional[str]]:
    """
    Classify a batch of reactions.

    Args:
        smiles_list: List of reaction SMILES strings.
        config_path: Optional path to config.yaml.

    Returns:
        List of classification results (reaction type or None for each input).
    """
    if not smiles_list:
        return []

    try:
        templates = get_templates(config_path)
    except (KeyError, FileNotFoundError) as e:
        logger.error(f"Failed to load templates for batch classification: {e}")
        return [None] * len(smiles_list)

    results = []
    for smiles in smiles_list:
        classification = classify_reaction(smiles, templates, config_path)
        results.append(classification)
    
    return results