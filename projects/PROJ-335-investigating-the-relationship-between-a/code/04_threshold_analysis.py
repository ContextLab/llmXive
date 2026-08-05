"""
T034: Compare correlation coefficients and reliability metrics to thresholds.

This script loads the results from the correlation analysis (r-values) and
split-half reliability analysis, compares them against defined thresholds,
and outputs a JSON summary to data/results/threshold_results.json.

Thresholds:
- Correlation coefficient |r| >= 0.3
- Reliability coefficient >= 0.7
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.logging_config import setup_logging, get_logger
from code.config import load_config


def load_analysis_results(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load correlation and reliability results from data/results/.

    Expects:
    - data/results/correlation_results.json (from T030/T032)
    - data/results/reliability_results.json (from T033)

    Returns a dictionary with r_value and reliability_coeff.
    """
    results_dir = Path(config.get("paths", {}).get("results", "data/results"))

    # Load correlation results
    corr_file = results_dir / "correlation_results.json"
    if not corr_file.exists():
        raise FileNotFoundError(f"Correlation results file not found: {corr_file}")

    with open(corr_file, "r") as f:
        corr_data = json.load(f)

    # Extract r_value (assume it's the primary correlation coefficient)
    # Structure expected: {"partial_correlation": {"r": <value>, ...}} or similar
    r_value = None
    if "partial_correlation" in corr_data:
        r_value = corr_data["partial_correlation"].get("r")
    elif "correlation" in corr_data:
        r_value = corr_data["correlation"].get("r")
    elif "r" in corr_data:
        r_value = corr_data["r"]

    if r_value is None:
        raise ValueError("Could not extract 'r' value from correlation results")

    # Load reliability results
    rel_file = results_dir / "reliability_results.json"
    if not rel_file.exists():
        raise FileNotFoundError(f"Reliability results file not found: {rel_file}")

    with open(rel_file, "r") as f:
        rel_data = json.load(f)

    # Extract reliability coefficient (split-half reliability)
    # Structure expected: {"split_half": {"reliability_coeff": <value>, ...}}
    reliability_coeff = None
    if "split_half" in rel_data:
        reliability_coeff = rel_data["split_half"].get("reliability_coeff")
    elif "reliability_coeff" in rel_data:
        reliability_coeff = rel_data["reliability_coeff"]
    elif "reliability" in rel_data:
        reliability_coeff = rel_data["reliability"].get("coefficient")

    if reliability_coeff is None:
        raise ValueError("Could not extract 'reliability_coeff' from reliability results")

    return {
        "r_value": r_value,
        "reliability_coeff": reliability_coeff
    }


def evaluate_thresholds(r_value: float, reliability_coeff: float) -> Dict[str, Any]:
    """
    Compare metrics against thresholds and determine status.

    Thresholds:
    - |r| >= 0.3 -> PASS, else FAIL
    - reliability >= 0.7 -> PASS, else LOW

    Returns a dictionary with status and values.
    """
    # Evaluate correlation threshold
    threshold_status = "PASS" if abs(r_value) >= 0.3 else "FAIL"

    # Evaluate reliability threshold
    reliability_status = "PASS" if reliability_coeff >= 0.7 else "LOW"

    return {
        "threshold_status": threshold_status,
        "reliability_status": reliability_status,
        "r_value": r_value,
        "reliability_coeff": reliability_coeff
    }


def save_threshold_results(results: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    Save threshold results to data/results/threshold_results.json.

    Returns the path to the saved file.
    """
    results_dir = Path(config.get("paths", {}).get("results", "data/results"))
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / "threshold_results.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    return str(output_file)


def main():
    """
    Main entry point for T034 threshold analysis.
    """
    # Setup logging
    logger = setup_logging()
    logger = get_logger(__name__)

    logger.info("Starting T034: Threshold Analysis")

    try:
        # Load configuration
        config = load_config()
        logger.info(f"Loaded configuration from {config.get('config_path', 'default')}")

        # Load analysis results
        logger.info("Loading correlation and reliability results...")
        metrics = load_analysis_results(config)
        logger.info(f"Loaded r_value={metrics['r_value']}, reliability_coeff={metrics['reliability_coeff']}")

        # Evaluate thresholds
        logger.info("Evaluating thresholds...")
        threshold_results = evaluate_thresholds(
            metrics["r_value"],
            metrics["reliability_coeff"]
        )

        logger.info(f"Threshold Status: {threshold_results['threshold_status']}")
        logger.info(f"Reliability Status: {threshold_results['reliability_status']}")

        # Save results
        output_path = save_threshold_results(threshold_results, config)
        logger.info(f"Threshold results saved to {output_path}")

        # Print summary
        print("\n" + "="*50)
        print("THRESHOLD ANALYSIS RESULTS")
        print("="*50)
        print(f"Correlation Coefficient (r): {threshold_results['r_value']:.4f}")
        print(f"Threshold (|r| >= 0.3): {threshold_results['threshold_status']}")
        print(f"Reliability Coefficient: {threshold_results['reliability_coeff']:.4f}")
        print(f"Threshold (>= 0.7): {threshold_results['reliability_status']}")
        print("="*50)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: Required input file missing. {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        print(f"ERROR: Invalid data format. {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())