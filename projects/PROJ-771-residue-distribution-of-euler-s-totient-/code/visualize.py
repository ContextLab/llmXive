"""
Visualization utilities for the Euler Totient residue distribution pipeline.

This module provides functions that are imported by ``code/run_analysis.py``.
The expected call pattern (as used in the orchestrator) is::

    data = load_residue_data(residue_path)
    plot_bar_frequencies(data, prime)
    plot_residual_qq(data, prime)
    annotate_theoretical_bounds(prime, data)
    generate_visualization_report(prime, N, stats_path)

All functions are deliberately side‑effecting: they write PNG files under
``results/plots/`` and a short markdown report under ``results/reports/``.
The PNGs are saved with a DPI of at least 300 to satisfy the publication‑quality
requirement.

The implementation avoids any synthetic data – it reads the real JSON artefacts
produced by the earlier stages of the pipeline.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chi2, probplot

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
GOLDEN_RATIO = 1.618033988749895  # φ – theoretical error‑bound constant

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _ensure_int_keys(freq_map: Dict[str, Any]) -> Dict[int, int]:
    """
    Convert the keys of a frequency map from strings to integers.

    The JSON schema stores the residue class as a string (because JSON
    object keys must be strings).  Downstream code works with ``int`` keys,
    so we normalise here.

    Parameters
    ----------
    freq_map:
        Mapping ``\"0\" → count`` etc. as read from JSON.

    Returns
    -------
    dict[int, int]
        Mapping with integer keys.
    """
    return {int(k): int(v) for k, v in freq_map.items()}

# ----------------------------------------------------------------------
# Public API – functions imported by ``run_analysis.py``
# ----------------------------------------------------------------------
def load_residue_data(path: str) -> Dict[str, Any]:
    """
    Load a ``ResidueDataset`` JSON file.

    Parameters
    ----------
    path:
        Path to the JSON file produced by the sieve stage
        (e.g. ``data/raw/residues_3_100.json``).

    Returns
    -------
    dict
        The parsed JSON with integer keys for ``frequency_map``.
    """
    logger.info(f"Loading residue data from {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalise the frequency map for easier downstream handling.
    if "frequency_map" in data:
        data["frequency_map"] = _ensure_int_keys(data["frequency_map"])
    else:
        logger.error("Residue JSON missing 'frequency_map'")
        raise KeyError("Residue JSON must contain a 'frequency_map' field")

    return data

def plot_bar_frequencies(data: Dict[str, Any], prime: int) -> None:
    """
    Produce a high‑resolution bar plot of observed residue frequencies.

    The plot contains:
    * Bars for each residue class ``0 … prime‑1``.
    * A horizontal line at the uniform expectation ``N / prime``.
    * A shaded band representing the theoretical error bound
      ``± φ·√N`` around the expectation.

    The figure is saved to ``results/plots/bar_{prime}_{N}.png`` with a DPI
    of 300.

    Parameters
    ----------
    data:
        The residue dataset dictionary as returned by :func:`load_residue_data`.
    prime:
        The prime modulus (must match ``data['prime_modulus']``; the function
        does not enforce this but logs a warning if they differ).
    """
    N = data["total_count"]
    freq_map = data["frequency_map"]
    if data.get("prime_modulus") != prime:
        logger.warning(
            f"Prime mismatch: dataset reports {data.get('prime_modulus')} but caller "
            f"requested {prime}. Continuing with caller's prime."
        )

    residues = list(range(prime))
    observed = [freq_map.get(r, 0) for r in residues]
    expected = N / prime

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(residues, observed, color="#1f77b4", edgecolor="black", width=0.6)

    # Uniform expectation line
    ax.axhline(expected, color="red", linestyle="--", linewidth=2,
               label=f"Uniform expectation (N/p = {expected:.2f})")

    # Theoretical error‑bound band
    bound = GOLDEN_RATIO * np.sqrt(N)
    lower = expected - bound
    upper = expected + bound
    ax.fill_between(
        residues,
        lower,
        upper,
        color="orange",
        alpha=0.3,
        label=f"Error bound ± φ·√N ≈ ±{bound:.2f}"
    )

    ax.set_xlabel("Residue class")
    ax.set_ylabel("Observed count")
    ax.set_title(f"Residue frequencies for prime {prime} (N={N})")
    ax.set_xticks(residues)
    ax.legend()

    output_path = paths.results("plots", f"bar_{prime}_{N}.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Bar plot saved to {output_path}")

def plot_residual_qq(data: Dict[str, Any], prime: int) -> None:
    """
    Produce a QQ‑plot of the chi‑square contributions (residuals).

    For each residue class we compute the contribution
    ``(O_i - E_i)^2 / E_i``.  Under the null hypothesis these contributions
    follow a chi‑square distribution with 1 degree of freedom.  The QQ‑plot
    compares the empirical quantiles to that theoretical distribution.

    The plot is saved to ``results/plots/qq_{prime}_{N}.png`` with a DPI
    of 300.

    Parameters
    ----------
    data:
        The residue dataset dictionary.
    prime:
        Prime modulus (again, only used for naming the output file).
    """
    N = data["total_count"]
    freq_map = data["frequency_map"]
    expected = N / prime

    contributions = [
        ((freq_map.get(r, 0) - expected) ** 2) / expected
        for r in range(prime)
    ]

    # QQ‑plot against chi2(df=1)
    fig, ax = plt.subplots(figsize=(8, 6))
    probplot(contributions, dist=chi2(df=1), plot=ax)
    ax.get_lines()[0].set_markerfacecolor("#1f77b4")  # style the points
    ax.set_title(f"QQ‑plot of chi‑square contributions (prime {prime}, N={N})")
    ax.set_xlabel("Theoretical quantiles")
    ax.set_ylabel("Ordered contributions")

    output_path = paths.results("plots", f"qq_{prime}_{N}.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"QQ‑plot saved to {output_path}")

def annotate_theoretical_bounds(prime: int, data: Dict[str, Any]) -> None:
    """
    Placeholder for future annotation logic.

    The current orchestrator calls this function after the two plots have
    been generated.  At present the bar plot already contains the
    theoretical error‑bound shading, and the QQ‑plot does not require an
    additional annotation.  This function therefore performs no action
    but is kept for API compatibility and future extensibility.

    Parameters
    ----------
    prime:
        Prime modulus (unused).
    data:
        Residue dataset (unused).
    """
    logger.debug("annotate_theoretical_bounds called – no additional action taken.")

def generate_visualization_report(prime: int, N: int, stats_path: str) -> None:
    """
    Write a short markdown report that links the generated figures and
    summarises the key statistics.

    The report is saved as ``results/reports/summary_{N}.md``.  It includes
    the paths to the bar plot and QQ‑plot, and a one‑line excerpt from the
    corresponding ``StatisticalResult`` JSON (chi‑square statistic,
    p‑value and test method).

    Parameters
    ----------
    prime:
        Prime modulus for which the report is generated.
    N:
        Upper bound used for the computation.
    stats_path:
        Path to the ``StatisticalResult`` JSON file produced by the
        statistics stage.
    """
    # Load the statistical result (we only need a few fields for the
    # summary).
    try:
        with open(stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
    except Exception as exc:
        logger.error(f"Failed to load statistical result from {stats_path}: {exc}")
        raise

    bar_path = paths.results("plots", f"bar_{prime}_{N}.png")
    qq_path = paths.results("plots", f"qq_{prime}_{N}.png")

    report_path = paths.results("reports", f"summary_{N}.md")
    with open(report_path, "w", encoding="utf-8") as out:
        out.write(f"# Residue‑distribution visualisation report\n\n")
        out.write(f"**Prime:** {prime}\n")
        out.write(f"**N:** {N}\n\n")
        out.write(f"## Generated figures\n")
        out.write(f"- Bar plot: `{bar_path}`\n")
        out.write(f"- QQ‑plot: `{qq_path}`\n\n")
        out.write("## Statistical summary\n")
        out.write(f"- Chi‑square statistic: {stats.get('chi_squared_statistic', 'N/A')}\n")
        out.write(f"- p‑value: {stats.get('p_value', 'N/A')}\n")
        out.write(f"- Test method: {stats.get('method', 'N/A')}\n")
    logger.info(f"Visualization report written to {report_path}")