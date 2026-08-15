"""
Sensitivity Analysis Module for Solar Irradiance Reconstruction.

This module implements the sensitivity analysis required by FR-009.
It loads per-cycle baseline offsets derived from the Cycle-Agnostic fallback model,
sweeps the inconsistency tolerance threshold, and measures reconstruction stability.

Output: data/processed/sensitivity_report.json
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd

from config import ensure_directories
from env_manager import get_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
THRESHOLD_SWEEP_VALUES = [0.01, 0.05, 0.1]
OUTPUT_FILENAME = "sensitivity_report.json"


def load_cycle_offsets() -> Dict[str, float]:
    """
    Load the per-cycle baseline offsets from the fallback model training.

    Returns:
        Dict mapping cycle IDs (as strings) to their baseline offset values.

    Raises:
        FileNotFoundError: If the offsets file does not exist.
        ValueError: If the file is empty or malformed.
    """
    data_path = get_data_path()
    offsets_path = data_path / "processed" / "cycle_specific_coefficients.json"

    if not offsets_path.exists():
        raise FileNotFoundError(
            f"Cycle offsets file not found at {offsets_path}. "
            "Run T019 (train_fallback.py) first to generate this artifact."
        )

    with open(offsets_path, "r") as f:
        data = json.load(f)

    if not data:
        raise ValueError("Cycle offsets file is empty.")

    return data


def calculate_stability_metric(
    offsets: Dict[str, float],
    threshold: float
) -> float:
    """
    Calculate the reconstruction stability metric for a given threshold.

    The stability is defined as the standard deviation of RMSE across the sweep,
    comparing against the Cycle-Agnostic baseline. In this context, we simulate
    the effect of the threshold on the effective offsets used for reconstruction.

    For a given threshold, we filter or adjust offsets that deviate significantly
    from the mean (representing the baseline). The "RMSE" proxy is calculated
    based on the variance of the adjusted offsets.

    Args:
        offsets: Dict of cycle_id -> baseline_offset.
        threshold: The inconsistency tolerance threshold.

    Returns:
        float: A proxy for RMSE stability (standard deviation of adjusted offsets).
    """
    if not offsets:
        return 0.0

    values = np.array(list(offsets.values()))
    mean_offset = np.mean(values)

    # Simulate the effect of the threshold:
    # Offsets with absolute difference from mean > threshold are considered
    # "inconsistent" and are clipped to the threshold boundary relative to the mean.
    # This simulates the robustness of the reconstruction when ignoring outliers.
    adjusted_values = np.clip(values, mean_offset - threshold, mean_offset + threshold)

    # The stability metric is the standard deviation of these adjusted values.
    # A lower std dev implies higher stability (less variance in the reconstruction).
    stability_rmse_proxy = np.std(adjusted_values)

    return stability_rmse_proxy


def run_sensitivity_sweep() -> Dict[str, Any]:
    """
    Execute the sensitivity analysis sweep over inconsistency tolerance thresholds.

    Returns:
        Dict containing the sweep results, including per-threshold metrics and
        the overall stability calculation.
    """
    logger.info("Loading cycle-specific coefficients...")
    offsets = load_cycle_offsets()
    logger.info(f"Loaded offsets for {len(offsets)} cycles.")

    results = {
        "thresholds": THRESHOLD_SWEEP_VALUES,
        "metrics": [],
        "summary": {}
    }

    rmse_values = []

    for threshold in THRESHOLD_SWEEP_VALUES:
        logger.info(f"Processing threshold: {threshold}")
        rmse = calculate_stability_metric(offsets, threshold)
        rmse_values.append(rmse)
        
        results["metrics"].append({
            "threshold": threshold,
            "stability_rmse": float(rmse)
        })

    # Calculate overall stability (std dev of RMSE across the sweep)
    overall_stability = float(np.std(rmse_values))
    
    results["summary"] = {
        "sweep_values": THRESHOLD_SWEEP_VALUES,
        "stability_metric_std_dev": overall_stability,
        "interpretation": "Lower std dev indicates higher reconstruction stability across thresholds."
    }

    logger.info(f"Sensitivity analysis complete. Stability std dev: {overall_stability:.6f}")
    return results


def save_report(report: Dict[str, Any]) -> Path:
    """
    Save the sensitivity report to the processed data directory.

    Args:
        report: The dictionary containing the analysis results.

    Returns:
        Path to the saved JSON file.
    """
    data_path = get_data_path()
    ensure_directories()
    output_path = data_path / "processed" / OUTPUT_FILENAME

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report saved to {output_path}")
    return output_path


def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Main entry point for the sensitivity analysis pipeline.

    Returns:
        The generated report dictionary.
    """
    report = run_sensitivity_sweep()
    save_report(report)
    return report


def main() -> None:
    """CLI entry point."""
    try:
        report = run_sensitivity_analysis()
        print(json.dumps(report, indent=2))
    except FileNotFoundError as e:
        logger.error(f"Data missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()