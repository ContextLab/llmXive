import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from ..config import get_data_path

logger = logging.getLogger(__name__)

def save_json_results(
    results: Dict[str, Any],
    filename: str
) -> None:
    """
    Save results to a JSON file.
    
    Args:
        results: Dictionary of results.
        filename: Output filename.
    """
    output_path = get_data_path() / "results" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def aggregate_permutation_results(
    permutation_results: Dict[str, Any],
    effect_results: Dict[str, Any],
    power_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate results from permutation, effect size, and power analyses.
    
    Args:
        permutation_results: Results from permutation test.
        effect_results: Results from effect size calculation.
        power_results: Results from power analysis.
        
    Returns:
        Aggregated results dictionary.
    """
    return {
        "permutation": permutation_results,
        "effect_size": effect_results,
        "power_analysis": power_results
    }

def run_and_save_all_results(
    permutation_results: Dict[str, Any],
    effect_results: Dict[str, Any],
    power_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any]
) -> None:
    """
    Run aggregation and save all results.
    
    Args:
        permutation_results: Permutation test results.
        effect_results: Effect size results.
        power_results: Power analysis results.
        sensitivity_results: Sensitivity analysis results.
    """
    save_json_results(permutation_results, "permutation_results.json")
    save_json_results(effect_results, "effect_size_results.json")
    save_json_results(power_results, "power_analysis.json")
    save_json_results(sensitivity_results, "sensitivity_results.json")

def main() -> int:
    """Main entry point for results script."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Results module ready.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())