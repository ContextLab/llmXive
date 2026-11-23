"""
Visualization module for User Story 3 (Robustness Assessment).
Generates histograms of stability metrics and uncertainty bands.
"""
import os
import json
import logging
import pickle
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union

from config import get_artifacts_dir, get_project_root
from robustness import load_loo_results, load_fpca_results
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def plot_stability_histogram(
    stability_metrics: Dict[str, List[float]],
    output_path: Path,
    title: str = "Stability Metrics Distribution (LOO Jackknife)"
) -> None:
    """
    Generate a histogram of stability metrics (loading correlations)
    across all LOO iterations and components.

    Args:
        stability_metrics: Dictionary mapping component index to list of correlations.
        output_path: Path to save the figure.
        title: Plot title.
    """
    plt.figure(figsize=(10, 6))
    
    all_correlations = []
    for comp_idx, corrs in stability_metrics.items():
        all_correlations.extend(corrs)
    
    if not all_correlations:
        logger.warning("No stability metrics found to plot.")
        plt.close()
        return

    # Plot histogram
    plt.hist(all_correlations, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    
    # Add reference lines
    plt.axvline(x=0.95, color='red', linestyle='--', linewidth=2, label='Stability Threshold (0.95)')
    plt.axvline(x=np.mean(all_correlations), color='green', linestyle='-', linewidth=2, 
               label=f'Mean Correlation: {np.mean(all_correlations):.3f}')
    
    plt.xlabel('Loading Correlation', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved stability histogram to {output_path}")

def plot_uncertainty_bands(
    loo_results: Dict[str, Any],
    output_path: Path,
    title: str = "Uncertainty Bands for Dominant Modes"
) -> None:
    """
    Generate plots showing uncertainty bands for dominant modes
    based on LOO jackknife results.

    Args:
        loo_results: Dictionary containing LOO results including eigenfunctions.
        output_path: Path to save the figure.
        title: Plot title.
    """
    if 'full_eigenfunctions' not in loo_results or 'loo_eigenfunctions' not in loo_results:
        logger.warning("Missing eigenfunction data for uncertainty band plot.")
        return

    full_eigenfunctions = loo_results['full_eigenfunctions']
    loo_eigenfunctions = loo_results['loo_eigenfunctions']
    
    # Assuming eigenfunctions are 2D arrays: (n_components, n_timepoints)
    if not isinstance(full_eigenfunctions, np.ndarray) or len(full_eigenfunctions.shape) < 2:
        logger.warning("Eigenfunctions not in expected format (n_components, n_timepoints).")
        return

    n_components = full_eigenfunctions.shape[0]
    n_timepoints = full_eigenfunctions.shape[1]
    timepoints = np.arange(n_timepoints)

    plt.figure(figsize=(12, 8))
    
    # Plot for each component
    colors = plt.cm.viridis(np.linspace(0, 1, n_components))
    
    for i in range(min(n_components, 5)):  # Limit to top 5 components
        full_mode = full_eigenfunctions[i]
        
        # Calculate mean and std from LOO results for this component
        loo_modes = [loo_eigenfunctions[j][i] for j in range(len(loo_eigenfunctions)) 
                    if i < len(loo_eigenfunctions[j])]
        
        if not loo_modes:
            continue
            
        loo_array = np.array(loo_modes)
        mean_mode = np.mean(loo_array, axis=0)
        std_mode = np.std(loo_array, axis=0)
        
        # Plot full ensemble mode
        plt.plot(timepoints, full_mode, color=colors[i], linewidth=2.5, 
                label=f'Full Ensemble (PC{i+1})')
        
        # Plot uncertainty band (mean ± 2*std)
        plt.fill_between(timepoints, 
                       mean_mode - 2*std_mode, 
                       mean_mode + 2*std_mode, 
                       color=colors[i], alpha=0.2, 
                       label=f'LOO Mean ± 2σ (PC{i+1})')
        
        # Plot LOO mean
        plt.plot(timepoints, mean_mode, color=colors[i], linestyle='--', linewidth=1, alpha=0.7)

    plt.xlabel('Time (standardized)', fontsize=12)
    plt.ylabel('Eigenfunction Value', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved uncertainty bands plot to {output_path}")

def generate_robustness_visualizations(
    artifacts_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """
    Generate all visualizations for robustness assessment.

    Args:
        artifacts_dir: Directory containing LOO results (defaults to project artifacts dir).
        output_dir: Directory to save figures (defaults to artifacts_dir/figures).

    Returns:
        Dictionary mapping plot type to output path.
    """
    if artifacts_dir is None:
        artifacts_dir = get_artifacts_dir()
    
    if output_dir is None:
        output_dir = artifacts_dir / "figures"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Load LOO results
    loo_results_path = artifacts_dir / "loo_results.pkl"
    if not loo_results_path.exists():
        logger.error(f"LOO results file not found at {loo_results_path}")
        return results
    
    loo_results = load_loo_results(loo_results_path)
    
    # Load stability metrics from unstable_modes.json if available
    stability_metrics_path = artifacts_dir / "unstable_modes.json"
    stability_metrics = {}
    if stability_metrics_path.exists():
        with open(stability_metrics_path, 'r') as f:
            data = json.load(f)
            # Extract correlations from the data structure
            if 'stability_metrics' in data:
                stability_metrics = data['stability_metrics']
    
    # Generate histogram if we have stability metrics
    if stability_metrics:
        hist_path = output_dir / "stability_histogram.png"
        plot_stability_histogram(stability_metrics, hist_path)
        results['histogram'] = hist_path
    else:
        # Try to compute from raw LOO results if available
        if 'correlations' in loo_results:
            # Reconstruct metrics from correlations
            corr_data = loo_results['correlations']
            metrics = {}
            for key, vals in corr_data.items():
                if isinstance(vals, list):
                    metrics[key] = vals
                else:
                    metrics[key] = [vals]
            
            if metrics:
                hist_path = output_dir / "stability_histogram.png"
                plot_stability_histogram(metrics, hist_path)
                results['histogram'] = hist_path

    # Generate uncertainty bands
    if 'full_eigenfunctions' in loo_results and 'loo_eigenfunctions' in loo_results:
        bands_path = output_dir / "uncertainty_bands.png"
        plot_uncertainty_bands(loo_results, bands_path)
        results['uncertainty_bands'] = bands_path
    
    logger.info(f"Generated {len(results)} robustness visualizations in {output_dir}")
    return results

def main() -> None:
    """Main entry point for generating robustness visualizations."""
    setup_logging()
    
    logger.info("Starting robustness visualization generation...")
    
    try:
        results = generate_robustness_visualizations()
        
        if results:
            logger.info(f"Successfully generated visualizations: {list(results.keys())}")
            for name, path in results.items():
                logger.info(f"  - {name}: {path}")
        else:
            logger.warning("No visualizations were generated. Check input data availability.")
            
    except Exception as e:
        logger.error(f"Failed to generate visualizations: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()