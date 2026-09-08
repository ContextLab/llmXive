"""
Results aggregation and serialization module.
Handles saving permutation test results, sensitivity analyses, and LOIO results.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

from config import get_project_root, ensure_directories, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)


def save_json_results(data: Dict[str, Any], output_path: Path) -> None:
    """
    Save a dictionary of results to a JSON file.

    Args:
        data: Dictionary containing results to save.
        output_path: Path to the output JSON file.
    """
    ensure_directories()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")


def aggregate_permutation_results(
    p_value: float,
    effect_size: float,
    partial_eta2: float,
    observed_cohen_d: float,
    n_permutations: int = 10000,
    n_samples: int = 0
) -> Dict[str, Any]:
    """
    Aggregate permutation test results into a standardized dictionary.

    Args:
        p_value: Permutation p-value.
        effect_size: Permutation effect size (Cohen's d).
        partial_eta2: Partial eta-squared for compatibility.
        observed_cohen_d: Observed Cohen's d value.
        n_permutations: Number of permutations run.
        n_samples: Total number of samples used.

    Returns:
        Dictionary with standardized result keys.
    """
    return {
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "partial_eta2": float(partial_eta2),
        "observed_cohen_d": float(observed_cohen_d),
        "n_permutations": int(n_permutations),
        "n_samples": int(n_samples),
        "method": "Permutation Test",
        "alpha": 0.05
    }


def run_and_save_all_results(
    permutation_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    power_results: Optional[Dict[str, Any]] = None
) -> None:
    """
    Run all analysis components and save results to JSON files.

    This function orchestrates the saving of:
    1. Permutation test results (p_value, effect_size, etc.)
    2. Sensitivity analysis results (threshold sweep and LOIO)
    3. Power analysis results (if available)

    Args:
        permutation_results: Results from the permutation test.
        sensitivity_results: Results from sensitivity analyses.
        power_results: Optional power analysis results.
    """
    project_root = get_project_root()
    results_dir = project_root / "data" / "results"
    ensure_directories()

    # Save permutation results
    permutation_path = results_dir / "permutation_results.json"
    save_json_results(permutation_results, permutation_path)

    # Save sensitivity results
    sensitivity_path = results_dir / "sensitivity_results.json"
    save_json_results(sensitivity_results, sensitivity_path)

    # Save power results if available
    if power_results:
        power_path = results_dir / "power_analysis.json"
        save_json_results(power_results, power_path)

    logger.info("All results saved successfully")


def main() -> None:
    """
    Main entry point for T036: Save results to JSON files.
    
    This function loads the computed results from the analysis modules,
    aggregates them, and saves them to the required JSON files.
    """
    logger.info("Starting T036: Save results to JSON files")
    
    project_root = get_project_root()
    results_dir = project_root / "data" / "results"
    ensure_directories()
    
    # Load permutation results from T034
    permutation_path = results_dir / "permutation_results.json"
    if not permutation_path.exists():
        logger.error(f"Permutation results file not found: {permutation_path}")
        raise FileNotFoundError(f"Missing permutation results: {permutation_path}")
    
    with open(permutation_path, 'r', encoding='utf-8') as f:
        permutation_data = json.load(f)
    
    # Load power analysis results from T034b
    power_path = results_dir / "power_analysis.json"
    power_data = None
    if power_path.exists():
        with open(power_path, 'r', encoding='utf-8') as f:
            power_data = json.load(f)
        logger.info(f"Loaded power analysis results from {power_path}")
    
    # Load sensitivity results from T035a and T035b
    sensitivity_path = results_dir / "sensitivity_results.json"
    if not sensitivity_path.exists():
        logger.error(f"Sensitivity results file not found: {sensitivity_path}")
        raise FileNotFoundError(f"Missing sensitivity results: {sensitivity_path}")
    
    with open(sensitivity_path, 'r', encoding='utf-8') as f:
        sensitivity_data = json.load(f)
    
    # Verify required keys in permutation results
    required_perm_keys = ['p_value', 'effect_size', 'observed_cohen_d']
    for key in required_perm_keys:
        if key not in permutation_data:
            logger.error(f"Missing required key in permutation results: {key}")
            raise KeyError(f"Missing required key in permutation results: {key}")
    
    # Verify required keys in sensitivity results
    required_sens_keys = ['sensitivity_sweep', 'loio_results']
    for key in required_sens_keys:
        if key not in sensitivity_data:
            logger.error(f"Missing required key in sensitivity results: {key}")
            raise KeyError(f"Missing required key in sensitivity results: {key}")
    
    # Aggregate and re-save results to ensure consistency
    aggregated_permutation = {
        "p_value": permutation_data['p_value'],
        "effect_size": permutation_data['effect_size'],
        "partial_eta2": permutation_data.get('partial_eta2', None),
        "observed_cohen_d": permutation_data['observed_cohen_d'],
        "n_permutations": permutation_data.get('n_permutations', 10000),
        "n_samples": permutation_data.get('n_samples', 0),
        "method": "Permutation Test",
        "alpha": 0.05
    }
    
    # Save final results
    save_json_results(aggregated_permutation, permutation_path)
    save_json_results(sensitivity_data, sensitivity_path)
    
    if power_data:
        save_json_results(power_data, power_path)
    
    logger.info("T036 completed successfully: All results saved and verified")
    logger.info(f"  - Permutation results: {permutation_path}")
    logger.info(f"  - Sensitivity results: {sensitivity_path}")
    if power_data:
        logger.info(f"  - Power analysis: {power_path}")


if __name__ == "__main__":
    main()