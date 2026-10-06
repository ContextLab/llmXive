"""
T040 Implementation: Generate plots (SHAP summary, stability distribution) and save to data/results/

This script produces:
1. data/results/shap_summary.png - SHAP summary plot of feature importance
2. data/results/stability_distribution.png - Distribution of feature importance from bootstrap stability analysis
"""
import os
import sys
import logging
import json
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)

def load_shap_results():
    """Load SHAP analysis results from previous step."""
    shap_path = CONFIG.SHAP_RESULTS_PATH
    if not os.path.exists(shap_path):
        raise FileNotFoundError(f"SHAP results not found at {shap_path}. Run shap_analysis.py first.")
    
    with open(shap_path, 'rb') as f:
        return pickle.load(f)

def load_bootstrap_results():
    """Load bootstrap stability results from previous step."""
    bootstrap_path = CONFIG.BOOTSTRAP_RESULTS_PATH
    if not os.path.exists(bootstrap_path):
        raise FileNotFoundError(f"Bootstrap results not found at {bootstrap_path}. Run bootstrap_stability.py first.")
    
    with open(bootstrap_path, 'rb') as f:
        return pickle.load(f)

def generate_shap_summary_plot(shap_results):
    """Generate and save SHAP summary plot."""
    logger.info("Generating SHAP summary plot...")
    
    shap_values = shap_results.get('shap_values')
    feature_names = shap_results.get('feature_names')
    
    if shap_values is None or len(shap_values) == 0:
        raise ValueError("No SHAP values found in results")
    
    # Calculate mean absolute SHAP values for ranking
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    indices = np.argsort(mean_abs_shap)[::-1]
    
    # Create summary plot
    plt.figure(figsize=(10, 8))
    
    # Bar plot of mean absolute SHAP values
    plt.barh(range(len(feature_names)), mean_abs_shap[indices], align='center')
    plt.yticks(range(len(feature_names)), [feature_names[i] for i in indices])
    plt.xlabel('Mean |SHAP Value|')
    plt.ylabel('Feature')
    plt.title('SHAP Summary - Feature Importance')
    plt.gca().invert_yaxis()
    
    # Save plot
    output_path = Path(CONFIG.RESULTS_DIR) / 'shap_summary.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"SHAP summary plot saved to {output_path}")
    return output_path

def generate_stability_distribution_plot(bootstrap_results):
    """Generate and save stability distribution plot."""
    logger.info("Generating stability distribution plot...")
    
    sample_size_sweep = bootstrap_results.get('sample_size_sweep', {})
    fixed_sample_bootstrap = bootstrap_results.get('fixed_sample_bootstrap', {})
    feature_names = bootstrap_results.get('feature_names', [])
    
    if not feature_names:
        raise ValueError("No feature names found in bootstrap results")
    
    # Prepare data for plotting
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Sample Size Sweep (Standard Deviation of Feature Importance)
    ax1 = axes[0]
    if sample_size_sweep and 'std_devs' in sample_size_sweep:
        std_devs = sample_size_sweep['std_devs']
        n_samples = sample_size_sweep['n_samples']
        
        # Plot std_dev for each feature across sample sizes
        for i, feature in enumerate(feature_names):
            if i < len(std_devs):
                ax1.plot(n_samples, std_devs[i], marker='o', label=feature, linewidth=2)
        
        ax1.set_xlabel('Sample Size')
        ax1.set_ylabel('Standard Deviation of Feature Importance')
        ax1.set_title('Feature Importance Stability vs Sample Size')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax1.grid(True, alpha=0.3)
    else:
        ax1.text(0.5, 0.5, 'No sample size sweep data available', 
                transform=ax1.transAxes, ha='center', va='center')
        ax1.set_title('Sample Size Sweep')
    
    # Plot 2: Fixed Sample Bootstrap Distribution
    ax2 = axes[1]
    if fixed_sample_bootstrap and 'importance_means' in fixed_sample_bootstrap:
        importance_means = fixed_sample_bootstrap['importance_means']
        importance_stds = fixed_sample_bootstrap.get('importance_stds', np.zeros_like(importance_means))
        
        # Create error bar plot
        x_pos = np.arange(len(feature_names))
        ax2.bar(x_pos, importance_means, yerr=importance_stds, capsize=5, alpha=0.7, color='steelblue')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(feature_names, rotation=45, ha='right')
        ax2.set_ylabel('Mean Feature Importance')
        ax2.set_title('Fixed-Sample Bootstrap Results (Mean ± Std Dev)')
        ax2.grid(True, alpha=0.3, axis='y')
    else:
        ax2.text(0.5, 0.5, 'No fixed sample bootstrap data available', 
                transform=ax2.transAxes, ha='center', va='center')
        ax2.set_title('Fixed Sample Bootstrap')
    
    plt.tight_layout()
    output_path = Path(CONFIG.RESULTS_DIR) / 'stability_distribution.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Stability distribution plot saved to {output_path}")
    return output_path

def main():
    """Main entry point for T040."""
    logger.info("Starting T040: Generating plots for SHAP and stability analysis...")
    
    try:
        # Ensure results directory exists
        os.makedirs(CONFIG.RESULTS_DIR, exist_ok=True)
        
        # Load results from previous steps
        shap_results = load_shap_results()
        bootstrap_results = load_bootstrap_results()
        
        # Generate plots
        shap_plot_path = generate_shap_summary_plot(shap_results)
        stability_plot_path = generate_stability_distribution_plot(bootstrap_results)
        
        # Log completion
        logger.info("T040 completed successfully.")
        logger.info(f"Generated: {shap_plot_path}")
        logger.info(f"Generated: {stability_plot_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"T040 failed: {str(e)}")
        raise

if __name__ == "__main__":
    sys.exit(main())
