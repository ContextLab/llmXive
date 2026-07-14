"""
Plotting module for visualizing posteriors and Bayes factors.

Generates publication-ready figures for:
1. Posterior distributions for inflation (r) and phase transition (E_PT) parameters.
2. Bayes factor comparison tables and visualizations.
3. Theoretical vs. Observed power spectra.

Output files are written to `figures/` directory.
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure figures directory exists
FIGURES_DIR = Path("data/derived/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def load_inference_results(results_path: str) -> Dict[str, Any]:
    """Load inference results from a JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Inference results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_model_comparison_results(results_path: str) -> Dict[str, Any]:
    """Load model comparison results from a JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Model comparison results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def plot_posterior_1d(
    samples: np.ndarray,
    labels: List[str],
    param_idx: int,
    param_name: str,
    true_value: Optional[float] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Plot 1D posterior distribution for a single parameter.
    
    Args:
        samples: Array of shape (n_samples, n_params) from nested sampling.
        labels: List of parameter names.
        param_idx: Index of the parameter to plot.
        param_name: Display name for the parameter.
        true_value: Optional true value to mark (for synthetic validation).
        output_path: Path to save the figure. Defaults to figures/posterior_<param>.png.
    
    Returns:
        Path to the saved figure.
    """
    param_samples = samples[:, param_idx]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot histogram
    counts, bins, _ = ax.hist(param_samples, bins=50, density=True, alpha=0.6, color='skyblue', edgecolor='black')
    
    # Calculate and plot KDE (if enough samples)
    if len(param_samples) > 10:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(param_samples)
        x_range = np.linspace(param_samples.min(), param_samples.max(), 1000)
        ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')
    
    # Mark true value if provided
    if true_value is not None:
        ax.axvline(true_value, color='red', linestyle='--', linewidth=2, label=f'True Value: {true_value:.2e}')
    
    # Calculate and display statistics
    median = np.median(param_samples)
    p16, p84 = np.percentile(param_samples, [16, 84])
    ax.axvline(median, color='green', linestyle='-', linewidth=2, label=f'Median: {median:.2e}')
    ax.axvspan(p16, p84, alpha=0.2, color='green', label=f'68% CI: [{p16:.2e}, {p84:.2e}]')
    
    ax.set_xlabel(param_name)
    ax.set_ylabel('Probability Density')
    ax.set_title(f'Posterior Distribution for {param_name}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if output_path is None:
        safe_name = param_name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
        output_path = str(FIGURES_DIR / f'posterior_{safe_name}.png')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved 1D posterior plot to {output_path}")
    return output_path

def plot_posterior_2d(
    samples: np.ndarray,
    labels: List[str],
    param_indices: Tuple[int, int],
    param_names: Tuple[str, str],
    true_values: Optional[Tuple[float, float]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Plot 2D posterior distribution (corner plot style) for two parameters.
    
    Args:
        samples: Array of shape (n_samples, n_params).
        labels: List of all parameter names.
        param_indices: Tuple of indices for the two parameters.
        param_names: Tuple of display names for the two parameters.
        true_values: Optional tuple of true values to mark.
        output_path: Path to save the figure.
    
    Returns:
        Path to the saved figure.
    """
    x_samples = samples[:, param_indices[0]]
    y_samples = samples[:, param_indices[1]]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # 2D histogram
    hist, xedges, yedges = np.histogram2d(x_samples, y_samples, bins=50, density=True)
    hist = hist.T  # Transpose for correct orientation
    
    # Plot contours
    levels = np.linspace(0, hist.max(), 6)
    contour = ax.contourf(xedges, yedges, hist, levels=levels, cmap='Blues', alpha=0.7)
    contour_lines = ax.contour(xedges, yedges, hist, levels=levels, colors='black', linewidths=0.5)
    
    # Mark true values if provided
    if true_values is not None:
        ax.plot(true_values[0], true_values[1], 'r*', markersize=20, label=f'True: ({true_values[0]:.2e}, {true_values[1]:.2e})')
    
    # Median point
    x_med = np.median(x_samples)
    y_med = np.median(y_samples)
    ax.plot(x_med, y_med, 'go', markersize=10, label=f'Median: ({x_med:.2e}, {y_med:.2e})')
    
    ax.set_xlabel(param_names[0])
    ax.set_ylabel(param_names[1])
    ax.set_title(f'2D Posterior: {param_names[0]} vs {param_names[1]}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if output_path is None:
        safe_name = f"{param_names[0].replace(' ', '_')}_vs_{param_names[1].replace(' ', '_')}"
        output_path = str(FIGURES_DIR / f'posterior_2d_{safe_name}.png')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved 2D posterior plot to {output_path}")
    return output_path

def plot_bayes_factor_table(
    comparison_results: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Plot a visual representation of Bayes factors and model comparison results.
    
    Args:
        comparison_results: Dictionary containing Bayes factors and model evidence.
        output_path: Path to save the figure.
    
    Returns:
        Path to the saved figure.
    """
    models = comparison_results.get('models', [])
    log_evidences = comparison_results.get('log_evidences', {})
    bayes_factors = comparison_results.get('bayes_factors', {})
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Extract model names and log evidences
    model_names = list(log_evidences.keys())
    log_evs = [log_evidences[m] for m in model_names]
    
    # Bar plot of log evidences
    colors = ['skyblue' if m != 'Null' else 'lightcoral' for m in model_names]
    bars = ax.bar(model_names, log_evs, color=colors, edgecolor='black', alpha=0.7)
    
    # Add value labels on bars
    for bar, log_ev in zip(bars, log_evs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{log_ev:.2f}',
                ha='center', va='bottom', fontsize=10)
    
    ax.set_ylabel('Log Evidence')
    ax.set_title('Model Comparison: Log Evidence')
    ax.grid(True, alpha=0.3, axis='y')
    
    if output_path is None:
        output_path = str(FIGURES_DIR / 'bayes_factor_evidence.png')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Bayes factor evidence plot to {output_path}")
    
    # Create a second plot for Bayes factors relative to Null model
    if 'Null' in model_names:
        null_ev = log_evidences['Null']
        bf_vs_null = {m: np.exp(log_evidences[m] - null_ev) for m in model_names if m != 'Null'}
        
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        models_bf = list(bf_vs_null.keys())
        bfs = list(bf_vs_null.values())
        
        colors_bf = ['green' if bf > 10 else 'orange' if bf > 3 else 'red' for bf in bfs]
        bars2 = ax2.bar(models_bf, bfs, color=colors_bf, edgecolor='black', alpha=0.7)
        
        # Add decision threshold line
        ax2.axhline(y=10, color='red', linestyle='--', linewidth=2, label='Strong Evidence Threshold (K>10)')
        ax2.axhline(y=3, color='orange', linestyle='--', linewidth=1, label='Moderate Evidence Threshold (K>3)')
        
        for bar, bf in zip(bars2, bfs):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                     f'{bf:.2f}',
                     ha='center', va='bottom', fontsize=10)
        
        ax2.set_ylabel('Bayes Factor (vs Null)')
        ax2.set_title('Bayes Factors Relative to Null Model')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        if output_path is None:
            bf_path = str(FIGURES_DIR / 'bayes_factor_vs_null.png')
        else:
            bf_path = str(FIGURES_DIR / 'bayes_factor_vs_null.png')
        
        plt.savefig(bf_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved Bayes factor vs Null plot to {bf_path}")
        return bf_path
    
    return output_path

def plot_spectrum_comparison(
    observed_spectrum: Dict[str, List[float]],
    theoretical_spectrum: Dict[str, List[float]],
    output_path: Optional[str] = None
) -> str:
    """
    Plot observed vs theoretical power spectra.
    
    Args:
        observed_spectrum: Dict with keys 'l_values' and 'cl_values' from observed data.
        theoretical_spectrum: Dict with keys 'l_values' and 'cl_values' from theoretical model.
        output_path: Path to save the figure.
    
    Returns:
        Path to the saved figure.
    """
    l_obs = observed_spectrum.get('l_values', [])
    cl_obs = observed_spectrum.get('cl_values', [])
    l_theory = theoretical_spectrum.get('l_values', [])
    cl_theory = theoretical_spectrum.get('cl_values', [])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot observed
    ax.errorbar(l_obs, cl_obs, yerr=cl_obs*0.1, fmt='o', label='Observed (BICEP/Planck)', color='blue', alpha=0.7)
    
    # Plot theoretical
    ax.plot(l_theory, cl_theory, 'r-', label='Theoretical Model', linewidth=2)
    
    ax.set_xlabel(r'$\ell$')
    ax.set_ylabel(r'$C_\ell^{BB}$')
    ax.set_title('Observed vs Theoretical B-mode Power Spectrum')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if output_path is None:
        output_path = str(FIGURES_DIR / 'spectrum_comparison.png')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved spectrum comparison plot to {output_path}")
    return output_path

def generate_all_plots(
    inference_results_path: str,
    model_comparison_results_path: Optional[str] = None,
    observed_spectrum_path: Optional[str] = None,
    theoretical_spectrum_path: Optional[str] = None
) -> List[str]:
    """
    Generate all plots for the current analysis.
    
    Args:
        inference_results_path: Path to inference results JSON.
        model_comparison_results_path: Optional path to model comparison results JSON.
        observed_spectrum_path: Optional path to observed spectrum JSON.
        theoretical_spectrum_path: Optional path to theoretical spectrum JSON.
    
    Returns:
        List of paths to generated figures.
    """
    generated_files = []
    
    try:
        # Load inference results
        inference_data = load_inference_results(inference_results_path)
        samples = np.array(inference_data.get('samples', []))
        param_names = inference_data.get('param_names', ['r', 'E_PT'])
        
        if samples.size == 0:
            logger.warning("No samples found in inference results. Skipping posterior plots.")
        else:
            # Plot 1D posteriors for each parameter
            for i, name in enumerate(param_names):
                true_val = None
                # Try to find true value if available in metadata
                if 'metadata' in inference_data and 'true_values' in inference_data['metadata']:
                    true_val = inference_data['metadata']['true_values'].get(name)
                
                path = plot_posterior_1d(samples, param_names, i, name, true_value=true_val)
                generated_files.append(path)
            
            # Plot 2D posterior if we have at least 2 parameters
            if len(param_names) >= 2:
                true_vals = None
                if 'metadata' in inference_data and 'true_values' in inference_data['metadata']:
                    true_vals = (
                        inference_data['metadata']['true_values'].get(param_names[0]),
                        inference_data['metadata']['true_values'].get(param_names[1])
                    )
                    true_vals = tuple(v for v in true_vals if v is not None)
                    if len(true_vals) < 2:
                        true_vals = None
                
                path = plot_posterior_2d(
                    samples, param_names, (0, 1), (param_names[0], param_names[1]),
                    true_values=true_vals
                )
                generated_files.append(path)
    
    except Exception as e:
        logger.error(f"Error generating posterior plots: {e}")
    
    try:
        if model_comparison_results_path and os.path.exists(model_comparison_results_path):
            comparison_data = load_model_comparison_results(model_comparison_results_path)
            path = plot_bayes_factor_table(comparison_data)
            generated_files.append(path)
    except Exception as e:
        logger.error(f"Error generating Bayes factor plots: {e}")
    
    try:
        if observed_spectrum_path and theoretical_spectrum_path:
            with open(observed_spectrum_path, 'r') as f:
                obs_spec = json.load(f)
            with open(theoretical_spectrum_path, 'r') as f:
                theo_spec = json.load(f)
            path = plot_spectrum_comparison(obs_spec, theo_spec)
            generated_files.append(path)
    except Exception as e:
        logger.error(f"Error generating spectrum comparison plot: {e}")
    
    logger.info(f"Generated {len(generated_files)} plot files.")
    return generated_files

def main():
    """
    Main entry point for generating plots.
    
    Usage:
        python code/plotting.py --inference <path> --comparison <path> [--observed <path>] [--theoretical <path>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate plots for model comparison and posteriors.")
    parser.add_argument("--inference", type=str, required=True, help="Path to inference results JSON.")
    parser.add_argument("--comparison", type=str, default=None, help="Path to model comparison results JSON.")
    parser.add_argument("--observed", type=str, default=None, help="Path to observed spectrum JSON.")
    parser.add_argument("--theoretical", type=str, default=None, help="Path to theoretical spectrum JSON.")
    
    args = parser.parse_args()
    
    generated = generate_all_plots(
        inference_results_path=args.inference,
        model_comparison_results_path=args.comparison,
        observed_spectrum_path=args.observed,
        theoretical_spectrum_path=args.theoretical
    )
    
    print(f"Successfully generated {len(generated)} plots:")
    for p in generated:
        print(f"  - {p}")

if __name__ == "__main__":
    main()