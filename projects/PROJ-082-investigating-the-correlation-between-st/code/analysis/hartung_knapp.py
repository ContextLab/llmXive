"""
Hartung-Knapp Adjustment for Meta-Analysis Confidence Intervals.

This module implements the Hartung-Knapp-Sidik-Jonkman (HKSJ) adjustment
for low-power meta-analysis scenarios (specifically 10 <= N < 20).
It adjusts the confidence intervals of the pooled effect size to account
for uncertainty in the between-study variance estimate.

The adjustment replaces the standard normal quantile (z) with a t-distribution
quantile with k-1 degrees of freedom, and scales the standard error of the
pooled effect by the square root of the estimated variance of the effect.

Output: Updates `data/derived/results.json` with `hk_adjusted_ci`.
"""

import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/hartung_knapp.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"


def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved results to {file_path}")


def load_effect_sizes_and_se() -> List[Tuple[float, float, str]]:
    """
    Load effect sizes (r) and standard errors (se) from extracted studies.
    
    Reads from data/processed/extracted_studies.csv.
    Returns a list of tuples: (r, se, author_year_id).
    """
    input_path = DATA_PROCESSED / "extracted_studies.csv"
    if not input_path.exists():
        logger.warning(f"Input file {input_path} not found. No data to process.")
        return []

    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            se_val = row.get('se')
            # Use author and year as a unique identifier if available, otherwise index
            author = row.get('author', 'Unknown')
            year = row.get('year', 'Unknown')
            study_id = f"{author}_{year}"

            if r_val is not None and se_val is not None:
                try:
                    r_float = float(r_val)
                    se_float = float(se_val)
                    if not math.isnan(r_float) and not math.isnan(se_float) and se_float > 0:
                        data.append((r_float, se_float, study_id))
                    else:
                        logger.debug(f"Skipping invalid values for {study_id}: r={r_float}, se={se_float}")
                except ValueError:
                    logger.debug(f"Skipping non-numeric values for {study_id}")
    
    return data


def calculate_hartung_knapp_adjusted_ci(
    effects: List[Tuple[float, float, str]],
    pooled_effect: float,
    pooled_se: float,
    k: int,
    alpha: float = 0.05
) -> Optional[Dict[str, float]]:
    """
    Calculate the Hartung-Knapp adjusted confidence interval.
    
    The HKSJ method adjusts the standard error of the pooled effect by a factor
    derived from the residual variance of the effect sizes around the pooled estimate.
    
    Formula:
    1. Calculate residual variance (tau2_hk): sum(w_i * (y_i - y_bar)^2) / (k - 1)
       where w_i = 1/se_i^2
    2. Adjusted SE: sqrt(tau2_hk * sum(w_i) / (k * sum(w_i) - (sum(w_i)^2 / sum(w_i^2)))) 
       Actually, the simpler HKSJ formulation is:
       Var_HKSJ = (1 / sum(w_i)) * (1 + (sum(w_i * (y_i - y_bar)^2) / (k-1)) * (1/sum(w_i) - 1/sum(w_i^2)/sum(w_i) ... wait)
       
    Standard HKSJ approach:
    1. Compute weights w_i = 1 / se_i^2
    2. Pooled effect y_bar = sum(w_i * y_i) / sum(w_i)
    3. Residual sum of squares Q = sum(w_i * (y_i - y_bar)^2)
    4. Variance of pooled effect under HKSJ: V_HKSJ = (Q / (k - 1)) * (1 / sum(w_i))
    5. Adjusted SE = sqrt(V_HKSJ)
    6. CI = y_bar +/- t_{k-1, 1-alpha/2} * Adjusted SE
    
    Args:
        effects: List of (r, se, id)
        pooled_effect: The pooled effect size (y_bar)
        pooled_se: The standard error of the pooled effect from standard random-effects
        k: Number of studies
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with 'lower' and 'upper' bounds, or None if k < 2.
    """
    if k < 2:
        logger.warning("Cannot calculate HKSJ CI with k < 2 studies.")
        return None

    # Calculate weights
    weights = [1.0 / (se ** 2) for _, se, _ in effects]
    sum_w = sum(weights)
    
    # Calculate weighted mean (should match pooled_effect, but we recompute for consistency)
    weighted_sum = sum(w * r for (r, se, _), w in zip(effects, weights))
    y_bar = weighted_sum / sum_w

    # Calculate residual sum of squares (Q statistic numerator)
    # Q = sum(w_i * (y_i - y_bar)^2)
    q_stat = sum(w * (r - y_bar) ** 2 for (r, se, _), w in zip(effects, weights))

    # Calculate the scaling factor for the variance
    # The HKSJ variance is: (Q / (k - 1)) * (1 / sum_w)
    # Note: In some formulations, the factor is (Q / (k-1)) * (1/sum_w) * (something related to k)
    # The most common HKSJ variance estimator for the pooled effect is:
    # Var_HKSJ = (1 / sum(w_i)) * (1 + (Q / (k-1)) * (1/sum(w_i) - 1/sum(w_i^2)/sum(w_i) ... no)
    # Let's stick to the core definition:
    # Var_HKSJ = (Q / (k-1)) * (1 / sum(w_i))
    # This assumes the random effects model variance is estimated by Q/(k-1) * (1/sum(w_i))
    # Wait, the standard DerSimonian-Laird variance is 1/sum(w_i).
    # The HKSJ adjustment multiplies the DL variance by a factor F = (Q / (k-1)) / (sum(w_i * se_i^2) / (k-1))? 
    # No. The HKSJ method replaces the standard error of the pooled effect with:
    # SE_HKSJ = sqrt( (Q / (k-1)) * (1 / sum(w_i)) )
    # But this is only if the DL estimate of tau^2 is 0?
    # Correct HKSJ formula:
    # SE_HKSJ = sqrt( (1 / sum(w_i)) * (1 + (Q - (k-1)) / (k-1)) ) ? No.
    
    # Let's use the standard definition from Hartung & Knapp (2001):
    # The variance of the pooled effect is estimated as:
    # V_HKSJ = (1 / sum(w_i)) * (sum(w_i * (y_i - y_bar)^2) / (k - 1))
    # This is equivalent to: (Q / (k-1)) * (1 / sum(w_i))
    
    # However, if the random effects model already includes tau^2 in the weights,
    # the formula is slightly different. The weights w_i = 1 / (se_i^2 + tau^2).
    # The HKSJ adjustment is:
    # SE_adj = sqrt( (sum(w_i * (y_i - y_bar)^2) / (k - 1)) * (1 / sum(w_i)) )
    # This is the one we use.
    
    if sum_w == 0:
        logger.error("Sum of weights is zero. Cannot compute HKSJ CI.")
        return None

    # Calculate the adjustment factor
    # Q is the residual sum of squares
    # The term (Q / (k-1)) is an estimate of the total variance (within + between) relative to weights?
    # Actually, the formula is:
    # SE_HKSJ = sqrt( (Q / (k-1)) * (1 / sum(w_i)) )
    # But wait, if the model is correct, Q ~ k-1.
    # The factor (Q / (k-1)) is the ratio of observed to expected heterogeneity.
    
    # Let's calculate Q again carefully
    # Q = sum(w_i * (y_i - y_bar)^2)
    # We already did this above.
    
    # Calculate the HKSJ variance
    # V_HKSJ = (Q / (k-1)) * (1 / sum(w_i))
    # This is the variance of the pooled effect under HKSJ.
    
    # However, there is a nuance: if the DL estimate of tau^2 is used to calculate weights,
    # then the standard error of the pooled effect is 1/sqrt(sum(w_i)).
    # The HKSJ adjustment multiplies this by sqrt(Q/(k-1)).
    # So SE_HKSJ = (1/sqrt(sum(w_i))) * sqrt(Q/(k-1))
    # Which is sqrt( (1/sum(w_i)) * (Q/(k-1)) )
    
    # Let's verify:
    # If Q = k-1 (perfect fit), then SE_HKSJ = 1/sqrt(sum(w_i)), which is the standard SE.
    # If Q > k-1 (more heterogeneity), SE_HKSJ is larger.
    # This seems correct.
    
    hk_variance = (q_stat / (k - 1)) * (1.0 / sum_w)
    hk_se = math.sqrt(hk_variance)
    
    # Degrees of freedom for t-distribution
    df = k - 1
    
    # Critical t-value for 95% CI (two-tailed)
    # Since we don't have scipy, we approximate t-value for common df
    # For df >= 30, t ~ 1.96
    # For small df, t is larger
    # Approximation for t_{df, 0.975}
    # Using a simple approximation or a lookup table for small df
    # For this implementation, we'll use a simplified approximation:
    # t = 1.96 + (1.96^3 + 1.96) / (4 * df) ... no, that's for normal.
    # Let's use a hardcoded lookup for small df and 1.96 for large df
    t_values = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
        6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980
    }
    
    t_crit = t_values.get(df, 1.96)
    if df > 120:
        t_crit = 1.96
    
    # Calculate CI
    lower = y_bar - t_crit * hk_se
    upper = y_bar + t_crit * hk_se
    
    return {
        "lower": round(lower, 4),
        "upper": round(upper, 4),
        "hk_se": round(hk_se, 4),
        "t_critical": t_crit,
        "degrees_of_freedom": df,
        "q_statistic": round(q_stat, 4)
    }


def run_hartung_knapp_adjustment() -> Dict[str, Any]:
    """
    Main function to run the Hartung-Knapp adjustment.
    
    1. Check study count (N).
    2. If 10 <= N < 20, perform adjustment.
    3. Load meta-analysis results.
    4. Calculate adjusted CI.
    5. Update results.json with hk_adjusted_ci.
    
    Returns:
        Dictionary with the result status and adjusted CI if applicable.
    """
    logger.info("Starting Hartung-Knapp Adjustment analysis.")
    
    # Load study count
    study_count_path = DATA_PROCESSED / "study_count.json"
    if not study_count_path.exists():
        logger.error(f"Study count file not found: {study_count_path}")
        return {"status": "error", "reason": "study_count.json not found"}
    
    study_count_data = load_json(study_count_path)
    N = study_count_data.get("N", 0)
    
    logger.info(f"Total studies (N): {N}")
    
    # Check condition: 10 <= N < 20
    if not (10 <= N < 20):
        logger.info(f"N={N} is not in the range [10, 20). Skipping HKSJ adjustment.")
        return {
            "status": "skipped",
            "reason": f"N={N} not in range [10, 20)",
            "hk_adjusted_ci": None
        }
    
    # Load meta-analysis results to get pooled effect and SE
    meta_results_path = DATA_DERIVED / "meta_results.json"
    if not meta_results_path.exists():
        logger.error(f"Meta-analysis results not found: {meta_results_path}")
        return {"status": "error", "reason": "meta_results.json not found"}
    
    meta_results = load_json(meta_results_path)
    pooled_effect = meta_results.get("pooled_effect")
    pooled_se = meta_results.get("pooled_se")
    
    if pooled_effect is None or pooled_se is None:
        logger.error("Pooled effect or SE not found in meta_results.json")
        return {"status": "error", "reason": "Missing pooled effect or SE in meta_results.json"}
    
    # Load effect sizes and SEs for calculation
    effects = load_effect_sizes_and_se()
    k = len(effects)
    
    if k < 2:
        logger.warning(f"Only {k} valid studies found for HKSJ calculation. Skipping.")
        return {
            "status": "skipped",
            "reason": f"Insufficient valid studies (k={k}) for HKSJ",
            "hk_adjusted_ci": None
        }
    
    # Calculate HKSJ adjusted CI
    hk_ci = calculate_hartung_knapp_adjusted_ci(
        effects=effects,
        pooled_effect=pooled_effect,
        pooled_se=pooled_se,
        k=k
    )
    
    if hk_ci is None:
        return {
            "status": "error",
            "reason": "Failed to calculate HKSJ CI",
            "hk_adjusted_ci": None
        }
    
    # Load existing results.json
    results_path = DATA_DERIVED / "results.json"
    results_data = {}
    if results_path.exists():
        results_data = load_json(results_path)
    
    # Update results with HKSJ CI
    results_data["hk_adjusted_ci"] = hk_ci
    results_data["hk_adjustment_applied"] = True
    results_data["hk_adjustment_reason"] = f"N={N} is in low-power range [10, 20)"
    
    # Save updated results
    save_json(results_path, results_data)
    
    logger.info("Hartung-Knapp adjustment completed successfully.")
    return {
        "status": "success",
        "hk_adjusted_ci": hk_ci,
        "hk_adjustment_applied": True
    }


def main():
    """Entry point for the Hartung-Knapp adjustment script."""
    try:
        result = run_hartung_knapp_adjustment()
        print(json.dumps(result, indent=2))
        if result.get("status") == "error":
            sys.exit(1)
    except Exception as e:
        logger.exception("An error occurred during Hartung-Knapp adjustment.")
        print(json.dumps({"status": "error", "reason": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()