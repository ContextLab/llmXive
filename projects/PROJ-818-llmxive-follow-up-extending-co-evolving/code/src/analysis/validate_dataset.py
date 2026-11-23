import sys
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

from src.utils.config import load_config

logger = logging.getLogger(__name__)

def load_generated_data(filepath: str) -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def validate_logic_proofs(proofs: List[Dict[str, Any]], threshold: float) -> Tuple[bool, float]:
    """
    Validate logic proofs.
    Returns (is_valid, validity_score).
    """
    if not proofs:
        return False, 0.0
    # Simplified validation: check if all proofs have 'solution' and 'problem'
    valid_count = 0
    for p in proofs:
        if 'problem' in p and 'solution' in p:
            valid_count += 1
    score = valid_count / len(proofs)
    return score >= threshold, score

def validate_grid_worlds(grids: List[Dict[str, Any]], threshold: float) -> Tuple[bool, float]:
    """
    Validate grid worlds.
    Returns (is_valid, solvability_score).
    """
    if not grids:
        return False, 0.0
    # Simplified validation: check if all grids have 'grid' and 'solution_path'
    valid_count = 0
    for g in grids:
        if 'grid' in g and 'solution_path' in g:
            valid_count += 1
    score = valid_count / len(grids)
    return score >= threshold, score

def validate_dataset(args):
    """
    Main validation function.
    Loads proofs and grids, validates them, and writes a report.
    """
    config = load_config()
    threshold = config.get('VALIDITY_THRESHOLD', 0.95)

    proofs_path = args.proofs
    grids_path = args.grids
    output_path = args.output

    try:
        proofs = load_generated_data(proofs_path)
        grids = load_generated_data(grids_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    logic_valid, logic_score = validate_logic_proofs(proofs, threshold)
    grid_valid, grid_score = validate_grid_worlds(grids, threshold)

    report = {
        "logic_proofs": {
            "count": len(proofs),
            "valid": logic_valid,
            "score": logic_score
        },
        "grid_worlds": {
            "count": len(grids),
            "valid": grid_valid,
            "score": grid_score
        },
        "overall_valid": logic_valid and grid_valid,
        "threshold": threshold
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {output_path}")

    if not report["overall_valid"]:
        logger.error("Validation failed. Threshold not met.")
        sys.exit(1)

    return 0

def main(args):
    return validate_dataset(args)
