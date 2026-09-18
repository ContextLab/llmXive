"""
Validation script for generated datasets (proofs and grids).
Loads generated data, validates logic proofs and grid solvability,
and exits with code 1 if validity/solvability is below the threshold.
"""
import sys
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# Import from existing project modules
from src.utils.config import load_config, Config
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_generated_data(proofs_path: str, grids_path: str) -> Tuple[List[Dict], List[Dict]]:
    """Load generated proofs and grids from JSON files."""
    proofs_path = Path(proofs_path)
    grids_path = Path(grids_path)

    if not proofs_path.exists():
        raise FileNotFoundError(f"Proofs file not found: {proofs_path}")
    if not grids_path.exists():
        raise FileNotFoundError(f"Grids file not found: {grids_path}")

    with open(proofs_path, 'r') as f:
        proofs = json.load(f)
    with open(grids_path, 'r') as f:
        grids = json.load(f)

    return proofs, grids

def validate_logic_proofs(proofs: List[Dict], config: Config) -> Dict[str, Any]:
    """
    Validate logic proofs against the generator.
    Returns metrics including validity rate.
    """
    generator = LogicProofGenerator(seed=config.seed + 1000)  # Different seed for validation context
    valid_count = 0
    invalid_count = 0
    errors = []

    for i, proof_data in enumerate(proofs):
        try:
            # Re-validate using the generator's internal logic
            # The proof_data should contain 'premises', 'conclusion', 'proof_steps'
            premises = proof_data.get('premises', [])
            conclusion = proof_data.get('conclusion')
            proof_steps = proof_data.get('proof_steps', [])

            if not premises or not conclusion:
                logger.warning(f"Proof {i} missing premises or conclusion")
                invalid_count += 1
                errors.append(f"Proof {i}: Missing premises or conclusion")
                continue

            # Use the generator to verify validity
            is_valid, error_msg = generator.validate_proof(premises, conclusion, proof_steps)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                errors.append(f"Proof {i}: {error_msg}")

        except Exception as e:
            logger.error(f"Error validating proof {i}: {e}")
            invalid_count += 1
            errors.append(f"Proof {i}: Validation error - {str(e)}")

    total = len(proofs)
    validity_rate = valid_count / total if total > 0 else 0.0

    return {
        "total": total,
        "valid": valid_count,
        "invalid": invalid_count,
        "validity_rate": validity_rate,
        "threshold": config.validity_threshold,
        "errors": errors[:10]  # Limit error reporting
    }

def validate_grid_worlds(grids: List[Dict], config: Config) -> Dict[str, Any]:
    """
    Validate grid worlds for solvability.
    Returns metrics including solvability rate.
    """
    generator = GridWorldGenerator(seed=config.seed + 2000)  # Different seed
    solvable_count = 0
    unsolvable_count = 0
    errors = []

    for i, grid_data in enumerate(grids):
        try:
            grid_config = grid_data.get('grid_config', {})
            start = tuple(grid_data.get('start', (0, 0)))
            end = tuple(grid_data.get('end', (0, 0)))
            obstacles = grid_data.get('obstacles', [])
            rules = grid_data.get('rules', [])

            if not grid_config:
                logger.warning(f"Grid {i} missing grid_config")
                unsolvable_count += 1
                errors.append(f"Grid {i}: Missing grid_config")
                continue

            # Use the generator to check solvability
            is_solvable, error_msg = generator.validate_solvability(
                grid_config, start, end, obstacles, rules
            )
            if is_solvable:
                solvable_count += 1
            else:
                unsolvable_count += 1
                errors.append(f"Grid {i}: {error_msg}")

        except Exception as e:
            logger.error(f"Error validating grid {i}: {e}")
            unsolvable_count += 1
            errors.append(f"Grid {i}: Validation error - {str(e)}")

    total = len(grids)
    solvability_rate = solvable_count / total if total > 0 else 0.0

    return {
        "total": total,
        "solvable": solvable_count,
        "unsolvable": unsolvable_count,
        "solvability_rate": solvability_rate,
        "threshold": config.validity_threshold,
        "errors": errors[:10]
    }

def validate_dataset(proofs_path: str, grids_path: str, output_path: str) -> bool:
    """
    Main validation function.
    Returns True if validation passes, False otherwise.
    """
    # Load configuration
    config = load_config()
    logger.info(f"Loaded config: validity_threshold={config.validity_threshold}")

    # Load data
    try:
        proofs, grids = load_generated_data(proofs_path, grids_path)
        logger.info(f"Loaded {len(proofs)} proofs and {len(grids)} grids")
    except FileNotFoundError as e:
        logger.error(str(e))
        return False

    # Validate proofs
    logger.info("Validating logic proofs...")
    proof_metrics = validate_logic_proofs(proofs, config)
    logger.info(f"Proof validity rate: {proof_metrics['validity_rate']:.4f} (threshold: {config.validity_threshold})")

    # Validate grids
    logger.info("Validating grid worlds...")
    grid_metrics = validate_grid_worlds(grids, config)
    logger.info(f"Grid solvability rate: {grid_metrics['solvability_rate']:.4f} (threshold: {config.validity_threshold})")

    # Compile report
    report = {
        "proof_validation": proof_metrics,
        "grid_validation": grid_metrics,
        "overall_pass": (
            proof_metrics['validity_rate'] >= config.validity_threshold and
            grid_metrics['solvability_rate'] >= config.validity_threshold
        )
    }

    # Write report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {output_path}")

    # Return success/failure
    return report['overall_pass']

def main():
    """CLI entry point for validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate generated datasets")
    parser.add_argument("--proofs", default="data/generated_proofs.json", help="Path to proofs file")
    parser.add_argument("--grids", default="data/generated_grids.json", help="Path to grids file")
    parser.add_argument("--output", default="data/validation_report.json", help="Path to output report")
    args = parser.parse_args()

    success = validate_dataset(args.proofs, args.grids, args.output)

    if success:
        logger.info("Validation PASSED")
        sys.exit(0)
    else:
        logger.error("Validation FAILED - data does not meet quality thresholds")
        sys.exit(1)

if __name__ == "__main__":
    main()
