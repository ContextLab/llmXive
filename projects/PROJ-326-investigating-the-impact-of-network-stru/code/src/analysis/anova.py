"""
ANOVA and multiple-comparison correction module.
Implements one-way ANOVA, Bonferroni, and Benjamini-Hochberg corrections.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)


class ANOVAError(Exception):
    """Custom exception for ANOVA-related errors."""
    pass


def run_one_way_anova(
    groups: Dict[str, List[Union[int, float]]],
    factor_name: str = "group"
) -> Dict[str, Any]:
    """
    Perform a one-way ANOVA test on multiple groups.

    Args:
        groups: Dictionary mapping group names to lists of values.
        factor_name: Name of the factor being tested.

    Returns:
        Dictionary containing F-statistic, p-value, and group statistics.
    """
    if len(groups) < 2:
        raise ANOVAError("At least two groups are required for ANOVA.")

    group_names = list(groups.keys())
    group_values = list(groups.values())

    # Check for empty groups
    for name, values in groups.items():
        if len(values) == 0:
            raise ANOVAError(f"Group '{name}' is empty. Cannot perform ANOVA.")

    # Perform ANOVA
    f_stat, p_value = stats.f_oneway(*group_values)

    # Calculate group statistics
    group_stats = {}
    for name, values in groups.items():
        values_arr = np.array(values)
        group_stats[name] = {
            "mean": float(np.mean(values_arr)),
            "std": float(np.std(values_arr)),
            "n": len(values),
        }

    return {
        "f_statistic": float(f_stat),
        "p_value": float(p_value),
        "factor_name": factor_name,
        "group_names": group_names,
        "group_stats": group_stats,
        "degrees_of_freedom": {
            "between": len(groups) - 1,
            "within": sum(len(v) for v in group_values) - len(groups),
        },
    }


def apply_multiple_comparison_correction(
    p_values: List[float],
    method: str = "fdr_bh"
) -> Dict[str, Any]:
    """
    Apply multiple-comparison correction to a list of p-values.

    Args:
        p_values: List of raw p-values.
        method: Correction method. Options: 'bonferroni', 'fdr_bh' (Benjamini-Hochberg),
                'fdr_by' (Benjamini-Yekutieli), 'sidak'.

    Returns:
        Dictionary containing corrected p-values, rejection decisions, and method info.
    """
    if not p_values:
        return {
            "corrected_p_values": [],
            "rejections": [],
            "method": method,
            "alpha": 0.05,
            "n_tests": 0,
        }

    # Map method names to statsmodels codes
    method_map = {
        "bonferroni": "bonferroni",
        "fdr_bh": "fdr_bh",
        "fdr_by": "fdr_by",
        "sidak": "sidak",
    }

    if method not in method_map:
        raise ANOVAError(f"Unknown correction method: {method}. Use {list(method_map.keys())}.")

    # Perform correction
    corrected_p_values, rejections, _, _ = multipletests(
        p_values, alpha=0.05, method=method_map[method]
    )

    method_name = {
        "bonferroni": "Bonferroni",
        "fdr_bh": "Benjamini-Hochberg",
        "fdr_by": "Benjamini-Yekutieli",
        "sidak": "Sidak",
    }[method]

    rationale = "Default for FDR control" if method == "fdr_bh" else "Family-wise error rate control"
    if method == "fdr_bh":
        rationale = "Control of False Discovery Rate (FDR) as recommended for exploratory analyses"

    return {
        "corrected_p_values": [float(p) for p in corrected_p_values],
        "rejections": list(rejections),
        "method": method_name,
        "method_code": method,
        "alpha": 0.05,
        "n_tests": len(p_values),
        "rationale": rationale,
    }


def correct_regression_pvalues(
    regression_results: List[Dict[str, Any]],
    p_value_key: str = "p_value",
    method: str = "fdr_bh"
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply multiple-comparison correction to a list of regression results.

    Args:
        regression_results: List of dictionaries containing regression results.
        p_value_key: Key name for the p-value in each result dict.
        method: Correction method ('bonferroni' or 'fdr_bh').

    Returns:
        Tuple of (updated_results, correction_metadata).
    """
    p_values = [r.get(p_value_key) for r in regression_results if p_value_key in r]

    if not p_values:
        logger.warning("No p-values found to correct.")
        return regression_results, {"method": method, "n_tests": 0}

    correction_result = apply_multiple_comparison_correction(p_values, method)

    # Update the results list with corrected p-values and rejection status
    updated_results = []
    for i, result in enumerate(regression_results):
        new_result = result.copy()
        if i < len(correction_result["corrected_p_values"]):
            new_result["p_value_corrected"] = correction_result["corrected_p_values"][i]
            new_result["is_significant_corrected"] = correction_result["rejections"][i]
        updated_results.append(new_result)

    return updated_results, correction_result


def run_anova_on_diffusion_by_topology(
    simulation_data: pd.DataFrame,
    target_column: str = "diffusion_rate",
    group_column: str = "topology_type",
    correction_method: str = "fdr_bh"
) -> Dict[str, Any]:
    """
    Run ANOVA on diffusion rates grouped by topology type and apply correction.

    Args:
        simulation_data: DataFrame containing simulation results.
        target_column: Name of the column containing the dependent variable.
        group_column: Name of the column containing the grouping variable.
        correction_method: Method for multiple-comparison correction.

    Returns:
        Dictionary containing ANOVA results and correction details.
    """
    if target_column not in simulation_data.columns:
        raise ANOVAError(f"Target column '{target_column}' not found in data.")
    if group_column not in simulation_data.columns:
        raise ANOVAError(f"Group column '{group_column}' not found in data.")

    # Group data
    groups = {}
    for name, group in simulation_data.groupby(group_column):
        values = group[target_column].dropna().tolist()
        if values:
            groups[name] = values

    if len(groups) < 2:
        raise ANOVAError("Not enough groups with data for ANOVA.")

    # Run ANOVA
    anova_result = run_one_way_anova(groups, factor_name=group_column)

    # Extract p-values for pairwise comparisons if needed, or use overall p-value
    # For multiple comparison correction, we typically correct pairwise p-values.
    # Here, we simulate pairwise comparisons by running t-tests between all pairs
    # if we want to correct for multiple comparisons across pairs.
    # However, the task specifically asks for correction in the context of ANOVA.
    # Standard practice: If ANOVA is significant, perform post-hoc tests (e.g., Tukey).
    # But the task asks for Bonferroni/BH on the p-values.
    # We will generate pairwise p-values to demonstrate the correction logic.

    group_names = list(groups.keys())
    pairwise_p_values = []
    pairwise_comparisons = []

    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            g1, g2 = group_names[i], group_names[j]
            _, p_val = stats.ttest_ind(groups[g1], groups[g2])
            pairwise_p_values.append(p_val)
            pairwise_comparisons.append(f"{g1}_vs_{g2}")

    correction_result = apply_multiple_comparison_correction(pairwise_p_values, correction_method)

    # Combine results
    final_result = {
        "anova": anova_result,
        "pairwise_comparisons": {
            "comparisons": pairwise_comparisons,
            "raw_p_values": pairwise_p_values,
            "corrected_p_values": correction_result["corrected_p_values"],
            "rejections": correction_result["rejections"],
        },
        "correction_method": correction_result["method"],
        "correction_rationale": correction_result["rationale"],
        "alpha": 0.05,
    }

    logger.info(
        f"ANOVA completed for {target_column} by {group_column}. "
        f"F-stat: {anova_result['f_statistic']:.4f}, P-value: {anova_result['p_value']:.4e}. "
        f"Correction: {correction_result['method']}."
    )

    return final_result
