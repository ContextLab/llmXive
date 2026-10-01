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
import argparse

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

def check_novelty_dry_run(composition: str, known_alloys_df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Simulate the novelty check process without making network requests or
    performing actual lookups. Logs the intended query path and expected outcome.

    Args:
        composition: The composition string to check.
        known_alloys_df: DataFrame of known alloys.

    Returns:
        A dictionary describing the simulated check process and expected result.
    """
    log_entry = {
        "composition": composition,
        "dry_run": True,
        "steps": []
    }

    # Step 1: External Database Query Simulation
    log_entry["steps"].append({
        "action": "query_external_db",
        "target": "Materials Project API",
        "status": "simulated_skip",
        "reason": "Dry-run mode: skipping actual network request"
    })

    # Step 2: Local File Check Simulation
    if known_alloys_df is not None:
        log_entry["steps"].append({
            "action": "check_local_file",
            "target": "data/known_alloys.csv",
            "status": "simulated_check",
            "expected_logic": f"Search for normalized '{normalize_composition(composition)}' in 'composition' column"
        })
        
        # Simulate the check logic for logging purposes (don't actually return the result)
        norm_comp = normalize_composition(composition)
        matches = known_alloys_df['composition'].apply(lambda x: normalize_composition(str(x)) == norm_comp)
        expected_result = "known" if matches.any() else "novel"
        
        log_entry["steps"].append({
            "action": "simulate_result",
            "expected_status": expected_result,
            "note": "This is a simulated outcome based on the local file content"
        })
    else:
        log_entry["steps"].append({
            "action": "check_local_file",
            "target": "data/known_alloys.csv",
            "status": "skipped",
            "reason": "Local file missing or empty in dry-run simulation"
        })
        log_entry["steps"].append({
            "action": "simulate_result",
            "expected_status": "unverified_external",
            "note": "Fallback to 'unverified_external' due to missing local data"
        })

    return log_entry

def batch_check_novelty_dry_run(compositions: List[str], known_alloys_df: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
    """
    Simulate the novelty check process for a batch of compositions.

    Args:
        compositions: List of composition strings.
        known_alloys_df: DataFrame of known alloys.

    Returns:
        List of dictionaries describing the simulated check processes.
    """
    results = []
    for comp in compositions:
        result = check_novelty_dry_run(comp, known_alloys_df)
        results.append(result)
    return results

def main():
    """
    Main entry point for testing the novelty module.
    Supports a --dry-run flag to simulate checks without external API calls.
    """
    parser = argparse.ArgumentParser(description="Novelty Check Utility")
    parser.add_argument('--dry-run', action='store_true', help='Simulate query logic without network requests')
    args = parser.parse_args()

    config = get_environment_config()
    known_df = load_known_alloys(config.data_dir / "known_alloys.csv")
    
    test_comps = ["Fe50Co50", "Cu60Zr40", "NonExistentAlloy"]
    
    if args.dry_run:
        logger.info("Running in DRY-RUN mode. Simulating query logic...")
        logger.info("=" * 60)
        results = batch_check_novelty_dry_run(test_comps, known_df)
        for i, res in enumerate(results):
            logger.info(f"--- Simulation for: {res['composition']} ---")
            for step in res['steps']:
                logger.info(f"  Step: {step['action']}")
                logger.info(f"    Target: {step.get('target', 'N/A')}")
                logger.info(f"    Status: {step['status']}")
                if 'reason' in step:
                    logger.info(f"    Reason: {step['reason']}")
                if 'expected_logic' in step:
                    logger.info(f"    Logic: {step['expected_logic']}")
                if 'expected_status' in step:
                    logger.info(f"    Expected Result: {step['expected_status']}")
            logger.info("=" * 60)
        
        logger.info("Dry-run complete. No external requests were made.")
    else:
        logger.info("Running standard novelty check...")
        statuses = batch_check_novelty(test_comps, known_df)
        
        for comp, status in zip(test_comps, statuses):
            print(f"{comp}: {status}")

if __name__ == "__main__":
    main()