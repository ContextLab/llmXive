"""
Chemistry utilities for reaction classification using SMARTS patterns.

This module provides functions to classify chemical reactions into
SN1, SN2, and Diels-Alder categories using RDKit-based template matching.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import re
from rdkit import Chem
from rdkit.Chem import rdChemReactions

from src.modeling.config import load_config

logger = logging.getLogger(__name__)

# Cache for compiled templates to avoid reloading on every call
_template_cache: Dict[str, Any] = {}

def get_templates() -> Dict[str, Any]:
    """
    Load and compile SMARTS patterns from configuration.
    
    Returns:
        Dict mapping reaction type names to compiled RDKit reaction templates.
        
    Raises:
        ValueError: If a template pattern is invalid or cannot be compiled.
    """
    if _template_cache:
        return _template_cache
    
    config = load_config()
    templates_config = config.get('reaction_templates', {})
    
    compiled_templates = {}
    
    for reaction_type, template_def in templates_config.items():
        pattern_str = template_def.get('pattern')
        if not pattern_str:
            logger.warning(f"No pattern defined for reaction type: {reaction_type}")
            continue
        
        try:
            # Compile the SMARTS pattern into an RDKit reaction template
            # Format: reactants >> products
            reaction = rdChemReactions.ReactionFromSmarts(pattern_str)
            if reaction is None:
                raise ValueError(f"Failed to compile SMARTS pattern for {reaction_type}: {pattern_str}")
            
            compiled_templates[reaction_type] = {
                'reaction': reaction,
                'pattern': pattern_str,
                'description': template_def.get('description', '')
            }
            logger.debug(f"Compiled template for {reaction_type}: {pattern_str}")
            
        except Exception as e:
            logger.error(f"Error compiling template for {reaction_type}: {e}")
            raise ValueError(f"Invalid SMARTS pattern for {reaction_type}: {pattern_str}") from e
    
    _template_cache.update(compiled_templates)
    return compiled_templates

def _match_reaction(
    rxn_smiles: str, 
    template: Any
) -> bool:
    """
    Check if a reaction SMILES matches a given template.
    
    Args:
        rxn_smiles: Reaction in SMILES format (reactants >> products).
        template: Compiled RDKit reaction template.
        
    Returns:
        True if the reaction matches the template, False otherwise.
    """
    try:
        # Parse the reaction SMILES
        rxn = Chem.ReactionFromSmarts(rxn_smiles)
        if rxn is None:
            return False
        
        # Get reactant and product molecules
        # The template matching works by checking if the transformation
        # defined by the template can be applied to the reaction
        
        # Extract reactants and products from the reaction
        reactant_smarts = rxn.GetReactantPatternSet()
        product_smarts = rxn.GetProductPatternSet()
        
        # Try to match the template against the reaction
        # We check if the template's reactant pattern matches any reactant
        # and if the template's product pattern matches the corresponding product
        
        template_reaction = template['reaction']
        template_reactants = template_reaction.GetReactants()
        template_products = template_reaction.GetProducts()
        
        # Simple matching: check if the template transformation is consistent
        # with the reaction transformation
        # This is a simplified approach; for production, more rigorous matching
        # would be needed (e.g., atom mapping verification)
        
        # Check if the reaction has the same number of reactant/product fragments
        # as the template
        if (rxn.GetNumReactantTemplates() == len(template_reactants) and
            rxn.GetNumProductTemplates() == len(template_products)):
            
            # Try to apply the template to see if it matches
            # RDKit's reaction matching
            for i in range(rxn.GetNumReactantTemplates()):
                reactant = rxn.GetReactantTemplate(i)
                if reactant is None:
                    continue
                
                # Check if template reactant matches any part of the reaction
                # This is a heuristic check
                for j, template_reactant in enumerate(template_reactants):
                    if template_reactant is None:
                        continue
                    # Simple substructure match check
                    # Note: This is a simplified check; real matching would need
                    # proper atom mapping
                    if reactant.HasSubstructMatch(template_reactant):
                        return True
        
        return False
      
    except Exception as e:
        logger.debug(f"Error matching reaction {rxn_smiles[:50]}...: {e}")
        return False

def classify_reaction(
    rxn_smiles: str,
    templates: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Classify a single reaction into SN1, SN2, or Diels-Alder.
    
    Args:
        rxn_smiles: Reaction in SMILES format (reactants >> products).
        templates: Pre-loaded templates dict. If None, loads from config.
        
    Returns:
        Reaction type string ('SN1', 'SN2', 'Diels-Alder') or None if no match.
    """
    if templates is None:
        templates = get_templates()
    
    # Try to match against each template
    for reaction_type, template_info in templates.items():
        try:
            if _match_reaction(rxn_smiles, template_info):
                return reaction_type
        except Exception as e:
            logger.debug(f"Error classifying {rxn_smiles[:50]}... as {reaction_type}: {e}")
            continue
    
    return None

def classify_batch(
    reactions: List[str],
    templates: Optional[Dict[str, Any]] = None
) -> List[Tuple[str, Optional[str]]]:
    """
    Classify a batch of reactions.
    
    Args:
        reactions: List of reaction SMILES strings.
        templates: Pre-loaded templates dict. If None, loads from config.
        
    Returns:
        List of tuples (original_smiles, classified_type).
        classified_type is None if no template matched.
    """
    if templates is None:
        templates = get_templates()
    
    results = []
    for i, rxn_smiles in enumerate(reactions):
        if not rxn_smiles or not isinstance(rxn_smiles, str):
            results.append((rxn_smiles, None))
            continue
        
        # Skip empty or malformed entries
        rxn_smiles = rxn_smiles.strip()
        if not rxn_smiles:
            results.append(('', None))
            continue
        
        classification = classify_reaction(rxn_smiles, templates)
        results.append((rxn_smiles, classification))
        
        if i % 1000 == 0 and i > 0:
            logger.debug(f"Processed {i}/{len(reactions)} reactions")
    
    return results
