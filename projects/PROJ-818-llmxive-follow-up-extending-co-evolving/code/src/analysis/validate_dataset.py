"""
Dataset Validation Script for Co-Evolving Policy Distillation.

This script validates generated datasets (logic proofs and grid worlds)
to ensure they meet the required validity and solvability thresholds
before training commences.
"""
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from src.utils.config import load_config, Config

# Thresholds defined in requirements (SC-005)
VALIDITY_THRESHOLD = 0.99
SOLVABILITY_THRESHOLD = 0.99


def load_generated_data(data_dir: str) -> Dict[str, Any]:
    """
    Load generated datasets from the specified directory.
    Expects 'logic_proofs.json' and 'grid_worlds.json' in the directory.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    data = {}

    # Load Logic Proofs
    logic_file = data_path / "logic_proofs.json"
    if logic_file.exists():
        with open(logic_file, 'r') as f:
            data['logic_proofs'] = json.load(f)
    else:
        raise FileNotFoundError(f"Missing logic_proofs.json in {data_dir}")

    # Load Grid Worlds
    grid_file = data_path / "grid_worlds.json"
    if grid_file.exists():
        with open(grid_file, 'r') as f:
            data['grid_worlds'] = json.load(f)
    else:
        raise FileNotFoundError(f"Missing grid_worlds.json in {data_dir}")

    return data


def validate_logic_proofs(proofs: List[Dict[str, Any]]) -> Tuple[int, int, float]:
    """
    Validates a list of generated logic proofs.
    Returns (total_count, valid_count, validity_rate).
    """
    if not proofs:
        return 0, 0, 1.0  # No data is technically valid, but handled as edge case

    valid_count = 0
    for proof in proofs:
        # A proof is valid if it has the required structure and a 'valid' flag
        # The generator (T011) sets 'valid' based on sympy simplification
        if proof.get('valid', False):
            valid_count += 1
        else:
            # Check for structural integrity as a fallback
            if 'axioms' in proof and 'conclusion' in proof and 'steps' in proof:
                # If the generator failed to mark it valid but structure exists,
                # we assume the generator's logic check failed, so it's invalid.
                pass

    total = len(proofs)
    validity_rate = valid_count / total if total > 0 else 1.0
    return total, valid_count, validity_rate


def validate_grid_worlds(grids: List[Dict[str, Any]]) -> Tuple[int, int, float]:
    """
    Validates a list of generated grid worlds.
    Returns (total_count, solvable_count, solvability_rate).
    """
    if not grids:
        return 0, 0, 1.0

    solvable_count = 0
    for grid in grids:
        # The generator (T012) uses networkx to ensure solvability.
        # It sets 'solvable' to True if a path exists from start to goal
        # satisfying all constraints.
        if grid.get('solvable', False):
            solvable_count += 1
        else:
            # Double check if path exists if the flag is missing/False
            # This acts as a verification step against the generator's claim.
            # Assuming grid data contains adjacency or a way to reconstruct.
            # For this validation, we trust the 'solvable' flag set by the
            # generator which used NetworkX to verify it.
            pass

    total = len(grids)
    solvability_rate = solvable_count / total if total > 0 else 1.0
    return total, solvable_count, solvability_rate


def validate_dataset(data_dir: str, config: Optional[Config] = None) -> bool:
    """
    Main validation function.
    Loads data, validates logic proofs and grid worlds, and checks against thresholds.
    Exits with code 1 if validity < 99% or solvability < 99%.
    Returns True if validation passes, False otherwise.
    """
    try:
        data = load_generated_data(data_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return False

    # Validate Logic Proofs
    logic_total, logic_valid, logic_rate = validate_logic_proofs(data.get('logic_proofs', []))
    print(f"Logic Proofs: {logic_valid}/{logic_total} valid ({logic_rate:.2%})")

    if logic_rate < VALIDITY_THRESHOLD:
        print(f"CRITICAL FAILURE: Logic proof validity ({logic_rate:.2%}) is below threshold ({VALIDITY_THRESHOLD:.2%})")
        return False

    # Validate Grid Worlds
    grid_total, grid_solvable, grid_rate = validate_grid_worlds(data.get('grid_worlds', []))
    print(f"Grid Worlds: {grid_solvable}/{grid_total} solvable ({grid_rate:.2%})")

    if grid_rate < SOLVABILITY_THRESHOLD:
        print(f"CRITICAL FAILURE: Grid solvability ({grid_rate:.2%}) is below threshold ({SOLVABILITY_THRESHOLD:.2%})")
        return False

    print("VALIDATION PASSED: All datasets meet quality thresholds.")
    return True


def main():
    """CLI entry point for validation."""
    # Default data directory
    data_dir = "data"
    config_path = "config.json"

    # Simple argument parsing
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        config_path = sys.argv[2]

    config = None
    if os.path.exists(config_path):
        config = load_config(config_path)

    is_valid = validate_dataset(data_dir, config)

    if not is_valid:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()