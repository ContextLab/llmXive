import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories, get_config_dict
from utils.logging import get_perturbation_logger, init_logging

OUTPUT_FILE = "data/processed/perturbation_candidates.json"

def load_candidates_from_pool() -> List[Dict[str, Any]]:
    """
    Loads the raw pool of generated candidates from the intermediate file
    produced by T017 (generate_perturbations.py).
    
    Expected input path: data/processed/perturbation_pool.json
    """
    pool_path = PROJECT_ROOT / "data/processed/perturbation_pool.json"
    if not pool_path.exists():
        logger = get_perturbation_logger()
        logger.error(f"Candidate pool file not found: {pool_path}")
        raise FileNotFoundError(f"Candidate pool file not found: {pool_path}")
    
    with open(pool_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def log_all_candidates(candidates: List[Dict[str, Any]]) -> int:
    """
    Writes ALL generated candidates (both included and excluded) to the 
    canonical log file: data/processed/perturbation_candidates.json.
    
    The output schema matches the contract defined in T011:
    - task_id
    - perturbation_type
    - raw_score
    - is_valid
    - reason
    
    Args:
        candidates: List of candidate dicts from the pool.
        
    Returns:
        The number of candidates written.
    """
    ensure_directories()
    output_path = PROJECT_ROOT / OUTPUT_FILE
    
    logger = get_perturbation_logger()
    logger.info(f"Logging {len(candidates)} candidates to {output_path}")
    
    # Prepare records to ensure schema compliance
    records = []
    for candidate in candidates:
        record = {
            "task_id": candidate.get("task_id"),
            "perturbation_type": candidate.get("perturbation_type"),
            "raw_score": candidate.get("raw_score"),
            "is_valid": candidate.get("is_valid"),
            "reason": candidate.get("reason", "No reason provided")
        }
        # Validate required fields exist
        if any(v is None for v in record.values()):
            logger.warning(f"Incomplete candidate record found: {candidate}")
            # Skip malformed records or fill with defaults? 
            # Per spec, we log what we have, but ensure keys exist.
            # If critical data is missing, we might skip or mark as invalid.
            if not record["task_id"] or record["perturbation_type"] is None:
                continue
        records.append(record)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Successfully logged {len(records)} candidates to {output_path}")
    return len(records)

def main():
    """
    Main entry point for T018.
    Loads the candidate pool and writes the full log.
    """
    init_logging()
    logger = get_perturbation_logger()
    logger.info("Starting T018: Log Perturbation Candidates")
    
    try:
        candidates = load_candidates_from_pool()
        count = log_all_candidates(candidates)
        logger.info(f"T018 Complete: Logged {count} candidates.")
    except FileNotFoundError as e:
        logger.error(f"Failed to load candidates: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during logging: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
