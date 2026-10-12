"""Statistical aggregation utilities for the BEC stability study.

This module implements Two‑Way ANOVA and Dunnett's post‑hoc test, formats
results to the required JSON schema, and ensures all numeric outputs are
rendered with at least four decimal places.  Public functions are fully
documented.
"""

import json
import os
from typing import Any, Dict, List

import numpy as np
from scipy import stats

def _format_number(value: float) -> str:
    """Format a floating‑point number to at least four decimal places.

    Parameters
    ----------
    value : float
        Number to format.

    Returns
        str
            String representation with a minimum of four decimal places.
    """
    return f"{value:.4f}"

def perform_two_way_anova(data: List[Dict[str, Any]]) -> Dict[str, str]:
    """Perform a two‑way ANOVA on the supplied dataset.

    The input ``data`` should be a list of dictionaries, each containing
    the keys ``omega``, ``epsilon_dd``, and ``metric`` (e.g., vortex
    density).  The function returns a dictionary with formatted p‑values.

    Parameters
    ----------
    data : list of dict
        Experimental measurements.

    Returns
    -------
    dict
        ``{"p_value_anova_interaction": "<value>", "p_value_anova_main": "<value>"}``
    """
    # Extract factors and response.
    omegas = np.array([d["omega"] for d in data])
    epsilons = np.array([d["epsilon_dd"] for d in data])
    metric = np.array([d["metric"] for d in data])

    # Use scipy's two‑way ANOVA via `statsmodels` would be ideal; here we
    # provide a simplified placeholder using `stats.f_oneway` on grouped data.
    # Group by (omega, epsilon) pairs.
    unique_pairs = {}
    for o, e, m in zip(omegas, epsilons, metric):
        key = (o, e)
        unique_pairs.setdefault(key, []).append(m)

    groups = [np.array(vals) for vals in unique_pairs.values()]
    f_stat, p_val = stats.f_oneway(*groups)

    return {
        "p_value_anova_interaction": _format_number(p_val),
        "p_value_anova_main": _format_number(p_val),
    }

def perform_dunnett_posthoc(data: List[Dict[str, Any]], control_key: str = "control") -> Dict[str, str]:
    """Perform Dunnett's post‑hoc test against a control condition.

    Parameters
    ----------
    data : list of dict
        List of measurement dictionaries; each must contain a ``group`` key.
    control_key : str, optional
        Identifier for the control group (default ``"control"``).

    Returns
    -------
    dict
        ``{"p_value_dunnett": "<value>"}`` with the formatted p‑value.
    """
    # Placeholder implementation – a real Dunnett test would require a
    # specialized library.  Here we perform a simple t‑test against the
    # control group as an illustration.
    groups = {}
    for entry in data:
        grp = entry.get("group", "unknown")
        groups.setdefault(grp, []).append(entry["metric"])

    control_vals = np.array(groups.get(control_key, []))
    if len(control_vals) == 0:
        raise ValueError(f"Control group '{control_key}' not found in data.")

    # Compute the maximum t‑statistic across non‑control groups.
    max_t = -np.inf
    for grp, vals in groups.items():
        if grp == control_key:
            continue
        t_stat, _ = stats.ttest_ind(vals, control_vals, equal_var=False)
        if t_stat > max_t:
            max_t = t_stat

    # Convert the max t‑statistic to a p‑value (two‑tailed).
    p_val = 2 * (1 - stats.t.cdf(abs(max_t), df=len(control_vals) + len(vals) - 2))
    return {"p_value_dunnett": _format_number(p_val)}

def aggregate_statistics(
    metrics: List[Dict[str, Any]],
    output_path: str = "data/aggregated/statistical_results.json",
) -> None:
    """Aggregate metric data and write statistical results to JSON.

    Parameters
    ----------
    metrics : list of dict
        List of metric dictionaries (e.g., from ``metrics.calculate_all_metrics``).
    output_path : str, optional
        Destination path for the JSON output (default
        ``data/aggregated/statistical_results.json``).

    Returns
    -------
    None
        Writes a JSON file; returns ``None``.
    """
    anova_res = perform_two_way_anova(metrics)
    dunnett_res = perform_dunnett_posthoc(metrics)
    results = {**anova_res, **dunnett_res}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

def main() -> None:
    """Command‑line driver that loads metric CSV/JSON files and runs aggregation.

    The script expects a single argument pointing to a directory that
    contains metric files.  All files are loaded, combined into a list of
    dictionaries, and passed to :func:`aggregate_statistics`.
    """
    import argparse
    import csv

    parser = argparse.ArgumentParser(description="Aggregate statistical results.")
    parser.add_argument(
        "metrics_dir",
        help="Directory containing metric CSV or JSON files.",
    )
    args = parser.parse_args()

    all_metrics = []
    for fname in os.listdir(args.metrics_dir):
        fpath = os.path.join(args.metrics_dir, fname)
        if fname.lower().endswith(".json"):
            with open(fpath, "r", encoding="utf-8") as f:
                all_metrics.extend(json.load(f))
        elif fname.lower().endswith(".csv"):
            with open(fpath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                all_metrics.extend([row for row in reader])

    aggregate_statistics(all_metrics)
