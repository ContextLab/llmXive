"""Sensitivity‑analysis utilities for metastability classification.

The module provides functions to load ground‑truth metrics, evaluate
classification thresholds, and sweep across parameter ranges.  All public
callables are fully documented.
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import List, Tuple, Dict, Any, Optional

@dataclass
class SensitivityResult:
    """Result of a single sensitivity‑analysis run.

    Attributes
    ----------
    density_threshold : float
        Threshold on condensate density drop.
    vortex_threshold : float
        Threshold on vortex density.
    false_positive_rate : float
    false_negative_rate : float
    accuracy : float
    """
    density_threshold: float
    vortex_threshold: float
    false_positive_rate: float
    false_negative_rate: float
    accuracy: float

def load_or_generate_ground_truth_metrics(metrics_dir: str) -> List[Dict[str, Any]]:
    """Load ground‑truth metrics from *metrics_dir*.

    If the directory contains CSV or JSON files with the required schema,
    they are parsed and returned.  If no such files are present, a
    ``FileNotFoundError`` is raised – the caller must ensure that the data
    exists.

    Parameters
    ----------
    metrics_dir : str
        Path to the directory containing metric files.

    Returns
    -------
    list of dict
        List of metric dictionaries, each containing at least the keys
        ``vortex_density`` and ``condensate_density``.
    """
    # For simplicity we assume a single JSON file named ``metrics.json``.
    json_path = os.path.join(metrics_dir, "metrics.json")
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"Metrics file not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_threshold(
    metrics_list: List[Dict[str, Any]],
    density_threshold: float,
    vortex_threshold: float,
) -> SensitivityResult:
    """Evaluate classification performance for given thresholds.

    The function compares the predicted metastability label (based on the
    supplied thresholds) against the ground‑truth label stored in the
    metric dictionaries.

    Parameters
    ----------
    metrics_list : list of dict
        Ground‑truth metric entries.
    density_threshold : float
        Threshold on condensate density drop.
    vortex_threshold : float
        Threshold on vortex density.

    Returns
    -------
    SensitivityResult
        Dataclass instance summarising false‑positive/negative rates and
        overall accuracy.
    """
    predictions = []
    ground_truth = []
    for m in metrics_list:
        pred = "metastable" if (
            m["vortex_density"] > vortex_threshold
            or m["condensate_density"] < density_threshold
        ) else "stable"
        predictions.append(pred)
        ground_truth.append(m["label"])

    from analysis.metrics import (
        calculate_false_positive_rate,
        calculate_false_negative_rate,
    )

    fp = calculate_false_positive_rate(predictions, ground_truth)
    fn = calculate_false_negative_rate(predictions, ground_truth)
    accuracy = sum(p == g for p, g in zip(predictions, ground_truth)) / len(predictions)

    return SensitivityResult(
        density_threshold=density_threshold,
        vortex_threshold=vortex_threshold,
        false_positive_rate=fp,
        false_negative_rate=fn,
        accuracy=accuracy,
    )

def run_sensitivity_analysis(
    metrics_dir: str,
    density_range: Tuple[float, float] = (0.5, 0.9),
    vortex_range: Tuple[float, float] = (0.2, 0.8),
    steps: int = 5,
) -> List[SensitivityResult]:
    """Run a grid search over density and vortex thresholds.

    Parameters
    ----------
    metrics_dir : str
        Directory containing ground‑truth metric files.
    density_range : tuple of float, optional
        (min, max) range for the condensate density threshold.
    vortex_range : tuple of float, optional
        (min, max) range for the vortex‑density threshold.
    steps : int, optional
        Number of discretisation steps per axis.

    Returns
    -------
    list of SensitivityResult
        Results for each combination of thresholds.
    """
    metrics = load_or_generate_ground_truth_metrics(metrics_dir)
    results = []
    for i in range(steps):
        d_thr = density_range[0] + i * (density_range[1] - density_range[0]) / (steps - 1)
        for j in range(steps):
            v_thr = vortex_range[0] + j * (vortex_range[1] - vortex_range[0]) / (steps - 1)
            results.append(evaluate_threshold(metrics, d_thr, v_thr))
    return results

def main() -> None:
    """Command‑line entry point for sensitivity analysis.

    The CLI expects a directory containing metric files and prints the
    resulting sensitivity table as JSON.
    """
    parser = argparse.ArgumentParser(description="Run sensitivity analysis.")
    parser.add_argument("metrics_dir", help="Directory with metric JSON/CSV files.")
    args = parser.parse_args()
    results = run_sensitivity_analysis(args.metrics_dir)
    print(json.dumps([asdict(r) for r in results], indent=2))

if __name__ == "__main__":
    main()
