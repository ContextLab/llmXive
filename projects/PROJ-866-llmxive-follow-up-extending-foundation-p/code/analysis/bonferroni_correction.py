import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np


def load_regression_stats(filepath: str) -> List[Dict[str, Any]]:
    """Load raw regression statistics from a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List of raw p-values.
        n_tests: Total number of hypothesis tests performed.

    Returns:
        List of corrected p-values (capped at 1.0).
    """
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected


def apply_bonferroni_to_covariates(
    stats: List[Dict[str, Any]], covariate_names: List[str]
) -> Dict[str, float]:
    """Apply Bonferroni correction specifically to covariate p-values.

    Args:
        stats: List of regression statistics dictionaries.
        covariate_names: Names of covariates to correct.

    Returns:
        Dictionary mapping covariate names to corrected p-values.
    """
    # Extract p-values for the specified covariates
    p_values = []
    for stat in stats:
        if stat.get("name") in covariate_names:
            p_values.append(stat.get("p_value", 1.0))

    if not p_values:
        return {}

    # Apply correction
    corrected = bonferroni_correction(p_values, len(p_values))

    # Map back to names
    result = {}
    for name, p in zip(covariate_names, corrected):
        # Find the corresponding original stat to ensure we have the right one
        for stat in stats:
            if stat.get("name") == name:
                result[name] = p
                break
    return result


def save_corrected_pvalues(
    corrected_pvalues: Dict[str, float], output_path: str
) -> None:
    """Save corrected p-values to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(corrected_pvalues, f, indent=2)


def main() -> None:
    """Main entry point for Bonferroni correction script."""
    input_path = "data/processed/regression_stats.json"
    output_path = "data/processed/corrected_pvalues.json"

    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        sys.exit(1)

    stats = load_regression_stats(input_path)
    covariates = ["depth", "complexity"]
    corrected = apply_bonferroni_to_covariates(stats, covariates)
    save_corrected_pvalues(corrected, output_path)
    print(f"Corrected p-values saved to {output_path}")


if __name__ == "__main__":
    main()
