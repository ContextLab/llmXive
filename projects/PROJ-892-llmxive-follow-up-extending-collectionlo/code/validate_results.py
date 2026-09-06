"""
Task T053: Result Aggregation Verification

Verifies the integrity of data/results.csv after all generation loops.
Checks for:
1. Non-empty rows for each quantization level (FP16, INT8, INT4).
2. Non-null values for similarity_score, lpips_distance, and cesr_score.
3. Correct mapping of effect to subspace_rank.

If any validation fails, the script halts and logs a "Result Integrity Error".
"""

import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_QUANTIZATION_LEVELS = {"fp16", "int8", "int4"}
REQUIRED_COLUMNS = {
    "prompt", "seed", "quantization_level", "similarity_score",
    "lpips_distance", "cesr_score", "image_path", "subspace_rank", "effect"
}
RESULTS_CSV_PATH = "data/results.csv"
SUBSPACE_RANKS_JSON_PATH = "data/subspace_ranks_merged.json"

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def validate_results_csv() -> bool:
    """
    Validates the integrity of data/results.csv.
    Returns True if validation passes, False otherwise.
    """
    project_root = get_project_root()
    results_path = project_root / RESULTS_CSV_PATH
    subspace_ranks_path = project_root / SUBSPACE_RANKS_JSON_PATH

    # 1. Check if results.csv exists
    if not results_path.exists():
        logger.error("Result Integrity Error: data/results.csv not found.")
        return False

    # 2. Check if subspace_ranks_merged.json exists (needed for validation)
    if not subspace_ranks_path.exists():
        logger.error("Result Integrity Error: data/subspace_ranks_merged.json not found for rank validation.")
        return False

    try:
        # Load subspace ranks for validation
        with open(subspace_ranks_path, 'r') as f:
            subspace_ranks_data = json.load(f)
        
        # Build a map of effect -> subspace_rank for validation
        # The JSON structure is expected to be a list of dicts or a dict of dicts
        valid_ranks = {}
        if isinstance(subspace_ranks_data, list):
            for item in subspace_ranks_data:
                if 'effect' in item and 'subspace_rank' in item:
                    valid_ranks[item['effect'].lower().strip()] = item['subspace_rank']
        elif isinstance(subspace_ranks_data, dict):
            for effect, rank_info in subspace_ranks_data.items():
                if isinstance(rank_info, dict) and 'subspace_rank' in rank_info:
                    valid_ranks[effect.lower().strip()] = rank_info['subspace_rank']
                elif isinstance(rank_info, (int, float)):
                    valid_ranks[effect.lower().strip()] = rank_info

        if not valid_ranks:
            logger.warning("No valid subspace ranks found in data/subspace_ranks_merged.json.")

    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Result Integrity Error: Failed to load subspace ranks: {e}")
        return False

    # 3. Read and validate CSV
    try:
        with open(results_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check headers
            if reader.fieldnames is None:
                logger.error("Result Integrity Error: data/results.csv is empty or has no headers.")
                return False
            
            actual_columns = set(reader.fieldnames)
            missing_columns = REQUIRED_COLUMNS - actual_columns
            if missing_columns:
                logger.error(f"Result Integrity Error: Missing required columns in data/results.csv: {missing_columns}")
                return False

            rows = list(reader)
            
            if not rows:
                logger.error("Result Integrity Error: data/results.csv contains no data rows.")
                return False

            # Track found quantization levels
            found_levels: Set[str] = set()
            row_count = 0

            for row_idx, row in enumerate(rows):
                row_count += 1
                
                # Check for non-null critical scores
                critical_fields = ["similarity_score", "lpips_distance", "cesr_score"]
                for field in critical_fields:
                    val = row.get(field)
                    if val is None or val == "":
                        logger.error(f"Result Integrity Error: Row {row_idx} has null/empty '{field}'.")
                        return False
                    
                    # Attempt to convert to float to ensure it's a valid number
                    try:
                        float(val)
                    except ValueError:
                        logger.error(f"Result Integrity Error: Row {row_idx} has invalid numeric value for '{field}': {val}")
                        return False

                # Check quantization level
                q_level = row.get("quantization_level", "").lower().strip()
                if q_level:
                    found_levels.add(q_level)
                
                # Validate effect to subspace_rank mapping
                effect = row.get("effect", "").lower().strip()
                rank_str = row.get("subspace_rank", "")
                
                if effect and effect in valid_ranks:
                    expected_rank = valid_ranks[effect]
                    try:
                        actual_rank = int(rank_str) if rank_str else None
                        if actual_rank is not None and actual_rank != expected_rank:
                            logger.warning(f"Row {row_idx}: Effect '{effect}' has rank {actual_rank}, expected {expected_rank}.")
                            # Depending on strictness, this might be an error. 
                            # For T053, we check for correctness, so mismatch is an error if data exists.
                            # However, if the JSON is the source of truth, we just ensure the CSV matches it.
                            # If the CSV has a rank but it doesn't match the JSON, that's an integrity error.
                            if rank_str: # If CSV claims a rank, it must match
                                logger.error(f"Result Integrity Error: Row {row_idx} effect '{effect}' subspace_rank mismatch. CSV: {actual_rank}, JSON: {expected_rank}")
                                return False
                    except ValueError:
                        logger.error(f"Result Integrity Error: Row {row_idx} has invalid subspace_rank: {rank_str}")
                        return False
                elif effect and effect not in valid_ranks:
                    logger.warning(f"Row {row_idx}: Effect '{effect}' not found in subspace ranks map.")
                    # If we have an effect but no rank data, we can't validate the mapping strictly,
                    # but we flag it. The task requires "Correct mapping", so missing data is a fail.
                    if not rank_str:
                        logger.error(f"Result Integrity Error: Row {row_idx} effect '{effect}' has no subspace_rank.")
                        return False

            # 4. Check for non-empty rows for each quantization level
            missing_levels = REQUIRED_QUANTIZATION_LEVELS - found_levels
            if missing_levels:
                logger.error(f"Result Integrity Error: Missing rows for quantization levels: {missing_levels}. Found: {found_levels}")
                return False

            logger.info(f"Validation passed. Checked {row_count} rows. Found levels: {found_levels}")
            return True

    except csv.Error as e:
        logger.error(f"Result Integrity Error: Failed to parse data/results.csv: {e}")
        return False
    except IOError as e:
        logger.error(f"Result Integrity Error: Failed to read data/results.csv: {e}")
        return False

def main():
    """Main entry point for the validation script."""
    logger.info("Starting Result Aggregation Verification (T053)...")
    
    if validate_results_csv():
        logger.info("Result Aggregation Verification: SUCCESS")
        sys.exit(0)
    else:
        logger.error("Result Aggregation Verification: FAILED - Pipeline halted due to integrity error.")
        sys.exit(1)

if __name__ == "__main__":
    main()