import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for script execution
import matplotlib.pyplot as plt
import numpy as np

# Import logging utilities from the project's utils module
from utils.logging import get_logger, log_with_context

logger = get_logger(__name__)

# Constants for file paths relative to project root
DATA_PROCESSED_DIR = Path("data/processed")
BASELINE_LOGS_FILE = DATA_PROCESSED_DIR / "baseline_logs.json"
EXPERIMENTAL_LOGS_FILE = DATA_PROCESSED_DIR / "experimental_logs.json"
OUTPUT_PLOT_FILE = DATA_PROCESSED_DIR / "success_rate_vs_steps.png"


def load_convergence_results() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Load baseline and experimental logs from data/processed.
    Returns a tuple (baseline_data, experimental_data).
    If a file is missing or invalid, returns None for that entry.
    """
    baseline_data = None
    experimental_data = None

    if BASELINE_LOGS_FILE.exists():
        try:
            with open(BASELINE_LOGS_FILE, 'r', encoding='utf-8') as f:
                baseline_data = json.load(f)
            logger.info(f"Loaded baseline logs from {BASELINE_LOGS_FILE}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to parse baseline logs: {e}")
    else:
        logger.warning(f"Baseline logs file not found: {BASELINE_LOGS_FILE}")

    if EXPERIMENTAL_LOGS_FILE.exists():
        try:
            with open(EXPERIMENTAL_LOGS_FILE, 'r', encoding='utf-8') as f:
                experimental_data = json.load(f)
            logger.info(f"Loaded experimental logs from {EXPERIMENTAL_LOGS_FILE}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to parse experimental logs: {e}")
    else:
        logger.warning(f"Experimental logs file not found: {EXPERIMENTAL_LOGS_FILE}")

    return baseline_data, experimental_data


def extract_plot_data(run_logs: Dict[str, Any], run_name: str) -> List[Tuple[int, float]]:
    """
    Extract (steps, success_rate) pairs from a run log dictionary.
    Expects run_logs to have a structure like:
    {
      "runs": [
        {"steps": 100, "success_rate": 0.5},
        ...
      ]
    }
    or potentially a flattened list if the structure varies.
    Returns a sorted list of (steps, success_rate) tuples.
    """
    data_points = []

    if not run_logs:
        return data_points

    # Handle potential list of runs directly
    runs = run_logs.get("runs", run_logs if isinstance(run_logs, list) else [])

    if not isinstance(runs, list):
        logger.warning(f"Unexpected log structure for {run_name}: expected 'runs' list or list root.")
        return data_points

    for entry in runs:
        if isinstance(entry, dict):
            steps = entry.get("steps")
            success_rate = entry.get("success_rate")

            if steps is not None and success_rate is not None:
                try:
                    data_points.append((int(steps), float(success_rate)))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid numeric data in entry: {entry}")
            else:
                # Try to find keys that might be slightly different
                steps = entry.get("step") or entry.get("total_steps")
                success_rate = entry.get("success_rate") or entry.get("success_rate_avg")
                if steps is not None and success_rate is not None:
                     data_points.append((int(steps), float(success_rate)))

    # Sort by steps to ensure the plot line is continuous
    data_points.sort(key=lambda x: x[0])
    return data_points


def create_success_rate_vs_steps_plot(
    baseline_points: List[Tuple[int, float]],
    experimental_points: List[Tuple[int, float]],
    output_path: Path
) -> bool:
    """
    Create and save the 'Success Rate vs. Steps' plot.
    Returns True if successful, False otherwise.
    """
    if not baseline_points and not experimental_points:
        logger.error("No data points available to plot.")
        return False

    plt.figure(figsize=(10, 6))

    if baseline_points:
        steps, rates = zip(*baseline_points)
        plt.plot(steps, rates, marker='o', linestyle='-', color='blue', label='Static Random (Baseline)')

    if experimental_points:
        steps, rates = zip(*experimental_points)
        plt.plot(steps, rates, marker='s', linestyle='--', color='red', label='State-Guided (Experimental)')

    plt.title('Success Rate vs. Training Steps')
    plt.xlabel('Steps')
    plt.ylabel('Success Rate')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.tight_layout()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        plt.savefig(output_path)
        logger.info(f"Plot saved successfully to {output_path}")
        plt.close()
        return True
    except Exception as e:
        logger.error(f"Failed to save plot: {e}")
        plt.close()
        return False


def generate_convergence_plot() -> bool:
    """
    Main orchestration function for generating the convergence plot.
    Loads logs, extracts data, and saves the plot to data/processed/.
    """
    logger.info("Starting convergence plot generation.")

    baseline_data, experimental_data = load_convergence_results()

    baseline_points = extract_plot_data(baseline_data, "Baseline")
    experimental_points = extract_plot_data(experimental_data, "Experimental")

    success = create_success_rate_vs_steps_plot(
        baseline_points,
        experimental_points,
        OUTPUT_PLOT_FILE
    )

    if success:
        logger.info("Convergence plot generation completed successfully.")
    else:
        logger.error("Convergence plot generation failed due to missing data or save error.")

    return success


def main():
    """Entry point for the script."""
    # Ensure we are running from the project root context if needed,
    # though paths are relative to project root as per spec.
    success = generate_convergence_plot()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
