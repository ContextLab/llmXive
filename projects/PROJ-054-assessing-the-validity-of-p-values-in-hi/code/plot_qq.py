"""
QQ-Plot Generation for P-Value Distribution Analysis

This module implements the generation of Quantile-Quantile (QQ) plots to visually
inspect the distribution of p-values against a theoretical uniform distribution
and a permutation-based reference distribution.

FR-005: Implement QQ-plot generation for visual inspection.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_pvalue_trajectories(trajectory_dir: str) -> Dict[str, List[float]]:
    """
    Load p-value trajectories from JSON files.

    Args:
        trajectory_dir: Path to directory containing trajectory JSON files.

    Returns:
        Dictionary mapping seed identifiers to lists of p-values.
    """
    trajectory_path = Path(trajectory_dir)
    if not trajectory_path.exists():
        raise FileNotFoundError(f"Trajectory directory not found: {trajectory_dir}")

    trajectories = {}
    for json_file in trajectory_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Expecting structure: {"p_values": [...], "seed": ..., ...}
                if "p_values" in data:
                    seed_key = data.get("seed", json_file.stem)
                    trajectories[str(seed_key)] = data["p_values"]
                else:
                    logger.warning(f"Skipping {json_file}: missing 'p_values' key")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading {json_file}: {e}")
            continue

    if not trajectories:
        raise ValueError("No valid trajectory files found in the specified directory.")

    return trajectories


def aggregate_pvalues(trajectories: Dict[str, List[float]]) -> List[float]:
    """
    Aggregate p-values from all trajectories into a single list.

    Args:
        trajectories: Dictionary of seed -> p-value lists.

    Returns:
        Flattened list of all p-values.
    """
    all_pvalues = []
    for seed, pvals in trajectories.items():
        all_pvalues.extend(pvals)
    logger.info(f"Aggregated {len(all_pvalues)} p-values from {len(trajectories)} trajectories.")
    return all_pvalues


def generate_qq_plot(
    pvalues: List[float],
    reference_type: str = "uniform",
    output_path: Optional[str] = None,
    title: str = "P-Value QQ-Plot",
    show_plot: bool = False
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Generate a QQ-plot comparing observed p-values to a theoretical distribution.

    Args:
        pvalues: List of observed p-values.
        reference_type: Type of reference distribution ("uniform" or "permutation").
                        Note: For "permutation", the user must provide pre-computed
                        reference quantiles or this function assumes uniformity as
                        the null hypothesis for standard tests.
        output_path: If provided, saves the plot to this path.
        title: Plot title.
        show_plot: If True, displays the plot interactively.

    Returns:
        Tuple of (Figure, Axes) objects.
    """
    if not pvalues:
        raise ValueError("Input p-values list is empty.")

    # Sort observed p-values
    observed = np.sort(pvalues)
    n = len(observed)

    # Calculate theoretical quantiles (expected values for Uniform[0,1])
    # Using the rank-based approach: i / (n + 1)
    theoretical = (np.arange(1, n + 1)) / (n + 1)

    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 8))

    # Plot the diagonal line (perfect uniformity)
    ax.plot([0, 1], [0, 1], 'k--', label='Uniform Reference (y=x)', linewidth=2)

    # Plot the observed data
    ax.scatter(theoretical, observed, s=10, alpha=0.6, color='blue', label='Observed P-values')

    # Calculate KS statistic for annotation
    ks_stat, p_ks = stats.kstest(observed, 'uniform')
    annotation = f"KS Statistic: {ks_stat:.4f}\n(p-value: {p_ks:.4f})"
    ax.text(0.05, 0.95, annotation, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_xlabel("Theoretical Quantiles (Uniform)")
    ax.set_ylabel("Observed P-values")
    ax.set_title(title)
    ax.legend(loc="upper left")
    ax.grid(True, linestyle=':', alpha=0.6)

    # Set limits to ensure 0-1 range is visible
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"QQ-plot saved to {output_path}")

    if show_plot:
        plt.show()

    return fig, ax


def main():
    """
    Main entry point for generating QQ-plots from trajectory data.

    Usage:
        python code/plot_qq.py --trajectory_dir data/synthetic/trajectories --output figures/qq_plot.png
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate QQ-plots for p-value analysis.")
    parser.add_argument(
        "--trajectory_dir",
        type=str,
        default="data/synthetic/trajectories",
        help="Directory containing p-value trajectory JSON files."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="figures/qq_plot.png",
        help="Path to save the output QQ-plot."
    )
    parser.add_argument(
        "--reference",
        type=str,
        choices=["uniform", "permutation"],
        default="uniform",
        help="Reference distribution type."
    )
    parser.add_argument(
        "--title",
        type=str,
        default="P-Value Distribution QQ-Plot",
        help="Custom title for the plot."
    )

    args = parser.parse_args()

    try:
        # Load data
        logger.info(f"Loading trajectories from {args.trajectory_dir}...")
        trajectories = load_pvalue_trajectories(args.trajectory_dir)

        # Aggregate
        all_pvalues = aggregate_pvalues(trajectories)

        # Generate plot
        logger.info("Generating QQ-plot...")
        fig, ax = generate_qq_plot(
            pvalues=all_pvalues,
            reference_type=args.reference,
            output_path=args.output,
            title=args.title
        )

        logger.info("QQ-plot generation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during QQ-plot generation: {e}")
        raise


if __name__ == "__main__":
    main()