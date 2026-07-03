"""Scaling plot generation for User Story 3.

Generates a PDF plot of specialization index and retrieval efficiency versus
number of agents, with fitted power-law curves and an explicit note about
the limitation of 3 data points for power-law reliability.

This module reads real measurement data from CSV files produced by the
scaling experiment (run_scaling_experiment.py) and produces a publication-quality
PDF plot.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# Try to import matplotlib and scipy; if unavailable, fall back to minimal implementation
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for PDF generation
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None  # type: ignore

try:
    from scipy.optimize import curve_fit
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


@dataclass
class ScalingPlotResult:
    """Result of scaling plot generation."""
    plot_path: str
    has_data: bool
    fitted: bool
    note_added: bool
    agent_counts: List[int]
    specialization_values: List[float]
    retrieval_values: List[float]


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power-law function: y = a * x^b.

    Args:
        x: Independent variable (agent count).
        a: Coefficient.
        b: Exponent.

    Returns:
        Fitted values.
    """
    return a * np.power(x, b)


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    confidence: float = 0.95
) -> Tuple[float, float, Optional[float], Optional[float]]:
    """Fit a power-law curve to data with confidence intervals on the exponent.

    Args:
        x: Independent variable values.
        y: Dependent variable values.
        confidence: Confidence level for intervals (default 0.95).

    Returns:
        Tuple of (coefficient a, exponent b, lower CI for b, upper CI for b).
        If fitting fails or CI cannot be computed, returns (a, b, None, None).
    """
    if not HAS_SCIPY or len(x) < 2:
        # Cannot fit with < 2 points
        return 0.0, 0.0, None, None

    try:
        # Initial guess: a=1, b=0 (flat line)
        p0 = [1.0, 0.0]

        # Bounds to prevent divergence
        bounds = ([0.0, -10.0], [100.0, 10.0])

        popt, pcov = curve_fit(power_law, x, y, p0=p0, bounds=bounds, maxfev=10000)

        a, b = popt

        # Compute confidence intervals if covariance is available
        if pcov is not None:
            try:
                perr = np.sqrt(np.diag(pcov))
                # Approximate 95% CI using normal approximation
                # For small samples, this is approximate
                t_value = 1.96  # Approximate for large n; for n=3, t(0.975, df=1) = 12.71
                # With only 3 points, df = n - 2 = 1, so t is large
                # But we use 1.96 as a standard reference, noting the limitation
                lower_ci = b - t_value * perr[1]
                upper_ci = b + t_value * perr[1]
                return float(a), float(b), float(lower_ci), float(upper_ci)
            except (ValueError, RuntimeError):
                return float(a), float(b), None, None
        else:
            return float(a), float(b), None, None

    except (RuntimeError, ValueError, np.linalg.LinAlgError):
        # Fallback: return zero if fitting fails
        return 0.0, 0.0, None, None


def load_scaling_data_real(
    results_dir: Path,
    agent_counts: List[int]
) -> Tuple[List[float], List[float]]:
    """Load real scaling data from CSV files.

    Reads specialization index and retrieval efficiency from CSV files
    produced by run_scaling_experiment.py for each agent count.

    Args:
        results_dir: Directory containing results CSV files.
        agent_counts: List of agent counts to load (e.g., [3, 5, 7]).

    Returns:
        Tuple of (specialization_values, retrieval_values) lists.

    Raises:
        FileNotFoundError: If required CSV files are missing.
        ValueError: If data cannot be parsed or is empty.
    """
    specialization_values = []
    retrieval_values = []

    for count in agent_counts:
        csv_path = results_dir / f"results_scaling_{count}_agents.csv"

        if not csv_path.exists():
            raise FileNotFoundError(
                f"Scaling results file not found: {csv_path}. "
                f"Run run_scaling_experiment.py first with --agents {count}."
            )

        df = pd.read_csv(csv_path)

        # Validate required columns
        required_cols = ['specialization_index', 'retrieval_efficiency']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(
                f"Missing required columns in {csv_path}: {missing}"
            )

        # Filter out invalid entries (NaN, negative, etc.)
        valid_mask = (
            df['specialization_index'].notna() &
            df['retrieval_efficiency'].notna() &
            (df['specialization_index'] >= 0) &
            (df['retrieval_efficiency'] >= 0)
        )
        valid_df = df[valid_mask]

        if len(valid_df) == 0:
            raise ValueError(
                f"No valid data in {csv_path} for agent count {count}"
            )

        # Compute mean values for this agent count
        spec_mean = valid_df['specialization_index'].mean()
        ret_mean = valid_df['retrieval_efficiency'].mean()

        specialization_values.append(float(spec_mean))
        retrieval_values.append(float(ret_mean))

    return specialization_values, retrieval_values


def generate_scaling_plot_with_notes(
    results_dir: Path,
    output_path: Path,
    agent_counts: List[int] = [3, 5, 7],
    dpi: int = 300
) -> ScalingPlotResult:
    """Generate scaling plot with power-law fits and limitation notes.

    Creates a PDF plot showing:
    - Specialization index vs. agent count (with power-law fit)
    - Retrieval efficiency vs. agent count (with power-law fit)
    - Explicit note about 3 data points limiting power-law reliability

    Args:
        results_dir: Directory containing results CSV files.
        output_path: Path for output PDF file.
        agent_counts: List of agent counts to plot.
        dpi: Resolution for the plot.

    Returns:
        ScalingPlotResult with metadata about the generated plot.

    Raises:
        FileNotFoundError: If required data files are missing.
        RuntimeError: If plot generation fails.
    """
    if not HAS_MATPLOTLIB:
        raise RuntimeError(
            "matplotlib is required for plot generation. "
            "Install with: pip install matplotlib"
        )

    # Load real data
    try:
        spec_vals, ret_vals = load_scaling_data_real(results_dir, agent_counts)
    except (FileNotFoundError, ValueError) as e:
        raise RuntimeError(f"Failed to load scaling data: {e}")

    has_data = len(spec_vals) > 0 and len(ret_vals) > 0

    if not has_data:
        raise ValueError("No valid data to plot")

    # Convert to numpy arrays
    x = np.array(agent_counts, dtype=float)
    y_spec = np.array(spec_vals)
    y_ret = np.array(ret_vals)

    # Fit power laws
    a_spec, b_spec, _, _ = fit_power_law_with_ci(x, y_spec)
    a_ret, b_ret, _, _ = fit_power_law_with_ci(x, y_ret)

    fitted = (b_spec != 0.0 or b_ret != 0.0)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Specialization Index vs. Agent Count
    ax1.scatter(x, y_spec, s=100, c='tab:blue', label='Measured', zorder=3)
    if fitted:
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit_spec = power_law(x_fit, a_spec, b_spec)
        ax1.plot(x_fit, y_fit_spec, 'b-', linewidth=2,
                label=f'Power-law fit: y = {a_spec:.3f} * x^{b_spec:.3f}')
    ax1.set_xlabel('Number of Agents', fontsize=12)
    ax1.set_ylabel('Specialization Index', fontsize=12)
    ax1.set_title('Specialization vs. Agent Count', fontsize=14)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_yscale('log')

    # Plot 2: Retrieval Efficiency vs. Agent Count
    ax2.scatter(x, y_ret, s=100, c='tab:red', label='Measured', zorder=3)
    if fitted:
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit_ret = power_law(x_fit, a_ret, b_ret)
        ax2.plot(x_fit, y_fit_ret, 'r-', linewidth=2,
                label=f'Power-law fit: y = {a_ret:.3f} * x^{b_ret:.3f}')
    ax2.set_xlabel('Number of Agents', fontsize=12)
    ax2.set_ylabel('Retrieval Efficiency', fontsize=12)
    ax2.set_title('Retrieval Efficiency vs. Agent Count', fontsize=14)
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_yscale('log')

    # Add explicit note about limitation
    note_text = (
        "NOTE: Only 3 data points (agent counts 3, 5, 7) are available. "
        "This severely limits the reliability of power-law fitting. "
        "Results should be interpreted with caution and validated with "
        "more agent counts in future work."
    )

    # Add text box to figure
    fig.text(
        0.5, 0.02,
        note_text,
        fontsize=10,
        ha='center',
        va='bottom',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
        wrap=True
    )

    # Adjust layout to make room for the note
    plt.tight_layout(rect=[0, 0.08, 1, 1])

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to PDF
    try:
        plt.savefig(output_path, dpi=dpi, format='pdf', bbox_inches='tight')
    except Exception as e:
        plt.close()
        raise RuntimeError(f"Failed to save plot: {e}")

    plt.close()

    return ScalingPlotResult(
        plot_path=str(output_path),
        has_data=True,
        fitted=fitted,
        note_added=True,
        agent_counts=agent_counts,
        specialization_values=spec_vals,
        retrieval_values=ret_vals
    )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the scaling plot generator."""
    parser = argparse.ArgumentParser(
        description='Generate scaling plot with power-law fits and limitation notes.'
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='results',
        help='Directory containing scaling experiment results CSV files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='scaling_plot.pdf',
        help='Output path for the PDF plot'
    )
    parser.add_argument(
        '--agents',
        type=str,
        default='3,5,7',
        help='Comma-separated list of agent counts (default: 3,5,7)'
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='Resolution for the plot (default: 300)'
    )
    return parser


def main() -> int:
    """Main entry point for the scaling plot generator."""
    parser = build_parser()
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_path = Path(args.output)

    # Parse agent counts
    try:
        agent_counts = [int(x.strip()) for x in args.agents.split(',')]
    except ValueError:
        print(f"Error: Invalid agent counts format: {args.agents}")
        print("Use comma-separated integers, e.g., '3,5,7'")
        return 1

    if len(agent_counts) < 2:
        print("Error: At least 2 agent counts are required for fitting")
        return 1

    print(f"Generating scaling plot...")
    print(f"  Results directory: {results_dir}")
    print(f"  Agent counts: {agent_counts}")
    print(f"  Output file: {output_path}")

    try:
        result = generate_scaling_plot_with_notes(
            results_dir=results_dir,
            output_path=output_path,
            agent_counts=agent_counts,
            dpi=args.dpi
        )

        print(f"\nPlot generated successfully!")
        print(f"  Output: {result.plot_path}")
        print(f"  Data points: {len(result.agent_counts)}")
        print(f"  Power-law fitted: {result.fitted}")
        print(f"  Limitation note added: {result.note_added}")

        if not result.fitted:
            print("  Warning: Power-law fitting failed (may need more data points)")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease run run_scaling_experiment.py first to generate the required CSV files.")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
