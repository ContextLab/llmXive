"""
Aggregation module for robustness metrics.

This module consolidates results from permutation tests, sensitivity analyses,
and ICV-restricted analyses into a comprehensive report.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from code.config import get_project_root, ensure_directories


def load_permutation_results(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load permutation test results.

    Args:
        filepath: Path to the robustness report.

    Returns:
        Dictionary of permutation results.
    """
    if filepath is None:
        project_root = get_project_root()
        filepath = str(project_root / "data" / "processed" / "robustness_report.json")

    with open(filepath, 'r') as f:
        data = json.load(f)

    return data.get("permutation_tests", {})


def load_sensitivity_report(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load sensitivity analysis report.

    Args:
        filepath: Path to the sensitivity report CSV.

    Returns:
        Dictionary of sensitivity results.
    """
    import pandas as pd
    if filepath is None:
        project_root = get_project_root()
        filepath = str(project_root / "data" / "processed" / "sensitivity_report.csv")

    df = pd.read_csv(filepath)
    return df.to_dict(orient='records')


def load_icv_restricted_results(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load ICV restricted analysis results.

    Args:
        filepath: Path to the ICV results JSON.

    Returns:
        Dictionary of ICV restricted results.
    """
    if filepath is None:
        project_root = get_project_root()
        filepath = str(project_root / "data" / "processed" / "icv_restricted_results.json")

    with open(filepath, 'r') as f:
        return json.load(f)


def load_primary_model_results(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load primary model results.

    Args:
        filepath: Path to the model results JSON.

    Returns:
        Dictionary of model results.
    """
    if filepath is None:
        project_root = get_project_root()
        filepath = str(project_root / "data" / "processed" / "model_results.json")

    with open(filepath, 'r') as f:
        return json.load(f)


def aggregate_metrics(
    perm_results: Dict[str, Any],
    sens_results: List[Dict[str, Any]],
    icv_results: Dict[str, Any],
    primary_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all robustness metrics into a summary.

    Args:
        perm_results: Permutation test results.
        sens_results: Sensitivity analysis results.
        icv_results: ICV restricted results.
        primary_results: Primary model results.

    Returns:
        Aggregated metrics dictionary.
    """
    summary = {
        "permutation_summary": {},
        "sensitivity_summary": {},
        "icv_effect_stability": {},
        "overall_robustness_score": 0.0
    }

    # Permutation summary
    for subfield, data in perm_results.items():
        p_perm = data.get("p_permutation", 1.0)
        summary["permutation_summary"][subfield] = {
            "p_permutation": p_perm,
            "significant": p_perm < 0.05
        }

    # Sensitivity summary
    if sens_results:
        counts = [r.get("significant_count", 0) for r in sens_results]
        summary["sensitivity_summary"] = {
            "min_significant": min(counts) if counts else 0,
            "max_significant": max(counts) if counts else 0,
            "mean_significant": sum(counts) / len(counts) if counts else 0
        }

    # ICV effect stability
    if "effect_size_changes" in icv_results:
        changes = icv_results["effect_size_changes"]
        summary["icv_effect_stability"] = {
            subfield: change for subfield, change in changes.items()
        }

    # Overall robustness score (simple heuristic)
    # Higher is better: permutations confirm significance, stability is high
    perm_sig_count = sum(1 for v in summary["permutation_summary"].values() if v["significant"])
    total_subfields = len(summary["permutation_summary"])
    if total_subfields > 0:
        summary["overall_robustness_score"] = perm_sig_count / total_subfields

    return summary


def main() -> None:
    """
    Main entry point for aggregating robustness metrics.
    """
    project_root = get_project_root()
    ensure_directories()

    # Load all reports
    perm_results = load_permutation_results()
    sens_results = load_sensitivity_report()
    icv_results = load_icv_restricted_results()
    primary_results = load_primary_model_results()

    # Aggregate
    summary = aggregate_metrics(perm_results, sens_results, icv_results, primary_results)

    # Save summary
    output_path = project_root / "data" / "processed" / "robustness_summary.json"
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logging.info(f"Aggregated robustness summary saved to {output_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
