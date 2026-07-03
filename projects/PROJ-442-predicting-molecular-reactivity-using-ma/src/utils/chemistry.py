import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import re
from src.modeling.config import load_config

logger = logging.getLogger(__name__)

def get_templates() -> Dict[str, str]:
    """
    Load reaction templates from config.
    """
    config = load_config()
    return config.get("reaction_templates", {})

def classify_reaction(smiles: str) -> Optional[str]:
    """
    Classify a reaction based on SMILES and templates.
    Returns the reaction type or None if no match.
    """
    templates = get_templates()
    # Simple string matching for demonstration; real implementation would use RDKit
    for r_type, pattern in templates.items():
        if pattern in smiles:
            return r_type
    return None

def classify_batch(smiles_list: List[str]) -> List[Tuple[str, Optional[str]]]:
    """
    Classify a batch of reactions.
    Returns list of (smiles, classification).
    """
    return [(smiles, classify_reaction(smiles)) for smiles in smiles_list]

def _match_reaction(smiles: str, pattern: str) -> bool:
    """
    Helper to match a pattern in smiles.
    """
    return pattern in smiles
