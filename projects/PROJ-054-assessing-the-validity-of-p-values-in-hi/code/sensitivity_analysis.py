"""
Sensitivity analysis module for varying correlation structures.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def load_trajectories_for_rho(
    trajectory_dir: str,
    rho_value: float
) -> List[Dict[str, Any]]:
    """
    Load trajectory files matching a specific rho value.

    Args:
        trajectory_dir: Directory containing trajectory files
        rho_value: Target correlation value

    Returns:
        List of trajectory data dictionaries.
    """
    results = []
    path = Path(trajectory_dir)
    for file_path in path.glob("*.json"):
        with open(file_path, 'r') as f:
            content = json.load(f)
            if abs(content.get("rho", 0) - rho_value) < 1e-6:
                results.append(content)
    return results

def calculate_ks_statistic_for_rho(
    trajectories: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Calculate KS statistics for a set of trajectories with the same rho.

    Args:
        trajectories: List of trajectory data

    Returns:
        Dictionary with aggregated KS statistics.
    """
    from scipy import stats
    all_pvals = []
    for traj in trajectories:
        if "iterations" in traj:
            for iter_data in traj["iterations"]:
                all_pvals.extend(iter_data["p_values"])
        elif "p_values" in traj:
            all_pvals.extend(traj["p_values"])

    if not all_pvals:
        return {"KS_statistic": 0.0, "p_value": 1.0}

    ks_stat, p_val = stats.kstest(all_pvals, 'uniform')
    return {
        "KS_statistic": float(ks_stat),
        "p_value": float(p_val),
        "n_pvalues": len(all_pvals)
    }

def run_sensitivity_analysis(
    trajectory_dir: str,
    rho_values: List[float]
) -> Dict[float, Dict[str, float]]:
    """
    Run sensitivity analysis across different rho values.

    Args:
        trajectory_dir: Directory containing trajectory files
        rho_values: List of rho values to analyze

    Returns:
        Dictionary mapping rho to KS statistics.
    """
    results = {}
    for rho in rho_values:
        trajectories = load_trajectories_for_rho(trajectory_dir, rho)
        ks_stats = calculate_ks_statistic_for_rho(trajectories)
        results[rho] = ks_stats
    return results

def main():
    """
    Entry point for sensitivity analysis.
    """
    logger.info("Sensitivity analysis module loaded.")
