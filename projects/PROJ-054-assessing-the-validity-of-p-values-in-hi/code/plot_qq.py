"""
QQ-Plot generation for p-value distribution analysis (FR-005).

Generates visual comparison of observed p-values against the theoretical
uniform distribution and the permutation-based gold standard reference.
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import existing analysis functions
from analyze_pvalues import generate_permutation_reference, calculate_ks_statistic
from utils.exceptions import AnalysisError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_pvalue_trajectories(data_dir: str) -> Dict[str, Any]:
    """
    Load p-value trajectories from JSON files.
    
    Args:
        data_dir: Path to directory containing trajectory JSON files.
        
    Returns:
        Dictionary mapping seed to list of p-value arrays.
    """
    trajectories = {}
    traj_path = Path(data_dir) / "synthetic" / "trajectories"
    
    if not traj_path.exists():
        raise AnalysisError(f"Trajectory directory not found: {traj_path}")
        
    for json_file in traj_path.glob("*.json"):
        seed = json_file.stem
        with open(json_file, 'r') as f:
            data = json.load(f)
            # Assuming structure: {"p_values": [[...], [...], ...]}
            # where each inner list is p-values for one iteration
            if "p_values" in data:
                trajectories[seed] = data["p_values"]
            else:
                logger.warning(f"Skipping {json_file}: missing 'p_values' key")
                
    if not trajectories:
        raise AnalysisError(f"No valid trajectory files found in {traj_path}")
        
    return trajectories


def aggregate_pvalues(trajectories: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Aggregate p-values across all iterations and seeds.
    
    Args:
        trajectories: Dictionary of p-value lists per seed.
        
    Returns:
        Tuple of (observed_pvalues, seeds_used)
    """
    all_pvalues = []
    seeds = []
    
    for seed, pvalue_list in trajectories.items():
        for iteration_pvalues in pvalue_list:
            all_pvalues.extend(iteration_pvalues)
        seeds.append(seed)
        
    return np.array(all_pvalues), seeds


def generate_qq_plot(
    observed_pvalues: np.ndarray,
    permutation_pvalues: np.ndarray,
    output_path: str,
    title: str = "QQ-Plot: p-value Distribution Analysis",
    alpha: float = 0.05
) -> None:
    """
    Generate QQ-plot comparing observed p-values to theoretical uniform 
    and permutation-based gold standard.
    
    Args:
        observed_pvalues: Array of observed p-values from t-tests/F-tests.
        permutation_pvalues: Array of p-values from permutation test (gold standard).
        output_path: Path to save the plot.
        title: Plot title.
        alpha: Significance level for confidence bands.
    """
    if len(observed_pvalues) == 0 or len(permutation_pvalues) == 0:
        raise AnalysisError("Cannot generate QQ-plot: empty p-value arrays")
        
    # Sort p-values
    observed_sorted = np.sort(observed_pvalues)
    permutation_sorted = np.sort(permutation_pvalues)
    
    # Theoretical quantiles (uniform distribution)
    n = len(observed_sorted)
    theoretical_quantiles = (np.arange(1, n + 1) - 0.5) / n
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot theoretical uniform reference (y = x line)
    ax.plot([0, 1], [0, 1], 'k--', label='Theoretical Uniform (Gold Standard)', 
            linewidth=2, alpha=0.7)
    
    # Plot observed p-values vs theoretical
    ax.scatter(theoretical_quantiles, observed_sorted, 
               alpha=0.5, s=15, color='blue', label='Observed (Standard Tests)', 
               edgecolors='none')
    
    # Plot permutation p-values vs theoretical
    ax.scatter(theoretical_quantiles, permutation_sorted, 
               alpha=0.5, s=15, color='green', label='Permutation (Empirical Gold Standard)', 
               edgecolors='none')
    
    # Add 95% confidence bands for uniform distribution
    # Using Kolmogorov-Smirnov critical values
    ks_critical = 1.36 / np.sqrt(n)  # Approximate for alpha=0.05
    lower_band = np.clip(theoretical_quantiles - ks_critical, 0, 1)
    upper_band = np.clip(theoretical_quantiles + ks_critical, 0, 1)
    ax.fill_between(theoretical_quantiles, lower_band, upper_band, 
                    color='gray', alpha=0.2, label='95% KS Confidence Band')
    
    # Calculate KS statistics for annotation
    ks_observed, _ = calculate_ks_statistic(observed_sorted, 'uniform')
    ks_permutation, _ = calculate_ks_statistic(permutation_sorted, 'uniform')
    
    # Annotate KS statistics
    annotation_text = (
        f"KS (Observed vs Uniform): {ks_observed:.4f}\n"
        f"KS (Permutation vs Uniform): {ks_permutation:.4f}"
    )
    ax.text(0.05, 0.95, annotation_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top', 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Labels and title
    ax.set_xlabel('Theoretical Quantiles (Uniform)', fontsize=12)
    ax.set_ylabel('Sample Quantiles', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"QQ-plot saved to: {output_path}")


def main() -> None:
    """
    Main entry point for QQ-plot generation.
    
    Loads p-value trajectories, generates permutation reference,
    and creates QQ-plots for each parameter configuration.
    """
    # Configuration
    data_dir = "data"
    output_dir = "figures"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading p-value trajectories...")
    try:
        trajectories = load_pvalue_trajectories(data_dir)
    except AnalysisError as e:
        logger.error(f"Failed to load trajectories: {e}")
        return
        
    logger.info(f"Loaded {len(trajectories)} trajectory files")
    
    # Process each seed/configuration
    for seed, pvalue_list in trajectories.items():
        logger.info(f"Processing seed: {seed}")
        
        # Aggregate p-values for this seed
        observed_pvalues, _ = aggregate_pvalues({seed: pvalue_list})
        
        if len(observed_pvalues) == 0:
            logger.warning(f"No p-values found for seed {seed}, skipping")
            continue
            
        # Generate permutation reference for this seed
        # Note: In practice, you might want to cache these or compute once
        logger.info(f"Generating permutation reference for seed {seed}...")
        try:
            # Extract parameters from seed filename or metadata
            # For now, we use a default configuration
            perm_pvalues = generate_permutation_reference(
                observed_pvalues, 
                n_permutations=1000,
                seed=int(seed)
            )
        except Exception as e:
            logger.error(f"Failed to generate permutation reference for seed {seed}: {e}")
            continue
            
        # Generate QQ-plot
        output_path = Path(output_dir) / f"qq_plot_{seed}.png"
        title = f"QQ-Plot for Seed {seed}\n(n={len(observed_pvalues)} p-values)"
        
        try:
            generate_qq_plot(
                observed_pvalues=observed_pvalues,
                permutation_pvalues=perm_pvalues,
                output_path=str(output_path),
                title=title
            )
            logger.info(f"Successfully generated QQ-plot: {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate QQ-plot for seed {seed}: {e}")
            
    logger.info("QQ-plot generation complete")


if __name__ == "__main__":
    main()
