"""Generate scaling analysis plot for the Social Memory Networks project.

This script orchestrates the creation of a PDF plot showing how the
specialization index and retrieval efficiency metrics scale with the
number of agents.  It first ensures that the raw scaling data exists by
invoking ``run_scaling_experiment.py`` (which runs the simulations for
the required agent counts).  The resulting CSV is then loaded, a
power‑law fit with confidence intervals is computed, and a figure is
produced with an explicit note that the analysis is based on only three
data points (agents = 3, 5, 7), limiting the reliability of the fitted
exponent.

The generated PDF is written to:
    projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

# Import the high‑level helper that creates the figure.
# The function is defined in ``code/analysis/scaling_plot_generator.py``.
from analysis.scaling_plot_generator import generate_scaling_plot_with_notes

# Constants that match the repository layout
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
SCALING_DATA_CSV = RESULTS_DIR / "scaling_data.csv"
SCALING_PLOT_PDF = RESULTS_DIR / "scaling_plot.pdf"

def ensure_scaling_data() -> Path:
    """Make sure the CSV with raw scaling data exists.

    If the file is missing we invoke ``run_scaling_experiment.py`` which
    runs the simulations for agent counts 3, 5, and 7 (800 games each) and
    writes the aggregated CSV to ``RESULTS_DIR``.
    """
    if SCALING_DATA_CSV.is_file():
        return SCALING_DATA_CSV

    # ``run_scaling_experiment.py`` expects to be executed from the repo
    # root.  We call it via ``python -m`` so the import machinery works
    # regardless of the current working directory.
    script_path = PROJECT_ROOT / "code" / "run_scaling_experiment.py"
    if not script_path.is_file():
        sys.exit(f"Missing scaling experiment script: {script_path}")

    # Run the script; it will write ``scaling_data.csv`` to the results dir.
    # Using ``check=True`` ensures we fail fast if the experiment crashes.
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        check=True,
    )

    if not SCALING_DATA_CSV.is_file():
        sys.exit(
            f"Expected scaling data CSV at {SCALING_DATA_CSV} but it was not created."
        )
    return SCALING_DATA_CSV

def main() -> None:
    """Entry point for the scaling‑plot generation script."""
    # Ensure the results directory exists.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: obtain the raw data.
    csv_path = ensure_scaling_data()
    data = pd.read_csv(csv_path)

    # Step 2: generate the plot with a note about the limited data points.
    # ``generate_scaling_plot_with_notes`` returns a ``ScalingPlotResult``
    # which contains the Matplotlib figure; the function also writes the
    # PDF to the supplied path.
    generate_scaling_plot_with_notes(
        data=data,
        output_path=SCALING_PLOT_PDF,
        note=(
            "Only three agent‑count points (3, 5, 7) are available; "
            "power‑law fits based on such few points should be interpreted "
            "cautiously."
        ),
    )

    print(f"Scaling plot written to {SCALING_PLOT_PDF}")

if __name__ == "__main__":
    main()
