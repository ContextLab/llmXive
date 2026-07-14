"""
src/analysis/robustness.py
---------------------------

Executes the primary correlation pipeline (implemented in
``src.analysis.correlation``) separately for visual and auditory modality
subsets.  The results are written to ``data/results/robustness_analysis.json``.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

from src.analysis.correlation import (
    load_trial_data,
    compute_hold_out_metrics,
    write_results as write_correlation_results,
)
from src.analysis.filter import (
    setup_directories as filter_setup_directories,
    load_trial_data as filter_load_trial_data,
    filter_by_modality,
    write_output as filter_write_output,
)

# ----------------------------------------------------------------------
# Logging helpers (simple console logger)
# ----------------------------------------------------------------------
def _setup_logging() -> None:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

def log_info(message: str) -> None:
    _setup_logging()
    logging.getLogger(__name__).info(message)

def log_error(message: str) -> None:
    _setup_logging()
    logging.getLogger(__name__).error(message)

# ----------------------------------------------------------------------
# Core functions
# ----------------------------------------------------------------------
def _determine_project_root() -> Path:
    """Return repository root (two levels up from this file)."""
    return Path(__file__).resolve().parents[3]

def run_bootstrap_correlation(
    trial_rows: list, bootstrap_count: int = 1000
) -> dict:
    """
    Wrapper that re‑uses the existing correlation bootstrap logic.
    For simplicity we call the correlation analysis directly (which already
    performs bootstrapping via ``src.analysis.bootstrap`` when required).
    """
    # The correlation module writes its own JSON; we capture the returned
    # dictionary for inclusion in the robustness summary.
    # Here we simply invoke the same computation without persisting
    # intermediate files.
    return compute_hold_out_metrics(trial_rows)

def run_robustness_analysis() -> dict:
    """
    Run the hold‑out correlation pipeline for each modality and collect
    results into a single dictionary.
    """
    project_root = _determine_project_root()
    derived_dir = project_root / "data" / "derived"

    results = {}
    for modality in ("visual", "auditory"):
        modality_file = derived_dir / f"{modality}_trials.csv"
        if not modality_file.is_file():
            log_error(f"Missing modality file: {modality_file}")
            continue

        log_info(f"Processing modality: {modality}")
        trial_rows = load_trial_data(modality_file)
        metrics = compute_hold_out_metrics(trial_rows)
        results[modality] = metrics

    return results

def write_results(results: dict, output_path: Path) -> None:
    """Write the robustness summary JSON."""
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    log_info(f"Robustness results written to {output_path}")

def main() -> None:
    """Entry point for the robustness analysis."""
    project_root = _determine_project_root()
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "robustness_analysis.json"

    results = run_robustness_analysis()
    if not results:
        log_error("Robustness analysis produced no results.")
        sys.exit(1)

    write_results(results, output_path)
    sys.exit(0)

if __name__ == "__main__":
    main()
