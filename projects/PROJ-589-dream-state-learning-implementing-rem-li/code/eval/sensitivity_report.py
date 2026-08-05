"""
Sensitivity Analysis Reporting Module.

Implements reporting logic for variance in final accuracy across temperature sweeps.
Dependent on T036 (temperature sweep execution).
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import numpy as np
from scipy.stats import variance as scipy_variance

# Project imports
from config import Config
from utils.logger import get_logger, log_event

# Ensure project root is in path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logger = get_logger(__name__)


def load_temperature_sweep_results(config: Config) -> List[Dict[str, Any]]:
    """
    Loads results from the temperature sweep execution (T036).

    Expects results to be stored in the configured results directory.
    The sweep typically generates a JSON file containing accuracy per temperature.

    Args:
        config: Configuration object containing paths.

    Returns:
        List of result dictionaries containing temperature and accuracy.
    """
    results_dir = Path(config.RESULTS_DIR)
    # Expected output from T036 sweep execution
    sweep_file = results_dir / "temperature_sweep_results.json"

    if not sweep_file.exists():
        # Fallback: look for any json in results if exact name varies
        json_files = list(results_dir.glob("*sweep*.json"))
        if not json_files:
            raise FileNotFoundError(
                f"Temperature sweep results not found at {sweep_file}. "
                "Ensure T036 (run_temperature_sweep) has been executed."
            )
        sweep_file = json_files[0]
        logger.warning(f"Using alternative sweep file: {sweep_file}")

    with open(sweep_file, 'r') as f:
        data = json.load(f)

    # Normalize to list of dicts if structure is different
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        # Try to interpret as single run
        return [data]


def compute_variance_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes statistical variance and summary metrics from the sweep results.

    Args:
        results: List of dicts with 'temperature' and 'accuracy' keys.

    Returns:
        Dictionary containing variance, mean, min, max, and full distribution.
    """
    if not results:
        return {"error": "No results provided"}

    accuracies = [r.get('accuracy', 0.0) for r in results]
    temperatures = [r.get('temperature', 0.0) for r in results]

    if len(accuracies) < 2:
        logger.warning("Insufficient data points for variance calculation.")
        return {
            "variance": 0.0,
            "mean": accuracies[0] if accuracies else 0.0,
            "count": len(accuracies),
            "temperatures": temperatures
        }

    # Use scipy variance (ddof=1 for sample variance)
    var_val = float(scipy_variance(accuracies, ddof=1))
    mean_val = float(np.mean(accuracies))
    min_val = float(np.min(accuracies))
    max_val = float(np.max(accuracies))
    std_val = float(np.std(accuracies, ddof=1))

    return {
        "variance": var_val,
        "std_dev": std_val,
        "mean_accuracy": mean_val,
        "min_accuracy": min_val,
        "max_accuracy": max_val,
        "sample_size": len(accuracies),
        "temperatures": temperatures,
        "accuracies": accuracies
    }


def generate_sensitivity_report(config: Config, output_filename: str = "sensitivity_analysis_report.json") -> str:
    """
    Generates the final sensitivity analysis report.

    1. Loads raw sweep results.
    2. Computes variance statistics.
    3. Saves report to data/results.

    Args:
        config: Configuration object.
        output_filename: Name of the output file.

    Returns:
        Path to the generated report.
    """
    logger.info("Generating sensitivity analysis report...")

    # Load data
    try:
        raw_results = load_temperature_sweep_results(config)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Compute metrics
    metrics = compute_variance_metrics(raw_results)

    # Construct report
    report = {
        "report_type": "sensitivity_analysis",
        "generated_at": datetime.utcnow().isoformat(),
        "config_snapshot": {
            "temperatures_swept": metrics.get("temperatures", []),
            "metric": "accuracy"
        },
        "statistics": {
            "variance": metrics.get("variance"),
            "standard_deviation": metrics.get("std_dev"),
            "mean": metrics.get("mean_accuracy"),
            "min": metrics.get("min_accuracy"),
            "max": metrics.get("max_accuracy"),
            "n": metrics.get("sample_size")
        },
        "raw_data": raw_results,
        "interpretation": ""
    }

    # Add interpretation
    if metrics.get("variance", 0) < 0.001:
        report["interpretation"] = (
            "Low variance observed across temperature settings. "
            "The model's performance is robust to temperature changes in the sweep range."
        )
    elif metrics.get("variance", 0) < 0.01:
        report["interpretation"] = (
            "Moderate variance observed. Temperature selection may impact performance, "
            "but the model remains generally stable."
        )
    else:
        report["interpretation"] = (
            "High variance observed. The model is highly sensitive to temperature "
            "hyperparameters within the tested range. Careful tuning is required."
        )

    # Save report
    results_dir = Path(config.RESULTS_DIR)
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / output_filename

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Sensitivity report saved to {output_path}")
    log_event("sensitivity_report_generated", {
        "path": str(output_path),
        "variance": report["statistics"]["variance"]
    })

    return str(output_path)


def main():
    """Entry point for script execution."""
    config = Config()
    try:
        report_path = generate_sensitivity_report(config)
        print(f"Report generated successfully: {report_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())