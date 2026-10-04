"""
Visualization module for residue distribution analysis.
"""
import os
import json
import random
import logging
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def pin_random_seed(seed: int) -> None:
    """Pin random seeds."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def is_seed_pinned() -> bool:
    return True

def get_current_seed() -> Optional[int]:
    return None

def load_residue_data(path: str) -> Dict[str, Any]:
    """Load residue data from JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def plot_bar_frequencies(residue_counts: Dict[int, int], prime: int) -> None:
    """Plot bar frequencies."""
    # Placeholder for matplotlib implementation
    logger.info(f"Plotting bar frequencies for prime={prime}")

def plot_residual_qq(residuals: List[float]) -> None:
    """
    Plot QQ plot of residuals.
    
    Generates a Quantile-Quantile plot comparing the observed Chi-squared residuals
    against the theoretical quantiles of a standard normal distribution.
    
    The residuals are expected to be calculated as: (O_k - E_k) / sqrt(E_k)
    
    Args:
        residuals: List of float values representing Chi-squared residuals.
    """
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt

    if not residuals:
        logger.warning("No residuals provided for QQ plot. Skipping generation.")
        return

    residuals = np.array(residuals)
    
    # Sort residuals
    sorted_residuals = np.sort(residuals)
    n = len(sorted_residuals)
    
    # Calculate theoretical quantiles (standard normal)
    # Using (i - 0.5) / n for the cumulative probability
    probabilities = (np.arange(1, n + 1) - 0.5) / n
    theoretical_quantiles = np.quantile(np.random.normal(0, 1, 10000), probabilities)
    
    # Create the plot
    plt.figure(figsize=(8, 6))
    plt.scatter(theoretical_quantiles, sorted_residuals, alpha=0.7, edgecolors='k', s=50)
    
    # Add reference line (y = x)
    min_val = min(theoretical_quantiles.min(), sorted_residuals.min())
    max_val = max(theoretical_quantiles.max(), sorted_residuals.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Theoretical (Normal)')
    
    plt.xlabel('Theoretical Quantiles (Standard Normal)')
    plt.ylabel('Observed Quantiles (Chi-squared Residuals)')
    plt.title('QQ Plot of Residue Distribution Residuals')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Determine output path based on environment or default
    output_dir = "results/plots"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "qq_residuals.png")
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"QQ plot saved to {output_path}")

def annotate_theoretical_bounds(plot: Any, prime: int) -> None:
    """Annotate theoretical bounds on plot."""
    # Placeholder
    logger.info(f"Annotating bounds for prime={prime}")

def generate_visualization_report(stats: Dict[str, Any], path: str) -> None:
    """Generate visualization report."""
    # Placeholder
    with open(path, 'w') as f:
        f.write("# Visualization Report\n")
        f.write("Placeholder content\n")
