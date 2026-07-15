import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import csv
import os
from material_db import get_material_conductivity

logger = logging.getLogger(__name__)

def run_sensitivity_sweep(config: Any, baseline_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run sensitivity sweep over scaling factors.
    """
    if not baseline_results:
        logger.warning("No baseline results for sensitivity analysis")
        return []

    factors = config.sensitivity_factors
    sensitivity_results = []

    for factor in factors:
        logger.info(f"Processing sensitivity factor: {factor}")

        # For each baseline result, apply scaling factor to conductivity
        for base_row in baseline_results:
            new_row = base_row.copy()
            # Scale conductivity
            if "conductivity" in new_row and new_row["conductivity"] is not None:
                new_row["conductivity"] = new_row["conductivity"] * factor
            new_row["scaling_factor"] = factor

            sensitivity_results.append(new_row)

    return sensitivity_results

def calculate_deviation_report(baseline_results: List[Dict[str, Any]], sensitivity_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate deviation report comparing sensitivity results to baseline.
    """
    if not baseline_results or not sensitivity_results:
        return {"deviations": []}

    df_baseline = pd.DataFrame(baseline_results)
    df_sens = pd.DataFrame(sensitivity_results)

    # Merge on seed, N, p, avg_degree
    merged = pd.merge(
        df_sens,
        df_baseline,
        on=["seed", "N", "p", "avg_degree"],
        suffixes=("_sens", "_base")
    )

    deviations = []
    for _, row in merged.iterrows():
        base_k = row["conductivity_base"]
        sens_k = row["conductivity_sens"]
        if base_k and base_k != 0:
            deviation_pct = ((sens_k - base_k) / base_k) * 100
            deviations.append({
                "seed": row["seed"],
                "factor": row["scaling_factor"],
                "deviation_pct": deviation_pct
            })

    return {"deviations": deviations}

def report_sensitivity_results(deviation_report: Dict[str, Any]) -> None:
    """
    Report sensitivity results to logger.
    """
    deviations = deviation_report.get("deviations", [])
    if not deviations:
        logger.info("No sensitivity deviations to report")
        return

    # Calculate stats
    dev_values = [d["deviation_pct"] for d in deviations]
    mean_dev = np.mean(dev_values)
    max_dev = max(abs(d) for d in dev_values)

    logger.info(f"Sensitivity analysis complete. Mean deviation: {mean_dev:.2f}%, Max deviation: {max_dev:.2f}%")

    # Check if within ±10%
    if max_dev <= 10.0:
        logger.info("All deviations within ±10% tolerance")
    else:
        logger.warning(f"Some deviations exceed ±10% tolerance (max: {max_dev:.2f}%)")

def analyze_sensitivity(config: Any, baseline_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Full sensitivity analysis pipeline.
    """
    logger.info("Starting sensitivity analysis")

    # Run sweep
    sweep_results = run_sensitivity_sweep(config, baseline_results)

    # Calculate deviations
    dev_report = calculate_deviation_report(baseline_results, sweep_results)

    # Report
    report_sensitivity_results(dev_report)

    return sweep_results
