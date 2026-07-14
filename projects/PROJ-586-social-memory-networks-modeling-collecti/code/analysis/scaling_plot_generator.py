"""Generate the scaling plot for User Story 3 (T030).

This script loads scaling results (specialization index and retrieval efficiency
vs. agent count), fits power-law curves, and generates a PDF plot with a
disclaimer about the limited number of data points.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Import existing functions from code/analysis/scaling.py
# We assume fit_power_law and load_scaling_data are available there.
# If they are not, we implement minimal versions here to satisfy the task.
try:
    from analysis.scaling import fit_power_law, load_scaling_data
except ImportError:
    # Fallback minimal implementations if not present
    def load_scaling_data(input_path: Path):
        """Load scaling results from a CSV file.

        Expected columns: agent_count, specialization_index, retrieval_efficiency
        """
        import csv
        data = {"agent_count": [], "specialization_index": [], "retrieval_efficiency": []}
        with open(input_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data["agent_count"].append(int(row["agent_count"]))
                data["specialization_index"].append(float(row["specialization_index"]))
                data["retrieval_efficiency"].append(float(row["retrieval_efficiency"]))
        return data

    def fit_power_law(x: np.ndarray, y: np.ndarray):
        """Fit y = a * x^b using log-log linear regression.

        Returns (a, b) and the fitted y values.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            log_x = np.log(x)
            log_y = np.log(y)
            # Simple linear regression: log_y = log_a + b * log_x
            # Using polyfit for simplicity
            coeffs = np.polyfit(log_x, log_y, 1)
            b = coeffs[0]
            log_a = coeffs[1]
            a = math.exp(log_a)
            y_fit = a * (x ** b)
            return a, b, y_fit


def generate_scaling_plot_with_notes(
    data: dict,
    output_path: Path,
    note_text: str = "3 data points limit power-law reliability",
):
    """Generate a PDF plot with power-law fits and a disclaimer note.

    Args:
        data: Dictionary with keys 'agent_count', 'specialization_index', 'retrieval_efficiency'.
        output_path: Path to the output PDF file.
        note_text: Text note to include on the plot.
    """
    agent_counts = np.array(data["agent_count"])
    spec_indices = np.array(data["specialization_index"])
    retrieval_effs = np.array(data["retrieval_efficiency"])

    # Sort by agent count for plotting
    sort_idx = np.argsort(agent_counts)
    agent_counts = agent_counts[sort_idx]
    spec_indices = spec_indices[sort_idx]
    retrieval_effs = retrieval_effs[sort_idx]

    # Fit power laws
    # Specialization
    a_spec, b_spec, y_spec_fit = fit_power_law(agent_counts, spec_indices)
    # Retrieval
    a_ret, b_ret, y_ret_fit = fit_power_law(agent_counts, retrieval_effs)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data points
    ax.plot(agent_counts, spec_indices, 'o-', label='Specialization Index', color='blue', alpha=0.7)
    ax.plot(agent_counts, retrieval_effs, 's-', label='Retrieval Efficiency', color='green', alpha=0.7)

    # Plot fitted curves (smooth)
    x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
    ax.plot(x_smooth, a_spec * (x_smooth ** b_spec), '--', color='blue', alpha=0.5, label=f'Spec Fit (b={b_spec:.2f})')
    ax.plot(x_smooth, a_ret * (x_smooth ** b_ret), '--', color='green', alpha=0.5, label=f'Ret Fit (b={b_ret:.2f})')

    ax.set_xlabel('Number of Agents')
    ax.set_ylabel('Metric Value')
    ax.set_title('Scaling of Collective Remembering Metrics')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add note about data point limitation
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.02, 0.98, note_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)

    # Save to PDF
    plt.tight_layout()
    plt.savefig(output_path, format='pdf')
    plt.close()
    print(f"Plot saved to {output_path}")


def run_scaling_analysis(input_csv: Path, output_pdf: Path):
    """Run the full scaling analysis and plot generation."""
    if not input_csv.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    data = load_scaling_data(input_csv)
    generate_scaling_plot_with_notes(data, output_pdf)


def build_parser():
    parser = argparse.ArgumentParser(description="Generate scaling plot for US-3")
    parser.add_argument("--input", type=Path, required=True, help="Input CSV with scaling results")
    parser.add_argument("--output", type=Path, required=True, help="Output PDF plot path")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    run_scaling_analysis(args.input, args.output)


if __name__ == "__main__":
    main()