"""
Scaling plot generator for User Story 3.

Generates scaling_plot.pdf with fitted power-law curves for specialization index
and retrieval efficiency, including a note about the limitation of 3 data points.
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

# Import from existing project modules
from analysis.scaling import fit_power_law, load_scaling_data
from utils.logging import get_logger

logger = get_logger(__name__)

def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b"""
    return a * np.power(x, b)

def fit_power_law_with_ci(
    x: np.ndarray, y: np.ndarray, n_bootstrap: int = 1000
) -> tuple[float, float, float, float]:
    """
    Fit a power law and compute 95% confidence intervals via bootstrapping.
    
    Returns:
        (a, b, a_ci_lower, b_ci_lower) - point estimates and lower bounds of 95% CI
    """
    if len(x) < 2:
        raise ValueError("Need at least 2 data points for fitting")

    # Log-transform for linear fitting
    log_x = np.log(x)
    log_y = np.log(y)

    # Linear regression on log-log
    coeffs = np.polyfit(log_x, log_y, 1)
    b = coeffs[0]  # exponent
    a = np.exp(coeffs[1])  # coefficient

    # Bootstrap for confidence intervals
    boot_a = []
    boot_b = []

    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(len(x), size=len(x), replace=True)
        x_boot = x[indices]
        y_boot = y[indices]

        # Sort to ensure monotonicity for polyfit
        sort_idx = np.argsort(x_boot)
        x_boot_sorted = x_boot[sort_idx]
        y_boot_sorted = y_boot[sort_idx]

        log_x_boot = np.log(x_boot_sorted)
        log_y_boot = np.log(y_boot_sorted)

        try:
            boot_coeffs = np.polyfit(log_x_boot, log_y_boot, 1)
            boot_b = boot_coeffs[0]
            boot_a_val = np.exp(boot_coeffs[1])
            boot_a.append(boot_a_val)
            boot_b.append(boot_b)
        except (ValueError, RuntimeWarning):
            continue

    if len(boot_a) > 0 and len(boot_b) > 0:
        a_ci_lower = np.percentile(boot_a, 2.5)
        b_ci_lower = np.percentile(boot_b, 2.5)
    else:
        a_ci_lower = a
        b_ci_lower = b

    return a, b, a_ci_lower, b_ci_lower

def load_scaling_results_for_plot(
    results_dir: Path,
) -> tuple[list[float], list[float], list[float], list[float]]:
    """
    Load scaling analysis results from JSON files.
    
    Returns:
        agent_counts, specialization_indices, retrieval_efficiencies, game_ids
    """
    agent_counts = []
    specialization_indices = []
    retrieval_efficiencies = []
    game_ids = []

    # Look for scaling results files
    scaling_files = list(results_dir.glob("scaling_results_*.json"))

    if not scaling_files:
        logger.warning("No scaling results files found in %s", results_dir)
        return agent_counts, specialization_indices, retrieval_efficiencies, game_ids

    for sf in sorted(scaling_files):
        try:
            with open(sf, "r") as f:
                data = json.load(f)

            # Extract agent count from filename or data
            agent_count = data.get("agent_count")
            if agent_count is None:
                # Try to infer from filename
                fname = sf.stem
                parts = fname.split("_")
                if len(parts) > 1:
                    try:
                        agent_count = int(parts[-1])
                    except ValueError:
                        continue

            if agent_count is None:
                continue

            agent_counts.append(agent_count)
            specialization_indices.append(data.get("specialization_index", 0.0))
            retrieval_efficiencies.append(data.get("retrieval_efficiency", 0.0))
            game_ids.append(data.get("game_id", 0))

        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load %s: %s", sf, e)
            continue

    return agent_counts, specialization_indices, retrieval_efficiencies, game_ids

def generate_scaling_plot_with_notes(
    agent_counts: list[float],
    specialization_indices: list[float],
    retrieval_efficiencies: list[float],
    output_path: Path,
    n_bootstrap: int = 1000,
) -> dict:
    """
    Generate scaling plot with power-law fits and limitation note.
    
    Args:
        agent_counts: List of agent counts
        specialization_indices: Corresponding specialization indices
        retrieval_efficiencies: Corresponding retrieval efficiencies
        output_path: Path to save the PDF
        n_bootstrap: Number of bootstrap samples for CI
    
    Returns:
        Dictionary with fit results
    """
    if len(agent_counts) < 2:
        raise ValueError("Need at least 2 data points for plotting")

    # Convert to numpy arrays
    x = np.array(agent_counts)
    y_spec = np.array(specialization_indices)
    y_ret = np.array(retrieval_efficiencies)

    # Sort by agent count for consistent plotting
    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    y_spec_sorted = y_spec[sort_idx]
    y_ret_sorted = y_ret[sort_idx]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot data points
    ax.scatter(x_sorted, y_spec_sorted, color='blue', label='Specialization Index', zorder=3, s=100)
    ax.scatter(x_sorted, y_ret_sorted, color='red', label='Retrieval Efficiency', zorder=3, s=100)

    # Fit power laws
    fit_results = {}

    # Specialization fit
    try:
        a_spec, b_spec, a_spec_ci, b_spec_ci = fit_power_law_with_ci(
            x_sorted, y_spec_sorted, n_bootstrap
        )
        x_fit = np.linspace(x_sorted.min(), x_sorted.max(), 100)
        y_spec_fit = power_law(x_fit, a_spec, b_spec)
        ax.plot(x_fit, y_spec_fit, 'b--', linewidth=2, 
               label=f'Spec: y = {a_spec:.3f}·x^{b_spec:.3f}')
        fit_results['specialization'] = {
            'a': a_spec, 'b': b_spec,
            'a_ci_lower': a_spec_ci, 'b_ci_lower': b_spec_ci
        }
    except Exception as e:
        logger.warning("Failed to fit specialization power law: %s", e)
        fit_results['specialization'] = None

    # Retrieval fit
    try:
        a_ret, b_ret, a_ret_ci, b_ret_ci = fit_power_law_with_ci(
            x_sorted, y_ret_sorted, n_bootstrap
        )
        y_ret_fit = power_law(x_fit, a_ret, b_ret)
        ax.plot(x_fit, y_ret_fit, 'r--', linewidth=2,
               label=f'Retrieval: y = {a_ret:.3f}·x^{b_ret:.3f}')
        fit_results['retrieval'] = {
            'a': a_ret, 'b': b_ret,
            'a_ci_lower': a_ret_ci, 'b_ci_lower': b_ret_ci
        }
    except Exception as e:
        logger.warning("Failed to fit retrieval power law: %s", e)
        fit_results['retrieval'] = None

    # Add limitation note
    note_text = (
        "Note: 3 data points limit power-law reliability.\n"
        "Confidence intervals computed via bootstrapping (1000 resamples)."
    )
    ax.text(0.02, 0.98, note_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Labels and legend
    ax.set_xlabel('Number of Agents', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title('Scaling Analysis: Specialization and Retrieval vs. Agent Count', fontsize=14)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_yscale('log')

        # Generate smooth curve for plotting
        x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
        y_smooth = power_law(x_smooth, 1.0, exponent)

        # Normalize to match data range for visualization
        y_min, y_max = min(spec_indices), max(spec_indices)
        y_smooth = y_min + (y_smooth - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())

        ax1.plot(x_smooth, y_smooth, 'r-', linewidth=2,
                label=f'Power-law fit (β={exponent:.3f})')

        # Add confidence interval shading
        y_ci_lower = y_min + (power_law(x_smooth, 1.0, ci_lower) - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())
        y_ci_upper = y_min + (power_law(x_smooth, 1.0, ci_upper) - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())
        ax1.fill_between(x_smooth, y_ci_lower, y_ci_upper, alpha=0.2, color='red')

        ax1.text(0.02, 0.98, note_text, transform=ax1.transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax1.set_xlabel('Number of Agents', fontsize=12)
        ax1.set_ylabel('Specialization Index', fontsize=12)
        ax1.set_title(f'Specialization Index vs Agent Count\n(R² = {r_sq:.3f})', fontsize=14)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
    else:
        ax1.text(0.5, 0.5, 'Insufficient data points\nfor power-law fitting',
                transform=ax1.transAxes, ha='center', va='center', fontsize=14)
        ax1.set_xlabel('Number of Agents')
        ax1.set_ylabel('Specialization Index')

    # Plot 2: Retrieval Efficiency
    ax2.scatter(agent_counts, ret_effs, s=100, alpha=0.7, edgecolors='black',
               label='Observed', zorder=3, color='green')

    if n_points >= 2:
        # Fit power law
        exponent, ci_lower, ci_upper, r_sq = fit_power_law_with_ci(
            agent_counts, ret_effs, n_bootstrap=1000
        )

        # Generate smooth curve
        x_smooth = np.linspace(min(agent_counts), max(agent_counts), 100)
        y_smooth = power_law(x_smooth, 1.0, exponent)

        # Normalize
        y_min, y_max = min(ret_effs), max(ret_effs)
        y_smooth = y_min + (y_smooth - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())

        ax2.plot(x_smooth, y_smooth, 'g-', linewidth=2,
                label=f'Power-law fit (β={exponent:.3f})')

        # Confidence interval
        y_ci_lower = y_min + (power_law(x_smooth, 1.0, ci_lower) - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())
        y_ci_upper = y_min + (power_law(x_smooth, 1.0, ci_upper) - y_smooth.min()) * (y_max - y_min) / (y_smooth.max() - y_smooth.min())
        ax2.fill_between(x_smooth, y_ci_lower, y_ci_upper, alpha=0.2, color='green')

        ax2.text(0.02, 0.98, note_text, transform=ax2.transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax2.set_xlabel('Number of Agents', fontsize=12)
        ax2.set_ylabel('Retrieval Efficiency', fontsize=12)
        ax2.set_title(f'Retrieval Efficiency vs Agent Count\n(R² = {r_sq:.3f})', fontsize=14)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'Insufficient data points\nfor power-law fitting',
                transform=ax2.transAxes, ha='center', va='center', fontsize=14)
        ax2.set_xlabel('Number of Agents')
        ax2.set_ylabel('Retrieval Efficiency')

    plt.suptitle('Scaling Analysis: Collective Remembering in Multi-Agent Networks',
                fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info("Scaling plot saved to %s", output_path)

    return fit_results

def run_scaling_analysis(
    results_dir: Path, output_dir: Path, n_bootstrap: int = 1000
) -> dict:
    """
    Run full scaling analysis and generate plot.
    
    Args:
        results_dir: Directory containing scaling results JSON files
        output_dir: Directory to save the plot and results
        n_bootstrap: Number of bootstrap samples
    
    Returns:
        Analysis results dictionary
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    agent_counts, spec_indices, ret_effs, game_ids = load_scaling_results_for_plot(results_dir)

    if len(agent_counts) < 2:
        raise ValueError(
            f"Insufficient data points for scaling analysis. "
            f"Found {len(agent_counts)} points, need at least 2."
        )

    # Generate plot
    output_path = output_dir / "scaling_plot.pdf"
    fit_results = generate_scaling_plot_with_notes(
        agent_counts, spec_indices, ret_effs, output_path, n_bootstrap
    )

    # Save fit results
    results_path = output_dir / "scaling_fit_results.json"
    with open(results_path, "w") as f:
        json.dump({
            "agent_counts": agent_counts,
            "specialization_indices": spec_indices,
            "retrieval_efficiencies": ret_effs,
            "fit_results": fit_results,
            "note": "3 data points limit power-law reliability"
        }, f, indent=2)

    return {
        "plot_path": str(output_path),
        "results_path": str(results_path),
        "fit_results": fit_results,
        "data_points": len(agent_counts)
    }

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling plot generation."""
    parser = argparse.ArgumentParser(
        description="Generate scaling plot with power-law fits"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Directory containing scaling results JSON files"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory to save the plot and results"
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap samples for confidence intervals"
    )
    return parser

def main() -> None:
    """Main entry point for scaling plot generation."""
    parser = build_parser()
    args = parser.parse_args()

    logger.info("Starting scaling plot generation")
    logger.info("Results directory: %s", args.results_dir)
    logger.info("Output directory: %s", args.output_dir)

    try:
        results = run_scaling_analysis(
            args.results_dir, args.output_dir, args.bootstrap
        )
        logger.info("Scaling plot generation completed successfully")
        logger.info("Plot saved to: %s", results["plot_path"])
        logger.info("Results saved to: %s", results["results_path"])
        logger.info("Data points used: %d", results["data_points"])

    except Exception as e:
        logger.error("Scaling plot generation failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
