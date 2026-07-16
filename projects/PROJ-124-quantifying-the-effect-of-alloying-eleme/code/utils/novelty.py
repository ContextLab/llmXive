"""
Novelty checking utilities for alloy composition screening.

This module provides functions to check if a proposed alloy composition
exists in a database of known alloys, supporting the novelty screening
requirement (FR-013).
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import json

logger = logging.getLogger(__name__)

# Path to the known alloys database
KNOWN_ALLOYS_PATH = Path("data/known_alloys.csv")

def load_known_alloys() -> Optional[pd.DataFrame]:
    """
    Load the known alloys database from CSV.
    
    Returns:
        DataFrame with known alloys, or None if file doesn't exist.
    """
    if not KNOWN_ALLOYS_PATH.exists():
        logger.warning(f"Known alloys file not found at {KNOWN_ALLOYS_PATH}. "
                     "Novelty checks will return 'unverified_external'.")
        return None
    
    try:
        df = pd.read_csv(KNOWN_ALLOYS_PATH)
        logger.info(f"Loaded {len(df)} known alloys from {KNOWN_ALLOYS_PATH}")
        return df
    except Exception as e:
        logger.error(f"Error loading known alloys: {e}")
        return None

def normalize_composition(composition: str) -> str:
    """
    Normalize a composition string for consistent comparison.
    
    Normalization steps:
    1. Strip whitespace
    2. Convert to uppercase
    3. Sort elements alphabetically (assuming format "Element1:val1,Element2:val2")
    
    Args:
        composition: Composition string like "Fe:0.5,Cu:0.5"
        
    Returns:
        Normalized composition string
    """
    if not composition or not isinstance(composition, str):
        return ""
    
    composition = composition.strip().upper()
    
    # Parse and sort elements for consistent comparison
    try:
        parts = composition.split(",")
        element_parts = []
        for part in parts:
            if ":" in part:
                elem, val = part.split(":", 1)
                element_parts.append((elem.strip(), val.strip()))
            else:
                # Handle case without explicit values (just element names)
                element_parts.append((part.strip(), ""))
        
        # Sort by element name
        element_parts.sort(key=lambda x: x[0])
        
        # Reconstruct
        normalized = ",".join([f"{elem}:{val}" if val else elem 
                              for elem, val in element_parts])
        return normalized
    except Exception as e:
        logger.warning(f"Could not normalize composition '{composition}': {e}")
        return composition

def compositions_match(comp1: str, comp2: str, tolerance: float = 0.01) -> bool:
    """
    Check if two compositions match within a tolerance.
    
    Args:
        comp1: First composition string
        comp2: Second composition string
        tolerance: Tolerance for numeric comparison (default 0.01)
        
    Returns:
        True if compositions match, False otherwise
    """
    norm1 = normalize_composition(comp1)
    norm2 = normalize_composition(comp2)
    
    if not norm1 or not norm2:
        return False
    
    # Exact string match after normalization
    if norm1 == norm2:
        return True
    
    # Try numeric comparison
    try:
        parts1 = {}
        parts2 = {}
        
        for part in norm1.split(","):
            if ":" in part:
                elem, val = part.split(":", 1)
                parts1[elem.strip()] = float(val.strip())
            else:
                parts1[part.strip()] = 1.0
        
        for part in norm2.split(","):
            if ":" in part:
                elem, val = part.split(":", 1)
                parts2[elem.strip()] = float(val.strip())
            else:
                parts2[part.strip()] = 1.0
        
        # Check if same elements
        if set(parts1.keys()) != set(parts2.keys()):
            return False
        
        # Check if values match within tolerance
        for elem in parts1:
            if abs(parts1[elem] - parts2[elem]) > tolerance:
                return False
        
        return True
    except Exception as e:
        logger.debug(f"Numeric comparison failed: {e}")
        return False

def check_novelty(composition: str, known_alloys: Optional[pd.DataFrame] = None) -> Tuple[str, bool]:
    """
    Check if a composition is novel (not in known alloys database).
    
    Args:
        composition: Composition string to check
        known_alloys: Optional DataFrame of known alloys. If None, loads from disk.
        
    Returns:
        Tuple of (novelty_status, is_novel)
        - novelty_status: "novel", "known", or "unverified_external"
        - is_novel: True if novel, False if known
    """
    if known_alloys is None:
        known_alloys = load_known_alloys()
    
    if known_alloys is None:
        return ("unverified_external", True)
    
    # Check if composition column exists
    composition_col = None
    for col in known_alloys.columns:
        if "composition" in col.lower():
            composition_col = col
            break
    
    if composition_col is None:
        logger.warning("No 'composition' column found in known alloys. "
                     "Returning 'unverified_external'.")
        return ("unverified_external", True)
    
    norm_composition = normalize_composition(composition)
    
    # Check for matches
    for _, row in known_alloys.iterrows():
        if compositions_match(norm_composition, str(row[composition_col])):
            return ("known", False)
    
    return ("novel", True)

def batch_check_novelty(compositions: List[str], 
                      known_alloys: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
    """
    Check novelty for a batch of compositions.
    
    Args:
        compositions: List of composition strings to check
        known_alloys: Optional DataFrame of known alloys
        
    Returns:
        List of dicts with composition, novelty_status, and is_novel
    """
    if known_alloys is None:
        known_alloys = load_known_alloys()
    
    results = []
    for comp in compositions:
        status, is_novel = check_novelty(comp, known_alloys)
        results.append({
            "composition": comp,
            "novelty_status": status,
            "is_novel": is_novel
        })
    
    return results

def main():
    """Main function for testing novelty check utilities."""
    # Test normalization
    test_comps = [
        "Fe:0.5,Cu:0.5",
        "Cu:0.5,Fe:0.5",
        "fe:0.5,cu:0.5",
        "Fe:0.6,Cu:0.4"
    ]
    
    logger.info("Testing composition normalization:")
    for comp in test_comps:
        normalized = normalize_composition(comp)
        logger.info(f"  '{comp}' -> '{normalized}'")
    
    # Test matching
    logger.info("\nTesting composition matching:")
    pairs = [
        ("Fe:0.5,Cu:0.5", "Cu:0.5,Fe:0.5", True),
        ("Fe:0.5,Cu:0.5", "Fe:0.6,Cu:0.4", False),
        ("Fe:0.5,Cu:0.5", "Fe:0.501,Cu:0.499", True)  # Within tolerance
    ]
    
    for c1, c2, expected in pairs:
        match = compositions_match(c1, c2)
        status = "✓" if match == expected else "✗"
        logger.info(f"  {status} '{c1}' vs '{c2}': {match} (expected {expected})")
    
    # Test with known alloys file
    logger.info("\nTesting with known alloys database:")
    known = load_known_alloys()
    if known is not None:
        test_comp = "Fe:0.5,Cu:0.5"
        status, is_novel = check_novelty(test_comp, known)
        logger.info(f"  Composition '{test_comp}': {status} (is_novel={is_novel})")
    else:
        logger.info("  Known alloys file not available for testing")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
