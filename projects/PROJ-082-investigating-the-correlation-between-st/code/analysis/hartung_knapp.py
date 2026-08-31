"""
Hartung-Knapp Adjustment for Meta-Analysis Confidence Intervals.

This module implements the Hartung-Knapp-Sidik-Jonkman (HKSJ) adjustment
for low-power meta-analyses (10 <= N < 20). It adjusts the standard error
of the pooled effect size to account for uncertainty in the between-study
variance estimate, providing more accurate coverage probabilities.

The adjustment replaces the standard normal quantile (z) with the t-distribution
quantile (t) with k-1 degrees of freedom, and scales the standard error of the
pooled effect by a factor derived from the observed heterogeneity.
"""

import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import existing utilities from the project API surface
# We assume these are available in utils.config and utils.logger
try:
    from utils.config import get_project_root, ensure_directory
    from utils.logger import get_logger
except ImportError:
    # Fallback if imports fail (should not happen in a correctly set up project)
    def get_project_root() -> Path:
        return Path(__file__).parent.parent.parent

    def ensure_directory(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    ensure_directory(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_effect_sizes_and_se(input_path: Path) -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors (se) from the extracted studies CSV.

    Args:
        input_path: Path to the extracted_studies.csv file.

    Returns:
        Tuple of (list of effect sizes, list of standard errors).
    """
    import csv

    effects = []
    ses = []

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return effects, ses

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            se_val = row.get('se')

            # Skip rows with missing data
            if r_val is None or se_val is None:
                continue

            try:
                r_float = float(r_val)
                se_float = float(se_val)
                effects.append(r_float)
                ses.append(se_float)
            except ValueError:
                logger.warning(f"Skipping row with invalid r/se: {row}")

    return effects, ses

def calculate_hartung_knapp_adjusted_ci(
    pooled_effect: float,
    pooled_se: float,
    effects: List[float],
    ses: List[float],
    tau_squared: float,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate the Hartung-Knapp adjusted confidence interval.

    The HKSJ method adjusts the standard error of the pooled effect by a factor
    that accounts for the uncertainty in the between-study variance estimate.
    It also uses the t-distribution with k-1 degrees of freedom instead of
    the standard normal distribution.

    Formula:
    SE_HK = SE_pooled * sqrt( (1/(k-1)) * sum( (effect_i - pooled_effect)^2 / (se_i^2 + tau^2) ) )
    CI = pooled_effect +/- t_{k-1, 1-alpha/2} * SE_HK

    Args:
        pooled_effect: The pooled effect size (e.g., from DerSimonian-Laird).
        pooled_se: The standard error of the pooled effect.
        effects: List of individual study effect sizes.
        ses: List of individual study standard errors.
        tau_squared: The estimated between-study variance.
        alpha: Significance level (default 0.05 for 95% CI).

    Returns:
        Tuple of (lower_bound, upper_bound) for the adjusted CI.
    """
    k = len(effects)

    if k < 2:
        logger.warning("Cannot calculate Hartung-Knapp CI with fewer than 2 studies.")
        return (pooled_effect - 1.96 * pooled_se, pooled_effect + 1.96 * pooled_se)

    # Calculate the scaling factor
    # Q_HK = sum( (effect_i - pooled_effect)^2 / (se_i^2 + tau^2) )
    numerator_sum = 0.0
    for i in range(k):
        diff = effects[i] - pooled_effect
        variance_i = ses[i]**2 + tau_squared
        numerator_sum += (diff ** 2) / variance_i

    # Scaling factor: sqrt( Q_HK / (k-1) )
    scaling_factor = math.sqrt(numerator_sum / (k - 1))

    # Adjusted standard error
    se_hk = pooled_se * scaling_factor

    # Use t-distribution with k-1 degrees of freedom
    t_crit = stats.t.ppf(1 - alpha / 2, df=k - 1)

    lower_bound = pooled_effect - t_crit * se_hk
    upper_bound = pooled_effect + t_crit * se_hk

    logger.info(
        f"Hartung-Knapp Adjustment: k={k}, "
        f"scaling_factor={scaling_factor:.4f}, "
        f"SE_HK={se_hk:.4f}, "
        f"t_crit({k-1})={t_crit:.4f}"
    )

    return (lower_bound, upper_bound)

def run_hartung_knapp_adjustment(
    input_path: Optional[Path] = None,
    results_path: Optional[Path] = None,
    n_studies: int = 15  # Default for testing if not provided
) -> Dict[str, Any]:
    """
    Run the Hartung-Knapp adjustment on a meta-analysis result.

    This function:
    1. Loads the meta-analysis results (pooled effect, SE, tau^2).
    2. Loads the individual study effect sizes and SEs.
    3. Checks if 10 <= N < 20 (low-power range).
    4. If in range, calculates the adjusted CI and updates the results.
    5. Writes the updated results to the output file.

    Args:
        input_path: Path to the extracted_studies.csv file.
        results_path: Path to the results.json file.
        n_studies: Number of studies (for testing/override).

    Returns:
        Dictionary containing the adjustment results.
    """
    project_root = get_project_root()

    # Default paths if not provided
    if input_path is None:
        input_path = project_root / "data" / "processed" / "extracted_studies.csv"
    if results_path is None:
        results_path = project_root / "data" / "derived" / "results.json"

    # Load results
    if not results_path.exists():
        logger.error(f"Results file not found: {results_path}")
        return {"status": "error", "message": "Results file not found"}

    results = load_json(results_path)

    # Check if meta-analysis was completed
    if results.get("status") != "completed":
        logger.info("Meta-analysis not completed, skipping Hartung-Knapp adjustment.")
        return {"status": "skipped", "reason": "Meta-analysis not completed"}

    # Get number of studies
    n = results.get("N", n_studies)

    # Only apply for low-power range: 10 <= N < 20
    if not (10 <= n < 20):
        logger.info(
            f"N={n} is not in low-power range (10 <= N < 20). "
            "Skipping Hartung-Knapp adjustment."
        )
        results["hk_adjusted_ci"] = None
        results["hk_adjustment_applied"] = False
        save_json(results_path, results)
        return {
            "status": "skipped",
            "reason": f"N={n} not in range [10, 20)",
            "hk_adjustment_applied": False
        }

    logger.info(f"N={n} is in low-power range. Applying Hartung-Knapp adjustment.")

    # Load effect sizes and SEs
    effects, ses = load_effect_sizes_and_se(input_path)

    if len(effects) < 2:
        logger.error("Insufficient studies for Hartung-Knapp adjustment.")
        return {"status": "error", "message": "Insufficient studies"}

    # Get pooled effect and SE from results
    pooled_effect = results.get("pooled_effect")
    pooled_se = results.get("pooled_se")
    tau_squared = results.get("tau_squared", 0.0)

    if pooled_effect is None or pooled_se is None:
        logger.error("Missing pooled_effect or pooled_se in results.")
        return {"status": "error", "message": "Missing pooled statistics"}

    # Calculate adjusted CI
    lower, upper = calculate_hartung_knapp_adjusted_ci(
        pooled_effect=pooled_effect,
        pooled_se=pooled_se,
        effects=effects,
        ses=ses,
        tau_squared=tau_squared
    )

    # Update results
    results["hk_adjusted_ci"] = {
        "lower": round(lower, 4),
        "upper": round(upper, 4),
        "level": "95%"
    }
    results["hk_adjustment_applied"] = True
    results["hk_degrees_of_freedom"] = len(effects) - 1

    # Save updated results
    save_json(results_path, results)

    logger.info(
        f"Hartung-Knapp adjustment complete. "
        f"Adjusted CI: [{lower:.4f}, {upper:.4f}]"
    )

    return {
        "status": "completed",
        "hk_adjusted_ci": results["hk_adjusted_ci"],
        "hk_adjustment_applied": True
    }

def main() -> int:
    """Main entry point for the Hartung-Knapp adjustment script."""
    logger.info("Starting Hartung-Knapp Adjustment...")

    try:
        result = run_hartung_knapp_adjustment()

        if result["status"] == "completed":
            logger.info("Hartung-Knapp adjustment successful.")
            return 0
        elif result["status"] == "skipped":
            logger.info(f"Hartung-Knapp adjustment skipped: {result.get('reason', 'N/A')}")
            return 0
        else:
            logger.error(f"Hartung-Knapp adjustment failed: {result.get('message', 'Unknown error')}")
            return 1

    except Exception as e:
        logger.exception(f"Unexpected error during Hartung-Knapp adjustment: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())