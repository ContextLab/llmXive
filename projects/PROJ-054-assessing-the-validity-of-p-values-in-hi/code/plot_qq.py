"""
QQ-plot generation module.
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def load_pvalue_trajectories(
    trajectory_dir: str
) -> Dict[str, List[float]]:
    """
    Load p-value trajectories from a directory.

    Args:
        trajectory_dir: Path to directory containing trajectory JSON files

    Returns:
        Dictionary mapping seed to list of p-values.
    """
    data = {}
    path = Path(trajectory_dir)
    for file_path in path.glob("*.json"):
        with open(file_path, 'r') as f:
            content = json.load(f)
            seed = content.get("seed", file_path.stem)
            if "iterations" in content:
                pvals = []
                for iter_data in content["iterations"]:
                    pvals.extend(iter_data["p_values"])
                data[str(seed)] = pvals
            elif "p_values" in content:
                data[str(seed)] = content["p_values"]
    return data

def aggregate_pvalues(
    trajectories: Dict[str, List[float]]
) -> np.ndarray:
    """
    Aggregate p-values from multiple trajectories.

    Args:
        trajectories: Dictionary of seed -> p-values

    Returns:
        Flattened array of all p-values.
    """
    all_pvals = []
    for pvals in trajectories.values():
        all_pvals.extend(pvals)
    return np.array(all_pvals)

def generate_qq_plot(
    observed_pvalues: np.ndarray,
    reference: str = "uniform",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Generate a QQ-plot of observed p-values against a reference.

    Args:
        observed_pvalues: Array of observed p-values
        reference: Reference distribution ('uniform' or 'empirical')
        output_path: Optional path to save the figure

    Returns:
        Matplotlib Figure object.
    """
    observed_sorted = np.sort(observed_pvalues)
    n = len(observed_sorted)

    if reference == "uniform":
        # Theoretical quantiles for Uniform(0,1)
        theoretical_quantiles = (np.arange(1, n + 1) - 0.5) / n
    else:
        raise ValueError("Only 'uniform' reference is supported for now.")

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(theoretical_quantiles, observed_sorted, alpha=0.5, label="Observed")
    ax.plot([0, 1], [0, 1], 'r--', label="Expected (Uniform)")
    ax.set_xlabel("Theoretical Quantiles")
    ax.set_ylabel("Observed Quantiles")
    ax.set_title("QQ-Plot of P-Values")
    ax.legend()
    ax.grid(True)

    if output_path:
        fig.savefig(output_path, dpi=150)
        logger.info(f"QQ-plot saved to {output_path}")

    return fig

def main():
    """
    Entry point for QQ-plot generation.
    """
    logger.info("QQ-plot module loaded.")
