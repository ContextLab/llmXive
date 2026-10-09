"""
Visualization utilities for the project.

This module provides a function to generate scatter plots of a given metric
against a behavioral score and a CLI entry point that processes all metric–
behavior pairs defined in the aggregated metrics TSV file. After each plot is
saved, the path of the generated PNG file is appended to
`data/analysis_log.txt` for traceability (Task T069).

The implementation relies on the project's existing logging utilities:
`utils.setup_logger` writes ISO‑timestamped entries to both
`data/preprocess_log.txt` and `data/analysis_log.txt`. By using this logger,
we guarantee that the plot files are recorded in the correct log file.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt

# Project‑specific utilities
from utils import setup_logger

# Constants
ANALYSIS_LOG_PATH = Path("data/analysis_log.txt")
PLOTS_OUTPUT_DIR = Path("data/results")
METRICS_AGG_TSV = Path("data/processed/metrics_aggregated.tsv")
BEHAVIORAL_TSV = Path("data/processed/behavioral_scores.tsv")

def _ensure_output_dir() -> None:
    """Create the directory for plot files if it does not exist."""
    PLOTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _load_metrics() -> List[Tuple[str, float]]:
    """
    Load the aggregated metrics TSV.

    Expected columns: subject_id, transition_count
    Returns a list of (subject_id, transition_count) tuples.
    """
    if not METRICS_AGG_TSV.is_file():
        raise FileNotFoundError(f"Aggregated metrics file not found: {METRICS_AGG_TSV}")
    data = np.genfromtxt(METRICS_AGG_TSV, delimiter="\t", dtype=str, skip_header=1)
    # If there is only one row `np.genfromtxt` returns a 1‑D array; handle both cases
    if data.ndim == 1:
        data = np.array([data])
    return [(row[0], float(row[1])) for row in data]

def _load_behavioral_scores() -> List[Tuple[str, float]]:
    """
    Load a TSV containing behavioral scores (e.g., DSST).

    Expected columns: subject_id, dsst_score
    Returns a list of (subject_id, dsst_score) tuples.
    """
    if not BEHAVIORAL_TSV.is_file():
        raise FileNotFoundError(f"Behavioral scores file not found: {BEHAVIORAL_TSV}")
    data = np.genfromtxt(BEHAVIORAL_TSV, delimiter="\t", dtype=str, skip_header=1)
    if data.ndim == 1:
        data = np.array([data])
    return [(row[0], float(row[1])) for row in data]

def generate_scatter_plot(
    metric_name: str,
    behavior_name: str,
    x: np.ndarray,
    y: np.ndarray,
    output_path: Path,
) -> None:
    """
    Create a scatter plot with a linear fit line and 95 % confidence interval.

    Parameters
    ----------
    metric_name : str
        Name of the metric (used for axis label and filename).
    behavior_name : str
        Name of the behavioral measure (used for axis label).
    x : np.ndarray
        Metric values (e.g., transition counts).
    y : np.ndarray
        Behavioral scores (e.g., DSST).
    output_path : Path
        Destination file path for the PNG image.
    """
    plt.figure(figsize=(6, 4))
    plt.scatter(x, y, alpha=0.7, edgecolor="k", linewidth=0.5)

    # Linear regression for the fit line
    if len(x) > 1:
        coeffs = np.polyfit(x, y, deg=1)
        fit_x = np.linspace(np.min(x), np.max(x), 100)
        fit_y = np.polyval(coeffs, fit_x)
        plt.plot(fit_x, fit_y, color="red", lw=2, label="Fit line")

        # Simple 95 % CI approximation using standard error of the estimate
        residuals = y - np.polyval(coeffs, x)
        se = np.sqrt(np.sum(residuals ** 2) / (len(x) - 2))
        ci = 1.96 * se
        plt.fill_between(
            fit_x,
            fit_y - ci,
            fit_y + ci,
            color="red",
            alpha=0.2,
            label="95 % CI",
        )

    plt.title(f"{metric_name} vs. {behavior_name}")
    plt.xlabel(metric_name)
    plt.ylabel(behavior_name)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

def _log_plot_path(logger: logging.Logger, plot_path: Path) -> None:
    """
    Append a line to the analysis log indicating that a plot was created.

    The logger configured by ``utils.setup_logger`` already writes to
    ``data/analysis_log.txt``. We simply log an INFO message; the logger's
    formatter includes the ISO‑timestamp required by the project spec.
    """
    logger.info(f"Plot generated: {plot_path}")

def main() -> None:
    """
    Entry point for the ``python -m code.viz`` CLI.

    The function:
    1. Loads metric values and behavioral scores.
    2. Aligns subjects present in both files.
    3. Generates a scatter plot for the (metric, behavior) pair.
    4. Writes the plot to ``data/results/plot_{metric}_{behavior}.png``.
    5. Logs the plot file path to ``data/analysis_log.txt``.
    """
    logger = setup_logger()  # Writes to both preprocess and analysis logs
    _ensure_output_dir()

    # Load data
    metrics = dict(_load_metrics())          # subject_id -> metric value
    behaviors = dict(_load_behavioral_scores())  # subject_id -> behavior value

    # Align subjects present in both datasets
    common_subjects = sorted(set(metrics) & set(behaviors))
    if not common_subjects:
        logger.warning("No overlapping subjects between metrics and behavioral data.")
        return

    metric_vals = np.array([metrics[s] for s in common_subjects])
    behavior_vals = np.array([behaviors[s] for s in common_subjects])

    # Define names for logging / filenames
    metric_name = "transition_count"
    behavior_name = "DSST_score"

    plot_filename = f"plot_{metric_name}_{behavior_name}.png"
    plot_path = PLOTS_OUTPUT_DIR / plot_filename

    # Generate and save the scatter plot
    generate_scatter_plot(
        metric_name=metric_name,
        behavior_name=behavior_name,
        x=metric_vals,
        y=behavior_vals,
        output_path=plot_path,
    )

    # Ensure the analysis log file exists (setup_logger creates it, but we double‑check)
    ANALYSIS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_LOG_PATH.touch(exist_ok=True)

    # Log the plot location for traceability (Task T069)
    _log_plot_path(logger, plot_path)

    logger.info("Visualization step completed successfully.")

if __name__ == "__main__":
    # Allow the module to be executed directly: ``python code/viz.py``
    main()
