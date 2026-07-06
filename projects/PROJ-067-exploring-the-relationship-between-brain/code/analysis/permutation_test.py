"""
Permutation test implementation for statistical validation.

Implements a non-parametric permutation test to generate a null distribution
for Spearman correlation between network metrics and Dream Recall Frequency (DRF).
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy.stats import spearmanr
from scipy.stats import fdr_bh
from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metrics_and_drf(metrics_path: str, drf_column: str = 'dream_recall_frequency') -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load metrics and DRF values from the subject metrics CSV.
    
    Args:
        metrics_path: Path to the subject_metrics.csv file
        drf_column: Name of the column containing DRF values
        
    Returns:
        Tuple of (metrics_array, drf_array, metric_names)
    """
    import pandas as pd
    
    df = pd.read_csv(metrics_path)
    
    # Validate DRF column exists
    if drf_column not in df.columns:
        raise ValueError(f"Column '{drf_column}' not found in metrics file. Available: {list(df.columns)}")
    
    # Filter out rows with missing DRF or NaN values in metrics
    valid_rows = df.dropna(subset=[drf_column])
    valid_rows = valid_rows.dropna(axis=1, how='all')
    
    if len(valid_rows) == 0:
        raise ValueError("No valid subjects found with DRF data after filtering NaNs.")
    
    # Extract DRF
    drf = valid_rows[drf_column].values.astype(float)
    
    # Identify metric columns (exclude subject_id, drf, and other non-metric columns)
    exclude_cols = ['subject_id', 'dream_recall_frequency', 'drf']
    metric_cols = [col for col in valid_rows.columns if col not in exclude_cols and valid_rows[col].dtype in [float, int]]
    
    if len(metric_cols) == 0:
        raise ValueError("No metric columns found in the dataset.")
    
    metrics = valid_rows[metric_cols].values.astype(float)
    
    logger.info(f"Loaded {len(drf)} subjects with {len(metric_cols)} metrics.")
    
    return metrics, drf, metric_cols

def calculate_observed_correlations(metrics: np.ndarray, drf: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate observed Spearman correlations between each metric and DRF.
    
    Args:
        metrics: Array of shape (n_subjects, n_metrics)
        drf: Array of shape (n_subjects,)
        
    Returns:
        Tuple of (rho_values, p_values)
    """
    n_subjects, n_metrics = metrics.shape
    rho_obs = np.zeros(n_metrics)
    p_obs = np.zeros(n_metrics)
    
    for i in range(n_metrics):
        metric = metrics[:, i]
        # Handle constant metrics
        if np.std(metric) < 1e-8:
            rho_obs[i] = 0.0
            p_obs[i] = 1.0
            continue
        
        # Handle constant DRF
        if np.std(drf) < 1e-8:
            rho_obs[i] = 0.0
            p_obs[i] = 1.0
            continue
        
        rho, p = spearmanr(metric, drf)
        rho_obs[i] = rho
        p_obs[i] = p
        
    return rho_obs, p_obs

def run_permutation_test(
    metrics: np.ndarray,
    drf: np.ndarray,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Run permutation test to generate null distribution for Spearman correlations.
    
    This function permutes the DRF labels (or metric labels) n_permutations times
    to build a null distribution of correlation coefficients.
    
    Args:
        metrics: Array of shape (n_subjects, n_metrics)
        drf: Array of shape (n_subjects,)
        n_permutations: Number of permutation iterations (exactly 1000 as per FR-007)
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (null_distribution, p_permutation, observed_rhos)
        - null_distribution: Array of shape (n_metrics, n_permutations)
        - p_permutation: Array of shape (n_metrics,) - two-sided p-values from permutation
        - observed_rhos: Array of shape (n_metrics,) - observed correlations
    """
    if seed is not None:
        np.random.seed(seed)
        
    n_subjects, n_metrics = metrics.shape
    
    if n_permutations != 1000:
        logger.warning(f"Requested {n_permutations} permutations, but FR-007 specifies exactly 1000. Using 1000.")
        n_permutations = 1000
        
    logger.info(f"Starting permutation test with {n_permutations} iterations...")
    
    # Initialize null distribution array: (n_metrics, n_permutations)
    null_dist = np.zeros((n_metrics, n_permutations))
    
    # Calculate observed correlations first
    observed_rhos, _ = calculate_observed_correlations(metrics, drf)
    
    for perm_idx in range(n_permutations):
        if (perm_idx + 1) % 100 == 0:
            logger.info(f"Permutation {perm_idx + 1}/{n_permutations} completed.")
        
        # Permute DRF labels (shuffling breaks the relationship)
        permuted_drf = drf.copy()
        np.random.shuffle(permuted_drf)
        
        # Calculate correlation for each metric with permuted DRF
        for i in range(n_metrics):
            metric = metrics[:, i]
            
            # Skip constant metrics
            if np.std(metric) < 1e-8 or np.std(permuted_drf) < 1e-8:
                null_dist[i, perm_idx] = 0.0
                continue
                
            rho, _ = spearmanr(metric, permuted_drf)
            null_dist[i, perm_idx] = rho
            
    # Calculate two-sided permutation p-values
    # p = (number of permuted |rho| >= observed |rho| + 1) / (n_permutations + 1)
    p_perm = np.zeros(n_metrics)
    abs_obs = np.abs(observed_rhos)
    abs_null = np.abs(null_dist)
    
    for i in range(n_metrics):
        count_extreme = np.sum(abs_null[i, :] >= abs_obs[i])
        p_perm[i] = (count_extreme + 1) / (n_permutations + 1)
        
    logger.info("Permutation test completed.")
    
    return null_dist, p_perm, observed_rhos

def generate_null_distribution_plot(
    null_dist: np.ndarray,
    observed_rhos: np.ndarray,
    metric_names: List[str],
    output_dir: str,
    metric_idx: int = 0
) -> str:
    """
    Generate a histogram of the null distribution with the observed correlation marked.
    
    Args:
        null_dist: Null distribution array (n_metrics, n_permutations)
        observed_rhos: Observed correlations (n_metrics,)
        metric_names: List of metric names
        output_dir: Directory to save the plot
        metric_idx: Index of the metric to plot
        
    Returns:
        Path to the saved plot file
    """
    import matplotlib.pyplot as plt
    
    metric_name = metric_names[metric_idx]
    obs_rho = observed_rhos[metric_idx]
    null_data = null_dist[metric_idx, :]
    
    plt.figure(figsize=(10, 6))
    plt.hist(null_data, bins=50, alpha=0.7, color='skyblue', edgecolor='black', label='Null Distribution')
    plt.axvline(x=obs_rho, color='red', linestyle='--', linewidth=2, label=f'Observed (ρ={obs_rho:.3f})')
    plt.axvline(x=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    
    plt.xlabel('Spearman Correlation Coefficient (ρ)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title(f'Permutation Test Null Distribution: {metric_name}', fontsize=14)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    plot_path = os.path.join(output_dir, f'null_distribution_{metric_name.replace(" ", "_").replace("-", "_")}.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Null distribution plot saved to: {plot_path}")
    return plot_path

def run_full_permutation_analysis(
    metrics_path: str,
    output_dir: str,
    n_permutations: int = 1000,
    seed: Optional[int] = None,
    generate_plots: bool = True
) -> Dict[str, Any]:
    """
    Run the complete permutation test analysis pipeline.
    
    Args:
        metrics_path: Path to subject_metrics.csv
        output_dir: Directory to save results
        n_permutations: Number of permutations (default 1000)
        seed: Random seed
        generate_plots: Whether to generate null distribution plots
        
    Returns:
        Dictionary containing analysis results
    """
    config = get_config()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    metrics, drf, metric_names = load_metrics_and_drf(metrics_path)
    
    # Run permutation test
    null_dist, p_perm, obs_rhos = run_permutation_test(
        metrics, drf, n_permutations=n_permutations, seed=seed
    )
    
    # Calculate FDR-corrected p-values for permutation p-values
    reject, p_fdr, _, _ = fdr_bh(p_perm, alpha=0.05)
    
    # Prepare results
    results = {
        'n_subjects': len(drf),
        'n_permutations': n_permutations,
        'seed': seed,
        'metrics': []
    }
    
    for i, name in enumerate(metric_names):
        metric_result = {
            'metric_name': name,
            'observed_rho': float(obs_rhos[i]),
            'permutation_p_value': float(p_perm[i]),
            'fdr_corrected_p_value': float(p_fdr[i]),
            'is_significant_fdr': bool(reject[i]),
            'null_distribution_stats': {
                'mean': float(np.mean(null_dist[i, :])),
                'std': float(np.std(null_dist[i, :])),
                'min': float(np.min(null_dist[i, :])),
                'max': float(np.max(null_dist[i, :])),
                'percentile_2.5': float(np.percentile(null_dist[i, :], 2.5)),
                'percentile_97.5': float(np.percentile(null_dist[i, :], 97.5))
            }
        }
        results['metrics'].append(metric_result)
        
        # Generate plot if requested
        if generate_plots:
            try:
                plot_path = generate_null_distribution_plot(
                    null_dist, obs_rhos, metric_names, str(output_dir), i
                )
                metric_result['null_distribution_plot'] = plot_path
            except Exception as e:
                logger.warning(f"Could not generate plot for {name}: {e}")
    
    # Save results to JSON
    results_path = output_dir / 'permutation_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Permutation analysis results saved to: {results_path}")
    
    return results

def main():
    """Main entry point for permutation test script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run permutation test for network metrics vs DRF')
    parser.add_argument(
        '--metrics-path', 
        type=str, 
        default='data/metrics/subject_metrics.csv',
        help='Path to subject metrics CSV file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/plots',
        help='Directory to save results and plots'
    )
    parser.add_argument(
        '--n-permutations',
        type=int,
        default=1000,
        help='Number of permutation iterations (default: 1000)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Disable plot generation'
    )
    
    args = parser.parse_args()
    
    # Ensure n_permutations is 1000 as per FR-007
    if args.n_permutations != 1000:
        logger.warning(f"FR-007 requires exactly 1000 permutations. Setting to 1000.")
        args.n_permutations = 1000
        
    try:
        results = run_full_permutation_analysis(
            metrics_path=args.metrics_path,
            output_dir=args.output_dir,
            n_permutations=args.n_permutations,
            seed=args.seed,
            generate_plots=not args.no_plots
        )
        
        print(f"\nPermutation Test Results Summary:")
        print(f"Subjects: {results['n_subjects']}")
        print(f"Permutations: {results['n_permutations']}")
        print(f"\nMetric Results:")
        for m in results['metrics']:
            sig = "***" if m['is_significant_fdr'] else ""
            print(f"  {m['metric_name']}: ρ={m['observed_rho']:.3f}, "
                  f"p_perm={m['permutation_p_value']:.3f}, "
                  f"p_fdr={m['fdr_corrected_p_value']:.3f} {sig}")
                  
    except Exception as e:
        logger.error(f"Permutation test failed: {e}")
        raise

if __name__ == '__main__':
    main()