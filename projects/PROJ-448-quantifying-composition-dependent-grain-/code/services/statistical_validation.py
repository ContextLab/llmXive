"""
Statistical Validation Service for Cooperative Effects Analysis.

Orchestrates joint verification of:
1. Interaction term significance (p-value < 0.05 AND |coefficient| > 0.01 eV)
2. K-fold cross-validation stability (R² std dev <= 0.05)

Produces a unified validation report.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Import from project API surface
from code.config import PROCESSED_PATH, get_logger
from code.errors import ValidationError

logger = get_logger(__name__)


def load_regression_results() -> Dict[str, Any]:
    """
    Load regression coefficients and p-values from T021b output.
    Expected file: data/processed/regression_results.json
    """
    path = PROCESSED_PATH / "regression_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Regression results file not found: {path}")

    with open(path, 'r') as f:
        return json.load(f)


def load_cv_results() -> Dict[str, Any]:
    """
    Load cross-validation results from T030 output.
    Expected file: data/processed/cross_validation_results.json
    """
    path = PROCESSED_PATH / "cross_validation_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Cross-validation results file not found: {path}")

    with open(path, 'r') as f:
        return json.load(f)


def check_interaction_significance(
    regression_results: Dict[str, Any]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Check if ANY interaction term has p < 0.05 AND |coefficient| > 0.01 eV.

    Returns:
        Tuple of (is_significant, list_of_significant_terms)
    """
    coefficients = regression_results.get("coefficients", {})
    p_values = regression_results.get("p_values", {})

    significant_terms = []

    for term, coef in coefficients.items():
        # Skip non-interaction terms (main effects)
        if "_" not in term or term.endswith("_0"):
            continue

        p_val = p_values.get(term, 1.0)
        abs_coef = abs(coef)

        logger.debug(f"Checking term {term}: coef={coef:.4f}, p={p_val:.4f}")

        if p_val < 0.05 and abs_coef > 0.01:
            significant_terms.append({
                "term": term,
                "coefficient": coef,
                "p_value": p_val,
                "abs_coefficient": abs_coef
            })

    is_significant = len(significant_terms) > 0

    if is_significant:
        logger.info(f"Found {len(significant_terms)} significant interaction terms")
    else:
        logger.info("No significant interaction terms found")

    return is_significant, significant_terms


def check_cv_stability(cv_results: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Check if CV R² standard deviation <= 0.05.

    Returns:
        Tuple of (is_stable, std_dev)
    """
    fold_scores = cv_results.get("fold_scores", {})
    r2_scores = [score["r2"] for score in fold_scores.values()]

    if len(r2_scores) == 0:
        raise ValidationError("No R² scores found in cross-validation results")

    std_dev = float(np.std(r2_scores))
    mean_r2 = float(np.mean(r2_scores))

    logger.info(f"CV R²: mean={mean_r2:.4f}, std_dev={std_dev:.4f}")

    is_stable = std_dev <= 0.05

    if is_stable:
        logger.info(f"CV stability check PASSED (std_dev={std_dev:.4f} <= 0.05)")
    else:
        logger.warning(f"CV stability check FAILED (std_dev={std_dev:.4f} > 0.05)")

    return is_stable, std_dev


def generate_validation_report(
    is_significant: bool,
    significant_terms: List[Dict[str, Any]],
    is_stable: bool,
    std_dev: float,
    regression_results: Dict[str, Any],
    cv_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the unified validation report.

    Logic:
    - If BOTH conditions are met: "Cooperative Effects Detected"
    - If either fails: "No Significant Cooperative Effects"
    """
    cooperative_detected = is_significant and is_stable

    status = "Cooperative Effects Detected" if cooperative_detected else "No Significant Cooperative Effects"

    report = {
        "status": status,
        "cooperative_effects_detected": cooperative_detected,
        "interaction_significance": {
            "is_significant": is_significant,
            "significant_terms": significant_terms,
            "threshold_p_value": 0.05,
            "threshold_coefficient": 0.01
        },
        "cv_stability": {
            "is_stable": is_stable,
            "std_dev": std_dev,
            "threshold_std_dev": 0.05,
            "mean_r2": float(np.mean([s["r2"] for s in cv_results.get("fold_scores", {}).values()])),
            "n_folds": len(cv_results.get("fold_scores", {}))
        },
        "regression_summary": {
            "n_features": regression_results.get("n_features"),
            "n_samples": regression_results.get("n_samples"),
            "model_r2": regression_results.get("r2"),
            "model_mse": regression_results.get("mse")
        },
        "validation_timestamp": cv_results.get("timestamp", "unknown")
    }

    return report


def run_statistical_validation() -> Dict[str, Any]:
    """
    Main orchestration function for T021c.

    1. Load regression results (T021b)
    2. Load CV results (T030)
    3. Check interaction significance
    4. Check CV stability
    5. Generate unified report
    6. Write to data/processed/statistical_validation_report.json
    """
    logger.info("Starting statistical validation for cooperative effects (T021c)")

    # Load inputs
    try:
        regression_results = load_regression_results()
        logger.info("Loaded regression results")
    except FileNotFoundError as e:
        logger.error(f"Failed to load regression results: {e}")
        raise

    try:
        cv_results = load_cv_results()
        logger.info("Loaded cross-validation results")
    except FileNotFoundError as e:
        logger.error(f"Failed to load CV results: {e}")
        raise

    # Check conditions
    is_significant, significant_terms = check_interaction_significance(regression_results)
    is_stable, std_dev = check_cv_stability(cv_results)

    # Generate report
    report = generate_validation_report(
        is_significant, significant_terms, is_stable, std_dev,
        regression_results, cv_results
    )

    # Write output
    output_path = PROCESSED_PATH / "statistical_validation_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Statistical validation report written to {output_path}")
    logger.info(f"Final status: {report['status']}")

    return report


def main():
    """Entry point for script execution."""
    try:
        run_statistical_validation()
        print("Statistical validation completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Statistical validation failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
