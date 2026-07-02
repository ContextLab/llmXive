"""Scaling analysis utilities.

Provides a thin wrapper around the existing power‑law fitting code to
generate the scaling plot required by task T030.
"""

from __future__ import annotations

import pathlib
from typing import Any, Tuple

import pandas as pd

from analysis.scaling import fit_power_law_with_ci, generate_scaling_plot as _gen_plot

__all__ = ["generate_scaling_plot"]


def generate_scaling_plot(csv_path: pathlib.Path, output_path: pathlib.Path) -> None:
    """Read ``csv_path`` (produced by ``run_experiment``) and write a PDF plot.

    The plot shows specialization index and retrieval efficiency versus the
    number of agents, together with fitted power‑law curves.
    """
    df = pd.read_csv(csv_path)

    # Fit power‑law curves for both metrics
    spec_fit = fit_power_law_with_ci(df, metric="specialization_index")
    retrieval_fit = fit_power_law_with_ci(df, metric="retrieval_efficiency")

    # Generate the plot
    _gen_plot(
        spec_fit=spec_fit,
        retrieval_fit=retrieval_fit,
        output_path=output_path,
    )
