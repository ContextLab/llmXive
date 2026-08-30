"""
Task T030/T031: Visualization Module.

Generates forest plots and residual diagnostic plots based on analysis results.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Import config
from config import get_data_dir

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_figures_dir() -> Path:
    """Returns the path to the figures directory."""
    return Path("figures")

def load_analysis_results() -> Optional[Dict[str, Any]]:
    """Loads the analysis results from `analysis/results.json`."""
    results_path = Path("analysis") / "results.json"
    if not results_path.exists():
        logger.error(f"Analysis results not found at {results_path}. Run analysis.py first.")
        return None
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse analysis results JSON: {e}")
        return None

def generate_forest_plot(results: Dict[str, Any], output_path: Path):
    """
    Generates a forest plot of condition effects (surprisal coefficient).
    """
    # Extract relevant data from the results dictionary.
    # The analysis.py script is expected to populate these keys.
    coef = results.get('coef_surprisal')
    ci_lower = results.get('ci_lower')
    ci_upper = results.get('ci_upper')
    pval = results.get('pval_surprisal')
    convergence_status = results.get('convergence_status', 'unknown')
    
    # Handle cases where we might have a list of results (if multiple datasets were run)
    # For now, we assume a single run as per the standard pipeline flow, 
    # but we check if 'coef_surprisal' is a list to be robust.
    if isinstance(coef, list):
        # If multiple datasets, we plot them in a row
        n = len(coef)
        plt.figure(figsize=(6 * n, 5))
        for i, (c, l, u, p) in enumerate(zip(coef, ci_lower, ci_upper, pval)):
            plt.subplot(1, n, i+1)
            plt.errorbar(
                x=[0],
                y=[c],
                yerr=[[c - l], [u - c]],
                fmt='o',
                capsize=5,
                markersize=10,
                color='blue',
                ecolor='black',
                linewidth=2
            )
            plt.axvline(x=0, color='red', linestyle='--', linewidth=1)
            title = f'Dataset {i+1}\n(β={c:.4f}, p={p:.4f})'
            if convergence_status and isinstance(convergence_status, list):
                title += f'\n[{convergence_status[i]}]'
            plt.title(title)
            plt.yticks([])
            # Dynamic X-axis limits based on data
            all_vals = [c, l, u]
            min_val = min(all_vals)
            max_val = max(all_vals)
            padding = (max_val - min_val) * 0.2 if max_val != min_val else 0.5
            plt.xlim(min_val - padding, max_val + padding)
            plt.xlabel('Effect Size (Coefficient)')
        plt.suptitle('Forest Plot of Surprisal Effects')
    else:
        # Single dataset case
        if coef is None:
            logger.warning("No surprisal coefficient found in results. Skipping forest plot.")
            # Create a placeholder to ensure file exists
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Forest Plot (No Data)')
            plt.axis('off')
            plt.savefig(output_path, dpi=300)
            plt.close()
            return

        plt.figure(figsize=(8, 6))
        plt.errorbar(
            x=[0],
            y=[coef],
            yerr=[[coef - ci_lower], [ci_upper - coef]],
            fmt='o',
            capsize=5,
            markersize=10,
            color='blue',
            ecolor='black',
            linewidth=2
        )
        plt.axvline(x=0, color='red', linestyle='--', linewidth=1)
        
        title = f'Surprisal Effect on Duration Perception\n(β={coef:.4f}, p={pval:.4f})'
        if convergence_status:
            title += f'\nStatus: {convergence_status}'
        
        plt.title(title)
        plt.yticks([])
        
        # Dynamic X-axis limits
        all_vals = [coef, ci_lower, ci_upper]
        min_val = min(all_vals)
        max_val = max(all_vals)
        padding = (max_val - min_val) * 0.2 if max_val != min_val else 0.5
        plt.xlim(min_val - padding, max_val + padding)
        
        plt.xlabel('Effect Size (Coefficient)')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
    
    logger.info(f"Forest plot saved to {output_path}")

def generate_residual_diagnostics(results: Dict[str, Any], output_path: Path):
    """
    Generates residual diagnostic plots (QQ plot, Histogram).
    """
    # We need the residuals. The analysis.py script should save them to 'residuals'.
    residuals = results.get('residuals')

    if residuals is None:
        logger.warning("Residuals not found in results. Creating a placeholder diagnostic plot.")
        plt.figure(figsize=(12, 5))
        plt.text(0.5, 0.5, 'Residuals not available in results.json', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Residual Diagnostics (Data Missing)')
        plt.axis('off')
        plt.savefig(output_path, dpi=300)
        plt.close()
        return

    # Ensure residuals is a list/array
    residuals = pd.Series(residuals)

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    # Histogram
    axs[0].hist(residuals, bins=30, edgecolor='black', alpha=0.7, color='skyblue')
    axs[0].set_title('Histogram of Residuals')
    axs[0].set_xlabel('Residual Value')
    axs[0].set_ylabel('Frequency')

    # QQ Plot
    stats.probplot(residuals, dist="norm", plot=axs[1])
    axs[1].set_title('Q-Q Plot of Residuals')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Residual diagnostics saved to {output_path}")

def run_visualization_pipeline():
    """Main entry point for visualization."""
    results = load_analysis_results()
    if not results:
        logger.error("Cannot proceed without analysis results.")
        return False

    figures_dir = get_figures_dir()
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Generate Forest Plot
    forest_path = figures_dir / "forest_plot_surprisal.png"
    generate_forest_plot(results, forest_path)

    # Generate Residual Diagnostics
    diag_path = figures_dir / "residual_diagnostics.png"
    generate_residual_diagnostics(results, diag_path)

    return True

def main():
    """Entry point."""
    logger.info("Starting Visualization Pipeline")
    success = run_visualization_pipeline()
    if success:
        logger.info("Visualization completed successfully.")
        sys.exit(0)
    else:
        logger.error("Visualization failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()