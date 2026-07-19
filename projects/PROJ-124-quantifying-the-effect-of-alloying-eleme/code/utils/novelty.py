"""
Novelty check utilities for metallic glass compositions.
Compares candidate compositions against a known alloys database.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import json
import re

from config.environment import get_environment_config

logger = logging.getLogger(__name__)

def load_known_alloys(path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """
    Load the known alloys database from disk.

    Args:
        path: Path to the known alloys CSV. Defaults to data/known_alloys.csv.

    Returns:
        DataFrame containing known alloys, or None if file is missing/empty.
    """
    if path is None:
        config = get_environment_config()
        path = config.data_dir / "known_alloys.csv"

    if not path.exists():
        logger.warning(f"Known alloys file not found at {path}. Novelty checks will return 'unverified_external'.")
        return None

    try:
        df = pd.read_csv(path)
        if df.empty:
            logger.warning(f"Known alloys file at {path} is empty. Novelty checks will return 'unverified_external'.")
            return None
        return df
    except Exception as e:
        logger.error(f"Failed to load known alloys from {path}: {e}")
        return None

def normalize_composition(composition_str: str) -> str:
    """
    Normalize a composition string for comparison.
    Removes spaces, standardizes formatting (e.g., "Fe50Co50" -> "Fe50Co50").
    """
    # Remove all whitespace
    normalized = re.sub(r'\s+', '', composition_str)
    # Ensure consistent case (upper)
    normalized = normalized.upper()
    return normalized

def compositions_match(comp1: str, comp2: str) -> bool:
    """
    Check if two composition strings represent the same alloy.
    Performs normalization before comparison.
    """
    norm1 = normalize_composition(comp1)
    norm2 = normalize_composition(comp2)
    return norm1 == norm2

def check_novelty(composition: str, known_alloys_df: pd.DataFrame) -> str:
    """
    Check if a single composition is novel against the known alloys database.

    Args:
        composition: The composition string to check (e.g., "Fe50Co50").
        known_alloys_df: DataFrame of known alloys.

    Returns:
        "novel" if not found, "known" if found.
    """
    if known_alloys_df is None:
        return "unverified_external"

    norm_comp = normalize_composition(composition)
    
    # Check if composition exists in the 'composition' column
    matches = known_alloys_df['composition'].apply(lambda x: normalize_composition(str(x)) == norm_comp)
    
    if matches.any():
        return "known"
    return "novel"

def batch_check_novelty(compositions: List[str], known_alloys_df: Optional[pd.DataFrame]) -> List[str]:
    """
    Check novelty for a batch of compositions.

    Args:
        compositions: List of composition strings.
        known_alloys_df: DataFrame of known alloys (loaded via load_known_alloys).

    Returns:
        List of novelty status strings ("novel", "known", "unverified_external").
    """
    if known_alloys_df is None:
        return ["unverified_external"] * len(compositions)

    results = []
    for comp in compositions:
        status = check_novelty(comp, known_alloys_df)
        results.append(status)
    
    return results

def main():
    """
    Main entry point for testing the novelty module.
    """
    config = get_environment_config()
    known_df = load_known_alloys(config.data_dir / "known_alloys.csv")
    
    test_comps = ["Fe50Co50", "Cu60Zr40", "NonExistentAlloy"]
    statuses = batch_check_novelty(test_comps, known_df)
    
    for comp, status in zip(test_comps, statuses):
        print(f"{comp}: {status}")

if __name__ == "__main__":
    main()
