"""
ANOVA testing and multiple-comparison correction module.

Implements:
- One-way ANOVA F-tests for comparing means across topology groups.
- Multiple-comparison correction (Bonferroni and Benjamini-Hochberg).
- Application of corrections to both ANOVA F-test p-values and regression coefficients.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from code.src.analysis.regression import RegressionResult

logger = logging.getLogger(__name__)


class ANOVAError(Exception):
    """Custom exception for ANOVA-related errors."""
    pass


def run_one_way_anova(
    groups: Dict[str, Union[List[float], np.ndarray]],
    factor_name: str = "topology_class",
    response_name: str = "diffusion_rate"
) -> Dict[str, Any]:
    """
    Perform a one-way ANOVA F-test to compare means across groups.

    Args:
        groups: Dictionary mapping group names (e.g., topology classes) to arrays of values.
        factor_name: Name of the grouping factor (for metadata).
        response_name: Name of the response variable (for metadata).

    Returns:
        Dictionary containing:
            - 'f_statistic': float
            - 'p_value': float
            - 'df_between': int
            - 'df_within': int
            - 'factor_name': str
            - 'response_name': str
            - 'group_counts': Dict[str, int]
    """
    if not groups:
        raise ANOVAError("Groups dictionary cannot be empty.")

    group_names = list(groups.keys())
    group_data = [np.array(groups[name]) for name in group_names]

    if any(len(g) == 0 for g in group_data):
        raise ANOVAError("One or more groups have zero samples.")

    # scipy.stats.f_oneway expects separate arrays for each group
    f_stat, p_val = stats.f_oneway(*group_data)

    # Degrees of freedom
    k = len(group_data)  # number of groups
    n = sum(len(g) for g in group_data)  # total samples
    df_between = k - 1
    df_within = n - k

    result = {
        "f_statistic": float(f_stat),
        "p_value": float(p_val),
        "df_between": int(df_between),
        "df_within": int(df_within),
        "factor_name": factor_name,
        "response_name": response_name,
        "group_counts": {name: int(len(g)) for name, g in zip(group_names, group_data)}
    }

    logger.info(f"ANOVA F-test: F={f_stat:.4f}, p={p_val:.4e} for {factor_name} vs {response_name}")
    return result


def apply_multiple_comparison_correction(
    p_values: List[float],
    method: str = "bonferroni",
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply multiple-comparison correction to a list of p-values.

    Supported methods:
        - 'bonferroni': Bonferroni correction (family-wise error rate control)
        - 'benjamini_hochberg': Benjamini-Hochberg procedure (FDR control)

    Args:
        p_values: List of raw p-values.
        method: Correction method ('bonferroni' or 'benjamini_hochberg').
        alpha: Significance level threshold.

    Returns:
        Dictionary containing:
            - 'raw_p_values': List[float]
            - 'corrected_p_values': List[float]
            - 'is_significant': List[bool]
            - 'method': str
            - 'alpha': float
    """
    if not p_values:
        raise ANOVAError("Cannot apply correction to empty p-value list.")

    if method == "bonferroni":
        # statsmodels multipletests with method='bonferroni'
        corrected, rejected, _, _ = multipletests(p_values, alpha=alpha, method='bonferroni')
    elif method == "benjamini_hochberg" or method == "fdr_bh":
        corrected, rejected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    else:
        raise ANOVAError(f"Unsupported correction method: {method}. Use 'bonferroni' or 'benjamini_hochberg'.")

    result = {
        "raw_p_values": [float(p) for p in p_values],
        "corrected_p_values": [float(p) for p in corrected],
        "is_significant": [bool(r) for r in rejected],
        "method": method,
        "alpha": alpha
    }

    logger.info(f"Applied {method} correction: {sum(rejected)} of {len(p_values)} tests significant at alpha={alpha}")
    return result


def correct_regression_pvalues(
    regression_results: List[RegressionResult],
    method: str = "bonferroni",
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Apply multiple-comparison correction to p-values from a list of regression results.

    This ensures correction is applied to regression coefficients as required by the task.

    Args:
        regression_results: List of RegressionResult objects.
        method: Correction method ('bonferroni' or 'benjamini_hochberg').
        alpha: Significance level threshold.

    Returns:
        List of dictionaries, each containing the original regression data plus:
            - 'corrected_p_values': List[float]
            - 'is_significant': List[bool]
            - 'correction_method': str
    """
    if not regression_results:
        return []

    # Extract p-values for each coefficient
    # Assuming regression_results.p_values is a list of p-values for coefficients
    all_p_values = []
    result_map = []

    for res in regression_results:
        # Handle case where p_values might be None or empty
        if res.p_values:
            all_p_values.extend(res.p_values)
        else:
            # If no p-values, append None placeholders to maintain alignment
            # This shouldn't happen in valid RegressionResult, but handle gracefully
            logger.warning("RegressionResult has no p_values; skipping correction for this result.")
            result_map.append({
                "original": res,
                "corrected_p_values": [],
                "is_significant": [],
                "correction_method": method
            })
            continue

    if not all_p_values:
        return result_map

    # Apply correction
    correction_result = apply_multiple_comparison_correction(all_p_values, method, alpha)

    # Map corrected values back to each regression result
    idx = 0
    for res in regression_results:
        if not res.p_values:
            continue
        num_coefs = len(res.p_values)
        corrected_p = correction_result["corrected_p_values"][idx:idx+num_coefs]
        is_sig = correction_result["is_significant"][idx:idx+num_coefs]
        idx += num_coefs

        result_map.append({
            "original": res,
            "corrected_p_values": corrected_p,
            "is_significant": is_sig,
            "correction_method": method
        })

    return result_map


def run_anova_on_diffusion_by_topology(
    simulation_results: pd.DataFrame,
    topology_column: str = "topology_class",
    diffusion_column: str = "diffusion_rate",
    correction_method: str = "bonferroni",
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run a full ANOVA pipeline:
    1. Group data by topology class.
    2. Run one-way ANOVA.
    3. If significant, perform post-hoc pairwise comparisons (t-tests) and correct p-values.

    Args:
        simulation_results: DataFrame with columns including topology_class and diffusion_rate.
        topology_column: Name of the topology class column.
        diffusion_column: Name of the diffusion rate column.
        correction_method: Method for multiple-comparison correction.
        alpha: Significance threshold.

    Returns:
        Dictionary containing:
            - 'anova_result': Dict from run_one_way_anova
            - 'post_hoc_result': Dict from apply_multiple_comparison_correction (if applicable)
            - 'pairwise_comparisons': List of pairwise test results (optional)
    """
    if topology_column not in simulation_results.columns or diffusion_column not in simulation_results.columns:
        raise ANOVAError(f"DataFrame must contain columns '{topology_column}' and '{diffusion_column}'.")

    # Group by topology
    groups = {}
    for name, group in simulation_results.groupby(topology_column):
        groups[name] = group[diffusion_column].values

    # Run ANOVA
    anova_res = run_one_way_anova(groups, factor_name=topology_column, response_name=diffusion_column)

    post_hoc = None
    pairwise_results = []

    # If ANOVA is significant, run post-hoc pairwise t-tests
    if anova_res["p_value"] < alpha:
        logger.info("ANOVA significant. Running post-hoc pairwise t-tests with correction.")
        group_names = list(groups.keys())
        p_vals = []
        comparisons = []

        for i in range(len(group_names)):
            for j in range(i + 1, len(group_names)):
                g1 = groups[group_names[i]]
                g2 = groups[group_names[j]]
                # Two-sample t-test
                _, p_val = stats.ttest_ind(g1, g2, equal_var=False)  # Welch's t-test
                p_vals.append(p_val)
                comparisons.append((group_names[i], group_names[j]))

        if p_vals:
            corr_res = apply_multiple_comparison_correction(p_vals, method=correction_method, alpha=alpha)
            post_hoc = corr_res

            # Attach significance to comparisons
            for idx, (g1, g2) in enumerate(comparisons):
                pairwise_results.append({
                    "group1": g1,
                    "group2": g2,
                    "raw_p_value": p_vals[idx],
                    "corrected_p_value": corr_res["corrected_p_values"][idx],
                    "is_significant": corr_res["is_significant"][idx]
                })

    return {
        "anova_result": anova_res,
        "post_hoc_result": post_hoc,
        "pairwise_comparisons": pairwise_results
    }
