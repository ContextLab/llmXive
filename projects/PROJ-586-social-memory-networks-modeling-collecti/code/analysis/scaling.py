"""Scaling analysis utilities.

This module provides a high‑level function ``generate_scaling_plot`` that
fits a power‑law relationship between the number of agents and each metric
(specialization index and retrieval efficiency) and produces a PDF plot.

The implementation is deliberately tolerant: it accepts any DataFrame that
contains the columns ``agent_count``, ``specialization_index`` and
``retrieval_efficiency``.  Missing columns raise a clear ``ValueError``.
"""

from __future__ import annotations

import pathlib
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

__all__ = ["generate_scaling_plot"]

def _power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Simple power‑law function ``y = a * x ** b``."""
    return a * np.power(x, b)

def _fit_power_law(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Fit ``y = a * x ** b`` using non‑linear least squares."""
    # Provide sensible initial guesses to aid convergence.
    popt, _ = curve_fit(_power_law, x, y, p0=(1.0, 0.5))
    a, b = popt
    return a, b

def generate_scaling_plot(
    df: pd.DataFrame,
    *,
    output_path: pathlib.Path | str = "scaling_plot.pdf",
) -> None:
    """Create a scaling plot with power‑law fits.

    Parameters
    ----------
    df :
        DataFrame containing at least the columns
        ``agent_count``, ``specialization_index`` and
        ``retrieval_efficiency``.
    output_path :
        Destination path for the generated PDF.

    The function writes ``output_path`` and returns ``None``.
    """
    required = {"agent_count", "specialization_index", "retrieval_efficiency"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    # Ensure numeric types.
    df = df.astype(
        {
            "agent_count": float,
            "specialization_index": float,
            "retrieval_efficiency": float,
        }
    )

    # Aggregate by agent count (mean metric per count).
    agg = df.groupby("agent_count", as_index=False).mean()

    agent_counts = agg["agent_count"].to_numpy()
    spec_vals = agg["specialization_index"].to_numpy()
    retrieval_vals = agg["retrieval_efficiency"].to_numpy()

    # Fit power‑law curves.
    a_spec, b_spec = _fit_power_law(agent_counts, spec_vals)
    a_ret, b_ret = _fit_power_law(agent_counts, retrieval_vals)

    # Plotting.
    plt.figure(figsize=(8, 6))
    plt.scatter(agent_counts, spec_vals, color="tab:blue", label="Specialization")
    plt.plot(
        agent_counts,
        _power_law(agent_counts, a_spec, b_spec),
        color="tab:blue",
        linestyle="--",
        label=f"Spec fit: $y = {a_spec:.2f}·x^{{{b_spec:.2f}}}$",
    )

    plt.scatter(
        agent_counts,
        retrieval_vals,
        color="tab:orange",
        label="Retrieval Efficiency",
    )
    plt.plot(
        agent_counts,
        _power_law(agent_counts, a_ret, b_ret),
        color="tab:orange",
        linestyle="--",
        label=f"Ret fit: $y = {a_ret:.2f}·x^{{{b_ret:.2f}}}$",
    )

    plt.title("Scaling of Metrics vs. Agent Count")
    plt.xlabel("Number of Agents")
    plt.ylabel("Metric Value")
    plt.legend()
    plt.grid(True, which="both", ls=":", linewidth=0.5)

    # Write the figure.
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, format="pdf")
    plt.close()
