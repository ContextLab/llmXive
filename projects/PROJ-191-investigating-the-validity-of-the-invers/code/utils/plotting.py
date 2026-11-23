"""
Visualization utilities for the Inverse-Square Law investigation.

Generates plots for:
1. MCMC posterior distributions (corner plot style) for alpha and lambda.
2. Bayes Factor evidence comparison.
3. Force vs. Separation data with model fits.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import norm

# Import project config for logging and paths
from config import get_logger, ProjectConfig

logger = get_logger(__name__)


def load_mcmc_chains(path: str) -> np.ndarray:
    """
    Load MCMC chains from the standard output path.

    Expected shape: (n_walkers, n_steps, n_params)
    Returns: (n_samples, n_params) flattened burn-in removed if necessary.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"MCMC chains file not found at {path}")

    chains = np.load(p)
    logger.info(f"Loaded MCMC chains with shape: {chains.shape}")

    # Simple burn-in: discard first 10%
    n_walkers, n_steps, n_params = chains.shape
    burn_in = int(n_steps * 0.1)
    flat_chains = chains[:, burn_in:, :].reshape(-1, n_params)
    logger.info(f"Flattened chains shape (after burn-in): {flat_chains.shape}")
    return flat_chains


def load_bayes_factor(path: str) -> float:
    """Load Bayes factor K from the results JSON."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Bayes factor file not found at {path}")

    with open(p, 'r') as f:
        data = json.load(f)

    if 'K' not in data:
        raise KeyError("Key 'K' not found in Bayes factor JSON")
    
    return float(data['K'])


def plot_posterior_distributions(
    chains: np.ndarray,
    param_names: List[str],
    output_path: str,
    title: str = "Posterior Distributions"
) -> None:
    """
    Create a corner-style plot for posterior distributions.
    
    Args:
        chains: Flattened chains (n_samples, n_params).
        param_names: List of parameter names (e.g., ['alpha', 'log_lambda']).
        output_path: Path to save the figure.
        title: Plot title.
    """
    if chains.shape[1] != len(param_names):
        raise ValueError(f"Number of params in chains ({chains.shape[1]}) "
                       f"does not match param_names ({len(param_names)})")

    fig, axes = plt.subplots(
        len(param_names), len(param_names),
        figsize=(10, 10),
        sharex='col', sharey='row'
    )

    # Handle 1D case separately if needed, but assume 2+ for this study
    for i, name_i in enumerate(param_names):
        for j, name_j in enumerate(param_names):
            ax = axes[i, j]
            
            if i == j:
                # Histogram for diagonal
                ax.hist(chains[:, i], bins=50, color='steelblue', alpha=0.7, density=True)
                ax.set_ylabel('Density')
                
                # Calculate quantiles
                q95 = np.percentile(chains[:, i], [2.5, 97.5])
                median = np.median(chains[:, i])
                ax.axvline(median, color='red', linestyle='--', linewidth=1, label='Median')
                ax.axvspan(q95[0], q95[1], alpha=0.2, color='red')
                ax.legend()
            else:
                # Scatter for off-diagonal
                ax.scatter(chains[:, j], chains[:, i], s=1, alpha=0.3, color='steelblue')
            
            if i == len(param_names) - 1:
                ax.set_xlabel(name_j)
            else:
                ax.tick_params(labelbottom=False)
            
            if j == 0:
                ax.set_ylabel(name_i)
            else:
                ax.tick_params(labelleft=False)

    fig.suptitle(title, y=1.02)
    plt.tight_layout()
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved posterior plot to {output_path}")


def plot_bayes_factor_evidence(
    bayes_factor: float,
    output_path: str,
    title: str = "Bayes Factor Evidence"
) -> None:
    """
    Plot the Bayes Factor on a standard scale (Kass & Raftery).
    
    Args:
        bayes_factor: The computed K value.
        output_path: Path to save the figure.
        title: Plot title.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Define standard thresholds
    thresholds = [1, 3, 10, 20, 150]
    labels = [
        "Not worth more than a bare mention",
        "Substantial",
        "Strong",
        "Very Strong",
        "Decisive"
    ]
    
    # Create a bar for the value
    # Since K can be large, we might plot log10(K) or just the value if small.
    # Let's plot a horizontal bar relative to thresholds.
    
    y_pos = np.arange(len(thresholds))
    colors = ['lightgray' if k < bayes_factor else 'steelblue' for k in thresholds]
    
    ax.barh(y_pos, thresholds, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel('Bayes Factor (K)')
    ax.set_title(f"Bayes Factor Interpretation: K = {bayes_factor:.2f}")
    
    # Add a vertical line for the actual value
    ax.axvline(bayes_factor, color='red', linestyle='--', linewidth=2, label='Observed K')
    ax.legend()
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved Bayes Factor plot to {output_path}")


def plot_force_vs_separation(
    data: Dict[str, Any],
    chains: Optional[np.ndarray] = None,
    output_path: Optional[str] = None,
    title: str = "Force vs Separation with Model Fit"
) -> None:
    """
    Plot the harmonized data with the median model fit from MCMC.
    
    Args:
        data: Dictionary containing 'separation_m', 'force_n', 'covariance_matrix'.
        chains: Optional MCMC chains to plot uncertainty band.
        output_path: Path to save the figure. If None, not saved (interactive only).
        title: Plot title.
    """
    from models.physics import yukawa_force, newtonian_force
    
    sep = data['separation_m']
    force = data['force_n']
    cov = data['covariance_matrix']
    std = np.sqrt(np.diag(cov))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot data with error bars
    ax.errorbar(sep, force, yerr=std, fmt='o', capsize=3, label='Experimental Data', alpha=0.7)
    
    # Generate smooth grid for model
    sep_smooth = np.linspace(sep.min(), sep.max(), 500)
    
    if chains is not None and len(chains) > 0:
        # Plot median model
        # Assume params are [alpha, log_lambda] or similar based on inference setup
        # We need to know the mapping. Let's assume standard Yukawa params: alpha, lambda_m
        # If chains are [alpha, log_lambda], we need to exp the second one.
        # For simplicity, let's assume the inference output defines the params.
        # We will try to infer from the shape or use a standard assumption.
        # Let's assume params are [alpha, log_lambda] for this plotter.
        
        alpha_samples = chains[:, 0]
        log_lambda_samples = chains[:, 1] if chains.shape[1] > 1 else np.zeros_like(alpha_samples)
        
        median_alpha = np.median(alpha_samples)
        median_log_lambda = np.median(log_lambda_samples)
        median_lambda = np.exp(median_log_lambda)
        
        # Calculate model
        model_force = yukawa_force(sep_smooth, median_alpha, median_lambda)
        ax.plot(sep_smooth, model_force, 'r-', label=f'Yukawa Fit ($\\alpha={median_alpha:.2e}$)', linewidth=2)
        
        # Plot 95% credible band
        # Sample 100 random draws to estimate band
        n_samples = min(100, len(chains))
        indices = np.random.choice(len(chains), n_samples, replace=False)
        model_samples = np.zeros((n_samples, len(sep_smooth)))
        
        for i, idx in enumerate(indices):
            a = chains[idx, 0]
            l_log = chains[idx, 1] if chains.shape[1] > 1 else 0
            lam = np.exp(l_log)
            model_samples[i, :] = yukawa_force(sep_smooth, a, lam)
        
        lower = np.percentile(model_samples, 2.5, axis=0)
        upper = np.percentile(model_samples, 97.5, axis=0)
        ax.fill_between(sep_smooth, lower, upper, color='red', alpha=0.2, label='95% Credible Interval')
    else:
        # Plot Newtonian baseline
        model_force = newtonian_force(sep_smooth)
        ax.plot(sep_smooth, model_force, 'k--', label='Newtonian Baseline')

    ax.set_xlabel('Separation (m)')
    ax.set_ylabel('Force (N)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150)
        logger.info(f"Saved force plot to {output_path}")
    
    plt.close()


def main():
    """
    Main entry point to generate all standard plots.
    Expects:
      - data/results/mcmc_chains.npy
      - data/results/bayes_factor.json
      - data/processed/harmonized_data.npz (or similar)
    """
    config = ProjectConfig()
    results_dir = config.results_dir
    processed_dir = config.processed_dir
    figures_dir = config.figures_dir
    
    # Ensure figures directory exists
    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Plot Posteriors
    chains_path = Path(results_dir) / "mcmc_chains.npy"
    if chains_path.exists():
        chains = load_mcmc_chains(str(chains_path))
        # Assume params are [alpha, log_lambda] based on inference tasks
        plot_posterior_distributions(
            chains, 
            param_names=['alpha', 'log_lambda'], 
            output_path=str(Path(figures_dir) / "posteriors.png")
        )
    else:
        logger.warning(f"MCMC chains not found at {chains_path}. Skipping posterior plot.")

    # 2. Plot Bayes Factor
    bf_path = Path(results_dir) / "bayes_factor.json"
    if bf_path.exists():
        try:
            bf = load_bayes_factor(str(bf_path))
            plot_bayes_factor_evidence(
                bf,
                output_path=str(Path(figures_dir) / "bayes_factor.png")
            )
        except (KeyError, ValueError) as e:
            logger.error(f"Could not plot Bayes factor: {e}")
    else:
        logger.warning(f"Bayes factor file not found at {bf_path}. Skipping BF plot.")

    # 3. Plot Force vs Separation
    # Try to load harmonized data. The path might vary, try common locations.
    data_paths = [
        Path(processed_dir) / "harmonized_data.npz",
        Path(processed_dir) / "harmonized_data.json",
        Path(processed_dir) / "covariance_matrix.npy" # Fallback if just cov exists, need full data
    ]
    
    harmonized_data = None
    for p in data_paths:
        if p.exists():
            try:
                if p.suffix == '.npz':
                    data_dict = np.load(p, allow_pickle=True)
                    harmonized_data = {
                        'separation_m': data_dict['separation_m'],
                        'force_n': data_dict['force_n'],
                        'covariance_matrix': data_dict['covariance_matrix']
                    }
                elif p.suffix == '.json':
                    with open(p, 'r') as f:
                        harmonized_data = json.load(f)
                break
            except Exception as e:
                logger.warning(f"Failed to load {p}: {e}")
    
    if harmonized_data:
        chains = load_mcmc_chains(str(chains_path)) if chains_path.exists() else None
        plot_force_vs_separation(
            harmonized_data,
            chains=chains,
            output_path=str(Path(figures_dir) / "force_fit.png")
        )
    else:
        logger.warning("Harmonized data not found. Skipping force fit plot.")

    logger.info("Plotting complete.")


if __name__ == "__main__":
    main()
