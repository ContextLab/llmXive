"""
Sensitivity Analysis Module for Energy Systems Project.

This module implements a caliper sweep to assess the robustness of the
Average Treatment Effect on the Treated (ATT) estimates against variations
in the propensity score matching caliper.

It reuses functions from `src.analysis.psm` (matching logic) and
`src.analysis.causal` (OLS estimation) to compile results.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from src.analysis.psm import iterative_matching, estimate_propensity, match_pairs
from src.analysis.causal import run_ols, DataUnavailableError
from src.utils.logging import get_logger

logger = get_logger(__name__)


def sweep_caliper(
    df: pd.DataFrame,
    calipers: List[float],
    outcome_col: str = "log_energy_cost",
    treatment_col: str = "treatment",
    covariates: Optional[List[str]] = None,
    min_adopters: int = 50
) -> Dict[str, Any]:
    """
    Perform a sensitivity analysis by sweeping caliper values.

    This function iterates over a provided list of caliper values, performing
    propensity score matching and subsequent OLS estimation for each. It
    compiles the resulting ATT estimates, p-values, confidence intervals,
    and sample sizes.

    Args:
        df: Preprocessed DataFrame containing treatment, outcome, and covariates.
        calipers: List of caliper values to test (e.g., [0.01, 0.02, 0.05, 0.1]).
        outcome_col: Name of the outcome variable column (default: "log_energy_cost").
        treatment_col: Name of the binary treatment column (default: "treatment").
        covariates: List of covariate column names for matching. If None, defaults
                    to a standard set if not inferred, but explicit passing is preferred.
        min_adopters: Minimum number of treated units required to proceed.

    Returns:
        A dictionary containing:
            - 'sweep_results': List of dicts with 'caliper', 'att', 'p_value',
                              'ci_lower', 'ci_upper', 'n_matched', 'status'.
            - 'summary': Dict with mean ATT, std dev of ATT across calipers.
            - 'best_caliper': The caliper value yielding the most stable estimate
                             (lowest variance in a sliding window or highest N with
                             acceptable balance - simplified here to highest N).
    """
    if covariates is None:
        # Default covariates if not specified, though task implies they are passed
        # or inferred from previous steps. We raise if missing to avoid guessing.
        raise ValueError("covariates must be provided for sensitivity analysis.")

    logger.info(f"Starting caliper sweep with {len(calipers)} values.")
    
    results = []
    best_result = None
    max_n_matched = 0

    for caliper in calipers:
        logger.info(f"Processing caliper: {caliper}")
        try:
            # Step 1: Estimate propensity scores
            # We assume estimate_propensity returns df with 'propensity_score' column
            # or modifies df in place. Based on API surface, it returns a DataFrame.
            df_scored = estimate_propensity(df, covariates=covariates)
            
            if 'propensity_score' not in df_scored.columns:
                logger.warning(f"Propensity score column missing after estimation for caliper {caliper}. Skipping.")
                results.append({
                    "caliper": caliper,
                    "att": None,
                    "p_value": None,
                    "ci_lower": None,
                    "ci_upper": None,
                    "n_matched": 0,
                    "status": "error_propensity"
                })
                continue

            # Step 2: Perform Matching
            # match_pairs returns the matched DataFrame
            df_matched = match_pairs(
                df_scored, 
                caliper=caliper, 
                treatment_col=treatment_col
            )

            n_treated = df_matched[df_matched[treatment_col] == 1].shape[0]
            
            if n_treated < min_adopters:
                logger.warning(f"Caliper {caliper}: Only {n_treated} adopters remain (< {min_adopters}). Skipping estimation.")
                results.append({
                    "caliper": caliper,
                    "att": None,
                    "p_value": None,
                    "ci_lower": None,
                    "ci_upper": None,
                    "n_matched": n_treated,
                    "status": "insufficient_power"
                })
                continue

            # Step 3: Estimate Causal Effect (OLS)
            # run_ols expects df with treatment, outcome, and optionally cluster info
            try:
                ols_result = run_ols(
                    df_matched,
                    outcome_col=outcome_col,
                    treatment_col=treatment_col,
                    covariates=covariates
                )
                
                att = ols_result.params[treatment_col]
                p_val = ols_result.pvalues[treatment_col]
                
                # 95% CI
                conf_int = ols_result.conf_int(alpha=0.05)
                ci_lower = conf_int.loc[treatment_col, 0]
                ci_upper = conf_int.loc[treatment_col, 1]

                results.append({
                    "caliper": caliper,
                    "att": float(att),
                    "p_value": float(p_val),
                    "ci_lower": float(ci_lower),
                    "ci_upper": float(ci_upper),
                    "n_matched": int(n_treated),
                    "status": "success"
                })

                # Track best by max matched sample size (simple heuristic)
                if n_treated > max_n_matched:
                    max_n_matched = n_treated
                    best_result = results[-1]

            except DataUnavailableError as e:
                logger.error(f"OLS failed for caliper {caliper}: {e}")
                results.append({
                    "caliper": caliper,
                    "att": None,
                    "p_value": None,
                    "ci_lower": None,
                    "ci_upper": None,
                    "n_matched": n_treated,
                    "status": "error_ols",
                    "error_msg": str(e)
                })
            except Exception as e:
                logger.error(f"Unexpected error during OLS for caliper {caliper}: {e}")
                results.append({
                    "caliper": caliper,
                    "att": None,
                    "p_value": None,
                    "ci_lower": None,
                    "ci_upper": None,
                    "n_matched": n_treated,
                    "status": "error_unknown",
                    "error_msg": str(e)
                })

        except Exception as e:
            logger.error(f"Matching failed for caliper {caliper}: {e}")
            results.append({
                "caliper": caliper,
                "att": None,
                "p_value": None,
                "ci_lower": None,
                "ci_upper": None,
                "n_matched": 0,
                "status": "error_matching",
                "error_msg": str(e)
            })

    # Compile Summary
    valid_att_values = [r["att"] for r in results if r["status"] == "success" and r["att"] is not None]
    summary = {
        "count_successful": len(valid_att_values),
        "mean_att": np.mean(valid_att_values) if valid_att_values else None,
        "std_att": np.std(valid_att_values) if valid_att_values else None,
        "range_att": (min(valid_att_values), max(valid_att_values)) if valid_att_values else None
    }

    return {
        "sweep_results": results,
        "summary": summary,
        "best_caliper": best_result["caliper"] if best_result else None,
        "best_result": best_result
    }
