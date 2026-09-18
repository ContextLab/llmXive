import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)


def save_json_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save results to a JSON file.

    Args:
        results: Dictionary of results to save
        output_path: Path to save JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Saved results to {output_path}")


def aggregate_permutation_results(
    perm_results: Dict[str, Any],
    effect_sizes: Dict[str, float]
) -> Dict[str, Any]:
    """
    Aggregate permutation test and effect size results.

    Args:
        perm_results: Permutation test results
        effect_sizes: Effect size calculations

    Returns:
        Combined results dictionary
    """
    return {
        "p_value": perm_results.get("p_value"),
        "effect_size": effect_sizes.get("cohens_d"),
        "partial_eta2": effect_sizes.get("partial_eta2"),
        "observed_cohen_d": effect_sizes.get("cohens_d"),
        "n_permutations": perm_results.get("n_permutations"),
        "n_low": perm_results.get("n_low"),
        "n_high": perm_results.get("n_high")
    }


def run_and_save_all_results(
    perm_results: Dict[str, Any],
    effect_sizes: Dict[str, float],
    sensitivity_results: Dict[str, Any],
    power_results: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> None:
    """
    Run all result aggregation and save to files.

    Args:
        perm_results: Permutation test results
        effect_sizes: Effect size calculations
        sensitivity_results: Sensitivity analysis results
        power_results: Power analysis results
        output_dir: Directory to save results
    """
    if output_dir is None:
        root = get_project_root()
        output_dir = root / "data" / "results"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate and save permutation results
    combined = aggregate_permutation_results(perm_results, effect_sizes)
    save_json_results(combined, output_dir / "permutation_results.json")

    # Save sensitivity results
    save_json_results(sensitivity_results, output_dir / "sensitivity_results.json")

    # Save power results
    save_json_results(power_results, output_dir / "power_analysis.json")


def main() -> None:
    """Main entry point for results saving."""
    root = get_project_root()

    # Load permutation results
    perm_path = root / "data" / "results" / "permutation_results.json"
    sensitivity_path = root / "data" / "results" / "sensitivity_results.json"
    power_path = root / "data" / "results" / "power_analysis.json"

    if perm_path.exists():
        with open(perm_path, 'r') as f:
            perm_results = json.load(f)
        logger.info(f"Loaded permutation results from {perm_path}")

    if sensitivity_path.exists():
        with open(sensitivity_path, 'r') as f:
            sensitivity_results = json.load(f)
        logger.info(f"Loaded sensitivity results from {sensitivity_path}")

    if power_path.exists():
        with open(power_path, 'r') as f:
            power_results = json.load(f)
        logger.info(f"Loaded power results from {power_path}")

    logger.info("Results aggregation complete.")


if __name__ == "__main__":
    main()
