"""
Visualization module for Euler's Totient residue distribution analysis.

Provides functions to generate bar plots, QQ-plots, and annotate theoretical bounds.
Implements deterministic random seed pinning for reproducible stochastic visual elements.
"""

import os
import json
import random
import logging
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global seed state for reproducibility
_seed_pinned = False
_current_seed: Optional[int] = None

# Constants
DEFAULT_DPI = 300
FIGURE_SIZE = (10, 6)
FONT_SIZE = 12


def pin_random_seed(seed: Optional[int] = None) -> int:
    """
    Initialize and pin the random seed for all stochastic operations in this module.
    
    Args:
        seed: The seed value to use. If None, uses the global seed from config.
    
    Returns:
        The seed value that was pinned.
    
    Raises:
        ValueError: If the seed has already been pinned with a different value.
    """
    global _seed_pinned, _current_seed
    
    if seed is None:
        # Try to load from environment or use default
        seed = int(os.environ.get('RANDOM_SEED', 42))
    
    if _seed_pinned and _current_seed != seed:
        raise ValueError(
            f"Random seed already pinned to {_current_seed}, cannot change to {seed}"
        )
    
    _current_seed = seed
    _seed_pinned = True
    
    # Pin seeds for all relevant libraries
    random.seed(seed)
    np.random.seed(seed)
    plt.rcParams['figure.dpi'] = DEFAULT_DPI
    
    logger.info(f"Random seed pinned to {seed} for visualize module")
    return seed


def is_seed_pinned() -> bool:
    """
    Check if the random seed has been pinned for this module.
    
    Returns:
        True if seed is pinned, False otherwise.
    """
    return _seed_pinned


def get_current_seed() -> Optional[int]:
    """
    Get the current pinned seed value.
    
    Returns:
        The current seed value, or None if not pinned.
    """
    return _current_seed


def load_residue_data(prime: int, N: int) -> Dict[str, Any]:
    """
    Load residue counts from the raw data file.
    
    Args:
        prime: The prime modulus used for residue calculation.
        N: The upper bound of the range [1, N].
    
    Returns:
        Dictionary containing residue counts and metadata.
    
    Raises:
        FileNotFoundError: If the data file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    filepath = f"data/raw/residues_{prime}_{N}.json"
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Residue data file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded residue data for p={prime}, N={N} from {filepath}")
    return data


def plot_bar_frequencies(residue_counts: Dict[int, int], prime: int, 
                          N: int, output_path: Optional[str] = None) -> plt.Figure:
    """
    Create a bar plot showing the distribution of residue counts modulo prime.
    
    Args:
        residue_counts: Dictionary mapping residue values to their counts.
        prime: The prime modulus.
        N: The upper bound of the range [1, N].
        output_path: Optional path to save the plot.
    
    Returns:
        The matplotlib Figure object.
    """
    # Ensure seed is pinned for reproducibility of any stochastic elements
    if not is_seed_pinned():
        logger.warning("Random seed not pinned. Using default for reproducibility.")
        pin_random_seed()
    
    residues = sorted(residue_counts.keys())
    counts = [residue_counts[r] for r in residues]
    expected_uniform = N / prime
    
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    
    # Create bar plot
    bars = ax.bar(residues, counts, color='skyblue', edgecolor='navy', alpha=0.7, label='Observed')
    
    # Add uniform expectation line
    ax.axhline(y=expected_uniform, color='red', linestyle='--', linewidth=2, 
              label=f'Uniform Expectation (N/{prime} = {expected_uniform:.2f})')
    
    # Formatting
    ax.set_xlabel('Residue Value (mod {prime})', fontsize=FONT_SIZE)
    ax.set_ylabel('Count', fontsize=FONT_SIZE)
    ax.set_title(f'Distribution of φ(n) mod {prime} for n ∈ [1, {N}]', fontsize=FONT_SIZE + 2)
    ax.legend(loc='best', fontsize=FONT_SIZE - 2)
    ax.grid(axis='y', alpha=0.3)
    
    # Ensure integer ticks for residue values
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Add count labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{count}', ha='center', va='bottom', fontsize=FONT_SIZE - 2)
    
    plt.tight_layout()
    
    if output_path:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=DEFAULT_DPI, bbox_inches='tight')
        logger.info(f"Bar plot saved to {output_path}")
    
    return fig


def plot_residual_qq(residuals: List[float], output_path: Optional[str] = None) -> plt.Figure:
    """
    Create a QQ-plot for chi-squared residuals.
    
    Args:
        residuals: List of residual values.
        output_path: Optional path to save the plot.
    
    Returns:
        The matplotlib Figure object.
    """
    if not is_seed_pinned():
        logger.warning("Random seed not pinned. Using default for reproducibility.")
        pin_random_seed()
    
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    
    # Sort residuals
    sorted_residuals = sorted(residuals)
    n = len(sorted_residuals)
    
    # Calculate theoretical quantiles (assuming normal distribution)
    from scipy.stats import norm
    theoretical_quantiles = norm.ppf([(i + 0.5) / n for i in range(n)])
    
    # Plot QQ-plot
    ax.scatter(theoretical_quantiles, sorted_residuals, alpha=0.6, edgecolors='k')
    
    # Add reference line
    if n > 0:
        min_val, max_val = min(theoretical_quantiles), max(theoretical_quantiles)
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', label='Reference Line')
    
    ax.set_xlabel('Theoretical Quantiles (Normal)', fontsize=FONT_SIZE)
    ax.set_ylabel('Sample Quantiles', fontsize=FONT_SIZE)
    ax.set_title('QQ-Plot of Residuals', fontsize=FONT_SIZE + 2)
    ax.legend(loc='best', fontsize=FONT_SIZE - 2)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=DEFAULT_DPI, bbox_inches='tight')
        logger.info(f"QQ-plot saved to {output_path}")
    
    return fig


def annotate_theoretical_bounds(fig: plt.Figure, prime: int, N: int, 
                                observed_counts: Dict[int, int]) -> plt.Figure:
    """
    Annotate the plot with theoretical error bounds.
    
    Implements error bounds from literature:
    1. Lebowitz-Lockard bound: E_bound = C * N^(1 - 1/φ(p))
    2. Pollack & Roy bound: O(N * exp(-c * sqrt(log N)))
    
    Args:
        fig: The matplotlib Figure to annotate.
        prime: The prime modulus.
        N: The upper bound of the range.
        observed_counts: Dictionary of observed residue counts.
    
    Returns:
        The annotated Figure object.
    """
    if not is_seed_pinned():
        logger.warning("Random seed not pinned. Using default for reproducibility.")
        pin_random_seed()
    
    # Constants for error bounds
    C_LEBOWITZ = 1.0  # Placeholder constant
    C_POLLACK = 1.0   # Placeholder constant
    
    # Calculate φ(p) for prime p
    phi_p = prime - 1
    
    # Lebowitz-Lockard bound
    lebowitz_bound = C_LEBOWITZ * (N ** (1 - 1/phi_p))
    
    # Pollack & Roy bound
    import math
    pollack_bound = N * math.exp(-0.5 * math.sqrt(math.log(N))) if N > 1 else 0
    
    # Get maximum observed deviation from uniform
    expected_uniform = N / prime
    max_deviation = max(abs(count - expected_uniform) for count in observed_counts.values())
    
    ax = fig.gca()
    
    # Add annotation text
    annotation_text = (
        f"Theoretical Error Bounds:\n"
        f"  Lebowitz-Lockard: ~{lebowitz_bound:.2f}\n"
        f"  Pollack & Roy: ~{pollack_bound:.2f}\n"
        f"  Max Observed Deviation: {max_deviation:.2f}"
    )
    
    ax.text(0.02, 0.98, annotation_text, transform=ax.transAxes, 
           fontsize=FONT_SIZE - 2, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    logger.info(f"Annotated theoretical bounds for p={prime}, N={N}")
    return fig


def generate_visualization_report(prime: int, N: int, output_dir: str) -> Dict[str, str]:
    """
    Generate all visualization artifacts for a given prime and N.
    
    Args:
        prime: The prime modulus.
        N: The upper bound of the range.
        output_dir: Directory to save output files.
    
    Returns:
        Dictionary mapping artifact types to file paths.
    """
    # Ensure seed is pinned
    if not is_seed_pinned():
        pin_random_seed()
    
    # Load data
    data = load_residue_data(prime, N)
    residue_counts = data.get('residue_counts', {})
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    artifacts = {}
    
    # Generate bar plot
    bar_path = os.path.join(output_dir, f"bar_freq_p{prime}_N{N}.png")
    fig = plot_bar_frequencies(residue_counts, prime, N, output_path=bar_path)
    fig = annotate_theoretical_bounds(fig, prime, N, residue_counts)
    fig.savefig(bar_path, dpi=DEFAULT_DPI, bbox_inches='tight')
    artifacts['bar_plot'] = bar_path
    plt.close(fig)
    
    # Generate QQ-plot (using synthetic residuals for demonstration if needed)
    # In a full implementation, residuals would be computed from statistical analysis
    residuals = [count - (N / prime) for count in residue_counts.values()]
    qq_path = os.path.join(output_dir, f"qq_plot_p{prime}_N{N}.png")
    if residuals:
        fig = plot_residual_qq(residuals, output_path=qq_path)
        artifacts['qq_plot'] = qq_path
        plt.close(fig)
    
    logger.info(f"Generated visualization report for p={prime}, N={N}")
    return artifacts