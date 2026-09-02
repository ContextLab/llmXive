"""
Hartung-Knapp Adjustment for Meta-Analysis.

This module implements the Hartung-Knapp-Sidik-Jonkman (HKSJ) adjustment
for confidence intervals in meta-analysis, specifically for low-power scenarios
(10 <= N < 20). It updates the meta-analysis results with adjusted confidence intervals.
"""
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import utilities from sibling modules as per API surface
from utils.config import get_project_root, ensure_directory

# Configure logger
logger = logging.getLogger(__name__)


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save a dictionary to a JSON file."""
    ensure_directory(file_path)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def load_effect_sizes_and_se(extracted_studies_path: Path) -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors from extracted studies CSV.
    Assumes columns: 'r', 'se' (or calculates se if n is present).
    """
    import csv

    effects = []
    ses = []

    if not extracted_studies_path.exists():
        logger.warning(f"Extracted studies file not found: {extracted_studies_path}")
        return effects, ses

    with open(extracted_studies_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            n_val = row.get('n')
            se_val = row.get('se')

            if r_val is None or r_val == '':
                continue

            try:
                r = float(r_val)
            except ValueError:
                continue

            # Calculate SE if not present but N is available
            # SE_r = sqrt((1 - r^2) / (n - 2))
            if se_val is None or se_val == '':
                if n_val and n_val != '':
                    try:
                        n = int(n_val)
                        if n > 2:
                            se = math.sqrt((1 - r**2) / (n - 2))
                        else:
                            continue # Cannot calculate SE for n <= 2
                    except ValueError:
                        continue
                else:
                    continue # Need SE or N to proceed
            else:
                try:
                    se = float(se_val)
                except ValueError:
                    continue

            effects.append(r)
            ses.append(se)

    return effects, ses


def calculate_hartung_knapp_adjusted_ci(
    pooled_effect: float,
    pooled_se: float,
    k: int,
    tau2: float,
    weights: List[float]
) -> Tuple[float, float]:
    """
    Calculate Hartung-Knapp adjusted confidence interval.

    The HKSJ method adjusts the standard error of the pooled effect
    and uses a t-distribution with k-1 degrees of freedom instead of
    the normal distribution.

    Formula:
    SE_HK = sqrt( (1/(k-1)) * sum( w_i * (y_i - theta_HK)^2 ) )
    CI = theta_HK +/- t_{k-1, 1-alpha/2} * SE_HK

    Args:
        pooled_effect: The pooled effect size (theta_HK)
        pooled_se: The standard error of the pooled effect from the standard model
        k: Number of studies
        tau2: Between-study heterogeneity variance
        weights: Weights used in the meta-analysis (1 / (se_i^2 + tau2))

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if k < 2:
        # Cannot compute HKSJ with fewer than 2 studies
        return (pooled_effect - 1.96 * pooled_se, pooled_effect + 1.96 * pooled_se)

    # Recalculate the standard error using the HKSJ method
    # We need the individual study effects to compute the residual sum of squares
    # However, we only have pooled_effect, pooled_se, tau2, and weights here.
    # We need to re-derive the individual effects or pass them in.
    # To keep this function pure, we will assume we are passed the weighted residuals
    # or we recalculate the variance of the weighted mean.

    # Standard approach for HKSJ requires the individual effects y_i.
    # Since this function signature doesn't have y_i, we will assume the caller
    # provides the necessary components or we calculate the "variance of the weighted mean"
    # based on the provided pooled_se and weights if possible, but strictly HKSJ
    # requires the sum of squared residuals.

    # Let's adjust the function to be more robust:
    # We will assume 'pooled_se' here is the standard DerSimonian-Laird SE.
    # The HK adjustment scales this SE by a factor derived from the heterogeneity.
    # However, the exact formula is:
    # var_HK(theta) = (1 / (k-1)) * sum( w_i * (y_i - theta)^2 )

    # Since we don't have y_i here, we cannot calculate the exact HK SE from scratch
    # without re-running the model logic.
    # Instead, we will implement the logic in the main runner which has access to the data.
    # This function will serve as the mathematical core if we had the residuals.
    # For now, we will return a placeholder that signals the need for data.
    
    # Re-implementation strategy:
    # The caller (run_hartung_knapp_adjustment) will have the effects and ses.
    # It will compute the HK SE there. This function is kept for API consistency
    # but the heavy lifting is in the runner.
    
    # Fallback to standard CI if we can't compute HK (missing data)
    # This path should ideally not be taken if the caller does it right.
    logger.warning("Missing individual study data for exact HK calculation. Returning standard CI.")
    return (pooled_effect - 1.96 * pooled_se, pooled_effect + 1.96 * pooled_se)


def run_hartung_knapp_adjustment(
    meta_results_path: Path,
    extracted_studies_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run the Hartung-Knapp adjustment on the meta-analysis results.

    1. Load meta-analysis results (pooled effect, SE, tau2, k).
    2. Check if 10 <= N < 20.
    3. If so, recalculate CI using HK method.
    4. Update the results dictionary with 'hk_adjusted_ci'.
    5. Save the updated results.

    Returns:
        The updated results dictionary.
    """
    if not meta_results_path.exists():
        logger.error(f"Meta results file not found: {meta_results_path}")
        return {}

    results = load_json(meta_results_path)
    
    # Check study count
    k = results.get('k', 0)
    n = results.get('N', 0) # Total studies

    # The task description says: "Adjust CI for low‑power meta‑analysis (10 ≤ N < 20)"
    # N is the total number of studies.
    if not (10 <= n < 20):
        logger.info(f"Hartung-Knapp adjustment not required. N={n} is not in [10, 20).")
        # Still save the file to indicate we checked, but no HK CI
        results['hk_adjustment_applied'] = False
        results['hk_adjusted_ci'] = None
        save_json(results, output_path)
        return results

    logger.info(f"Applying Hartung-Knapp adjustment for N={n}.")

    # Load individual study data to compute HK SE
    effects, ses = load_effect_sizes_and_se(extracted_studies_path)
    
    if len(effects) < 2:
        logger.warning("Not enough studies to compute HK adjustment.")
        results['hk_adjustment_applied'] = False
        results['hk_adjusted_ci'] = None
        save_json(results, output_path)
        return results

    # Extract parameters from meta results
    pooled_effect = results.get('pooled_effect')
    pooled_se = results.get('pooled_se')
    tau2 = results.get('tau2', 0)

    if pooled_effect is None or pooled_se is None:
        logger.error("Pooled effect or SE missing in meta results.")
        results['hk_adjustment_applied'] = False
        results['hk_adjusted_ci'] = None
        save_json(results, output_path)
        return results

    # Calculate weights: w_i = 1 / (se_i^2 + tau2)
    weights = [1.0 / (se**2 + tau2) for se in ses]
    
    # Recalculate pooled effect using weights (should match meta result, but for HK we use the weighted mean)
    # theta_HK = sum(w_i * y_i) / sum(w_i)
    sum_w = sum(weights)
    theta_hk = sum(w * y for w, y in zip(weights, effects)) / sum_w

    # Calculate HK Standard Error
    # var_HK = (1 / (k-1)) * sum( w_i * (y_i - theta_HK)^2 )
    # Note: k here is the number of studies used in the calculation (len(effects))
    k_eff = len(effects)
    if k_eff < 2:
       var_hk = 0
    else:
       sum_sq_resid = sum(w * (y - theta_hk)**2 for w, y in zip(weights, effects))
       var_hk = sum_sq_resid / (k_eff - 1)
    
    se_hk = math.sqrt(var_hk)

    # Critical value from t-distribution with k-1 degrees of freedom
    # 95% CI -> alpha = 0.05 -> two-tailed
    df = k_eff - 1
    t_crit = stats.t.ppf(0.975, df)

    # Calculate adjusted CI
    lower = theta_hk - t_crit * se_hk
    upper = theta_hk + t_crit * se_hk

    results['hk_adjustment_applied'] = True
    results['hk_adjusted_ci'] = {
        'lower': round(lower, 4),
        'upper': round(upper, 4)
    }
    results['hk_se'] = round(se_hk, 4)
    results['hk_t_crit'] = round(t_crit, 4)

    save_json(results, output_path)
    logger.info(f"Hartung-Knapp CI calculated: [{lower:.4f}, {upper:.4f}]")

    return results


def main() -> int:
    """Main entry point for the Hartung-Knapp adjustment script."""
    project_root = get_project_root()
    
    # Define paths
    meta_results_path = project_root / "data" / "derived" / "meta_results.json"
    extracted_studies_path = project_root / "data" / "processed" / "extracted_studies.csv"
    output_path = project_root / "data" / "derived" / "results.json"

    # Ensure output directory exists
    ensure_directory(output_path)

    try:
        run_hartung_knapp_adjustment(
            meta_results_path,
            extracted_studies_path,
            output_path
        )
        return 0
    except Exception as e:
        logger.exception(f"Error running Hartung-Knapp adjustment: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())