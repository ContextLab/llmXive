"""
Lexicon loading and matching logic.
"""
import csv
import logging
from pathlib import Path
from typing import Dict, List, Set, Any

from .utils import setup_logging, PipelineError

logger = setup_logging(__name__)

def load_lexicon(path: Path = None) -> Dict[str, Dict[str, Any]]:
    """
    Load the demographic lexicon from CSV.
    """
    if path is None:
        path = Path("data/raw/lexicon.csv")
    
    if not path.exists():
        # Fallback to a minimal in-memory lexicon if file missing
        # In a real scenario, this should raise or fetch from URL
        logger.warning(f"Lexicon file {path} not found. Using minimal fallback.")
        return {
            "man": {"category": "male", "weight": 1.0},
            "woman": {"category": "female", "weight": 1.0},
            "boy": {"category": "male", "weight": 1.0},
            "girl": {"category": "female", "weight": 1.0}
        }
    
    lexicon = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row['term'].lower()
            lexicon[term] = {
                'category': row['category'],
                'weight': float(row['weight'])
            }
    return lexicon

def match_lexicon(tokens: List[str], lexicon: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Match tokens against the lexicon.
    Returns list of matched terms.
    """
    matches = []
    for token in tokens:
        if token in lexicon:
            matches.append(token)
    return matches
