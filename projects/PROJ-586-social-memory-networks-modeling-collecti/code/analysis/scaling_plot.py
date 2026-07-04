"""
Scaling Plot Generator for User Story 3.

Generates a PDF plot of specialization index and retrieval efficiency vs. agent count,
with fitted power-law curves. Includes an explicit note about the limitation of
having only 3 data points for power-law reliability.

Output: projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# Ensure we can import from the project root if run as a script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from analysis.scaling import load_scaling_data


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """
    Power law function: y = a * x^b

    Args:
        x: Independent variable (agent count)
        a: Scaling coefficient
        b: Exponent

    Returns:
        y: Dependent variable (metric value)
    """
    return a * np.power(x, b)


def generate_scaling_plot_with_notes(
    input_csv: Path,
    output_pdf: Path,
    agent_counts: list[int] | None = None,
) -> None:
    """
    Generate scaling plot with power-law fits and explicit reliability notes.

    Args:
        input_csv: Path to CSV containing scaling data (agent_count, specialization_index, retrieval_efficiency)
        output_pdf: Path where the PDF plot will be written
        agent_counts: Optional list of agent counts to filter for (default: all in data)
    """
    # Load data
    df = load_scaling_data(input_csv)

    if df.empty:
        raise ValueError(f"No data found in {input_csv}")

    # Filter if specific agent counts requested
    if agent_counts is not None:
        df = df[df["agent_count"].isin(agent_counts)].reset_index(drop=True)

    if df.empty:
        raise ValueError(f"No matching data for agent counts {agent_counts} in {input_csv}")

    # Sort by agent count for consistent plotting
    df = df.sort_values("agent_count").reset_index(drop=True)

    agent_counts_arr = df["agent_count"].values
    spec_idx = df["specialization_index"].values
    ret_eff = df["retrieval_efficiency"].values

    # Prepare figure
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend for PDF generation
    import matplotlib.pyplot as plt

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Color map for clarity
    colors = {"specialization": "tab:blue", "retrieval": "tab:orange"}

    # Plot raw data points
    ax1.scatter(
        agent_counts_arr,
        spec_idx,
        color=colors["specialization"],
        label="Specialization Index (observed)",
        s=100,
        zorder=5,
    )
    ax2 = ax1.twinx()
    ax2.scatter(
        agent_counts_arr,
        ret_eff,
        color=colors["retrieval"],
        label="Retrieval Efficiency (observed)",
        s=100,
        zorder=5,
    )

    # Fit power laws (with warnings suppressed for potential fit issues)
    x_vals = np.linspace(min(agent_counts_arr), max(agent_counts_arr), 100)

    try:
        # Fit specialization
        popt_spec, _ = curve_fit(
            power_law,
            agent_counts_arr,
            spec_idx,
            p0=[1.0, -0.1],
            maxfev=1000,
        )
        ax1.plot(
            x_vals,
            power_law(x_vals, *popt_spec),
            color=colors["specialization"],
            linestyle="--",
            linewidth=2,
            label=f"Specialization Fit: y = {popt_spec[0]:.3f}x^{popt_spec[1]:.3f}",
        )
    except Exception as e:
        warnings.warn(f"Could not fit specialization power law: {e}")
        popt_spec = None

    try:
        # Fit retrieval
        popt_ret, _ = curve_fit(
            power_law,
            agent_counts_arr,
            ret_eff,
            p0=[1.0, -0.1],
            maxfev=1000,
        )
        ax2.plot(
            x_vals,
            power_law(x_vals, *popt_ret),
            color=colors["retrieval"],
            linestyle="--",
            linewidth=2,
            label=f"Retrieval Fit: y = {popt_ret[0]:.3f}x^{popt_ret[1]:.3f}",
        )
    except Exception as e:
        warnings.warn(f"Could not fit retrieval power law: {e}")
        popt_ret = None

    # Labels and titles
    ax1.set_xlabel("Number of Agents (N)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Specialization Index", color=colors["specialization"], fontsize=12)
    ax2.set_ylabel("Retrieval Efficiency", color=colors["retrieval"], fontsize=12)
    ax1.tick_params(axis="y", labelcolor=colors["specialization"])
    ax2.tick_params(axis="y", labelcolor=colors["retrieval"])
    plt.title("Scaling of Collective Remembering Metrics vs. Agent Count", fontsize=14, fontweight="bold")

    # Combine legends from both axes
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right")

    # Explicit note about 3 data points limitation
    note_text = (
        "NOTE: Only 3 data points (N=3, 5, 7) are available. "
        "Power-law fitting with n=3 is statistically unreliable and should be "
        "interpreted as a preliminary trend estimate only. More data points are required "
        "to robustly determine scaling exponents."
    )

    # Add text box with the note
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.8)
    ax1.text(
        0.5,
        -0.15,
        note_text,
        transform=ax1.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="center",
        bbox=props,
        fontfamily="monospace",
    )

    # Adjust layout to make room for the note
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)

    # Ensure output directory exists
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Save to PDF
    plt.savefig(output_pdf, dpi=300, format="pdf")
    plt.close(fig)

    print(f"Scaling plot saved to: {output_pdf}")


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits and reliability notes."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/scaling_results.csv"),
        help="Path to input CSV with scaling data",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/scaling_plot.pdf"),
        help="Path for output PDF",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=None,
        help="Comma-separated list of agent counts to include (e.g., 3,5,7)",
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    agent_counts = None
    if args.agents:
        try:
            agent_counts = [int(x.strip()) for x in args.agents.split(",")]
        except ValueError:
            print(f"Error: Invalid agent counts: {args.agents}")
            return 1

    # Resolve paths relative to project root if needed
    if not args.input.is_absolute():
        # Try relative to current working directory first, then script location
        if not args.input.exists():
            script_dir = Path(__file__).resolve().parent
            args.input = script_dir / args.input

    if not args.output.is_absolute():
        if not args.output.exists():
            script_dir = Path(__file__).resolve().parent
            args.output = script_dir.parent / args.output

    try:
        generate_scaling_plot_with_notes(args.input, args.output, agent_counts)
        return 0
    except Exception as e:
        print(f"Error generating scaling plot: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())