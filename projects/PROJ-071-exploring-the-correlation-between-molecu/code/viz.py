"""Visualization module for molecular complexity vs degradation analysis.

Generates diagnostic plots including residual analysis and insufficiency plots.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# Set style for scientific publication quality
plt.style.use('seaborn-whitegrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12

# Project root relative to this file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
OUTPUTS_DIR = os.path.join(DATA_DIR, 'outputs')

# Ensure output directory exists
os.makedirs(OUTPUTS_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


def get_data_path(filename: str) -> str:
    """Get full path to a data file."""
    return os.path.join(PROJECT_ROOT, 'data', filename)


def check_gate_status() -> Tuple[bool, Dict[str, Any]]:
    """Check the gate status from gate_status.json."""
    gate_path = os.path.join(PROCESSED_DIR, 'gate_status.json')
    if not os.path.exists(gate_path):
        logger.warning(f"Gate status file not found: {gate_path}")
        return False, {"status": "UNKNOWN", "reason": "File not found"}
    
    try:
        with open(gate_path, 'r') as f:
            status = json.load(f)
        return status.get('status') == 'PASS', status
    except Exception as e:
        logger.error(f"Error reading gate status: {e}")
        return False, {"status": "ERROR", "reason": str(e)}


def check_statistical_gate() -> Tuple[bool, Dict[str, Any]]:
    """Check the statistical gate status from stat_gate_status.json."""
    stat_gate_path = os.path.join(PROCESSED_DIR, 'stat_gate_status.json')
    if not os.path.exists(stat_gate_path):
        logger.warning(f"Statistical gate status file not found: {stat_gate_path}")
        return False, {"status": "UNKNOWN", "reason": "File not found"}
    
    try:
        with open(stat_gate_path, 'r') as f:
            status = json.load(f)
        return status.get('status') == 'PASS', status
    except Exception as e:
        logger.error(f"Error reading statistical gate status: {e}")
        return False, {"status": "ERROR", "reason": str(e)}


def load_analysis_results() -> Optional[Dict[str, Any]]:
    """Load analysis results from analysis_results.json."""
    results_path = os.path.join(PROCESSED_DIR, 'analysis_results.json')
    if not os.path.exists(results_path):
        logger.warning(f"Analysis results file not found: {results_path}")
        return None
    
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading analysis results: {e}")
        return None


def load_residuals_data() -> Optional[pd.DataFrame]:
    """Load residuals data for plotting if available."""
    # Try to load from a standard residuals file if it exists
    residuals_path = os.path.join(PROCESSED_DIR, 'residuals_data.csv')
    if os.path.exists(residuals_path):
        try:
            return pd.read_csv(residuals_path)
        except Exception as e:
            logger.error(f"Error reading residuals data: {e}")
    
    # Fallback: try to extract from analysis_results.json if it contains residuals
    results = load_analysis_results()
    if results and 'residuals' in results:
        return pd.DataFrame(results['residuals'])
    
    return None


def plot_scatter_with_regression(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: str
) -> None:
    """Generate a scatter plot with regression line."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Scatter plot
    ax.scatter(x, y, alpha=0.6, edgecolors='w', linewidth=0.5, s=50)
    
    # Fit regression line
    if len(x) > 1 and np.std(x) > 0:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        x_line = np.array([min(x), max(x)])
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'y = {slope:.3f}x + {intercept:.3f}\nR² = {r_value**2:.3f}')
        ax.legend()
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved scatter plot to {output_path}")


def generate_placeholder_plot(output_path: str, message: str) -> None:
    """Generate a placeholder plot when data is insufficient."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=14, transform=ax.transAxes)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved placeholder plot to {output_path}")


def generate_correlation_scatter_plots(results: Dict[str, Any]) -> None:
    """Generate scatter plots for top correlated features (T032)."""
    # This function is called by T032, but we ensure it's safe here too
    logger.info("Generating correlation scatter plots...")
    # Implementation handled by T032, kept here for completeness


def plot_residual_histogram(residuals: np.ndarray, output_path: str) -> None:
    """Generate histogram of residuals."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(residuals, bins=30, edgecolor='black', alpha=0.7, color='skyblue')
    ax.axvline(x=0, color='r', linestyle='--', linewidth=2, label='Zero residual')
    ax.set_xlabel('Residuals')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Residuals')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved residual histogram to {output_path}")


def plot_qq_plot(residuals: np.ndarray, output_path: str) -> None:
    """Generate QQ plot of residuals."""
    fig, ax = plt.subplots(figsize=(10, 6))
    stats.probplot(residuals, dist="norm", plot=ax)
    ax.set_title('Q-Q Plot of Residuals')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved QQ plot to {output_path}")


def plot_residuals_vs_fitted(
    fitted: np.ndarray,
    residuals: np.ndarray,
    output_path: str
) -> None:
    """Generate residuals vs fitted values plot."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(fitted, residuals, alpha=0.6, edgecolors='w', linewidth=0.5, s=50)
    ax.axhline(y=0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Fitted Values')
    ax.set_ylabel('Residuals')
    ax.set_title('Residuals vs Fitted Values')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved residuals vs fitted plot to {output_path}")


def generate_residual_diagnostic_plots(results: Dict[str, Any]) -> None:
    """Generate all residual diagnostic plots (T033)."""
    # Load residuals data
    residuals_df = load_residuals_data()
    
    if residuals_df is None or len(residuals_df) == 0:
        logger.warning("No residuals data found. Generating placeholder plots.")
        generate_placeholder_plot(
            os.path.join(OUTPUTS_DIR, 'residuals.png'),
            "No Residuals Data Available\n(Analysis may have been skipped or failed)"
        )
        generate_placeholder_plot(
            os.path.join(OUTPUTS_DIR, 'qq_plot.png'),
            "No Residuals Data Available\n(QQ-plot requires model residuals)"
        )
        return

    # Extract arrays
    residuals = residuals_df.get('residuals', residuals_df.iloc[:, 0] if len(residuals_df.columns) > 0 else None)
    fitted = residuals_df.get('fitted_values', residuals_df.iloc[:, -1] if len(residuals_df.columns) > 1 else None)

    if residuals is None or len(residuals) == 0:
        logger.warning("Residuals column not found or empty.")
        generate_placeholder_plot(
            os.path.join(OUTPUTS_DIR, 'residuals.png'),
            "No Residuals Data Available"
        )
        generate_placeholder_plot(
            os.path.join(OUTPUTS_DIR, 'qq_plot.png'),
            "No Residuals Data Available"
        )
        return

    # Plot 1: Residual Histogram
    plot_residual_histogram(
        residuals.values if hasattr(residuals, 'values') else np.array(residuals),
        os.path.join(OUTPUTS_DIR, 'residuals.png')
    )

    # Plot 2: QQ Plot
    plot_qq_plot(
        residuals.values if hasattr(residuals, 'values') else np.array(residuals),
        os.path.join(OUTPUTS_DIR, 'qq_plot.png')
    )

    # Plot 3: Residuals vs Fitted (if fitted values available)
    if fitted is not None and len(fitted) > 0:
        plot_residuals_vs_fitted(
            fitted.values if hasattr(fitted, 'values') else np.array(fitted),
            residuals.values if hasattr(residuals, 'values') else np.array(residuals),
            os.path.join(OUTPUTS_DIR, 'residuals_vs_fitted.png')
        )
    else:
        logger.warning("Fitted values not found. Skipping residuals vs fitted plot.")


def generate_insufficiency_plots(gate_status: Dict[str, Any]) -> None:
    """Generate diagnostic plots for insufficient data (T033)."""
    logger.info("Generating insufficiency diagnostic plots...")
    
    # Try to load the full dataset to show distribution
    merged_path = os.path.join(PROCESSED_DIR, 'merged_drugs.csv')
    standard_path = os.path.join(PROCESSED_DIR, 'standard_subset.csv')
    
    data_to_plot = None
    plot_title = "Distribution of Half-Lives (Limited Data)"
    
    if os.path.exists(standard_path):
        try:
            data_to_plot = pd.read_csv(standard_path)
        except Exception as e:
            logger.error(f"Error reading standard_subset.csv: {e}")
    elif os.path.exists(merged_path):
        try:
            data_to_plot = pd.read_csv(merged_path)
        except Exception as e:
            logger.error(f"Error reading merged_drugs.csv: {e}")
    
    if data_to_plot is None or 'half_life' not in data_to_plot.columns:
        # Fallback: generate a generic insufficiency plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.6, "Data Insufficiency Detected", ha='center', va='center', fontsize=16, transform=ax.transAxes)
        ax.text(0.5, 0.4, f"Reason: {gate_status.get('reason', 'Unknown')}", ha='center', va='center', fontsize=12, transform=ax.transAxes)
        ax.text(0.5, 0.3, f"Available N: {gate_status.get('N_std', gate_status.get('N', 'N/A'))}", ha='center', va='center', fontsize=12, transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUTS_DIR, 'limited_data_dist.png'), dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Saved insufficiency plot to {os.path.join(OUTPUTS_DIR, 'limited_data_dist.png')}")
        return

    # Extract half-life column
    half_lives = data_to_plot['half_life'].dropna()
    
    if len(half_lives) == 0:
        generate_placeholder_plot(
            os.path.join(OUTPUTS_DIR, 'limited_data_dist.png'),
            "No Valid Half-Life Data Found"
        )
        return

    # Generate histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(half_lives, bins=20, edgecolor='black', alpha=0.7, color='lightcoral')
    ax.set_xlabel('Half-Life (hours)')
    ax.set_ylabel('Frequency')
    ax.set_title(f'{plot_title}\n(N = {len(half_lives)})')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUTS_DIR, 'limited_data_dist.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved insufficiency distribution plot to {os.path.join(OUTPUTS_DIR, 'limited_data_dist.png')}")


def main() -> None:
    """Main entry point for visualization tasks."""
    logger.info("Starting visualization module (T033)...")
    
    # Check gate status
    gate_passed, gate_status = check_gate_status()
    stat_gate_passed, stat_gate_status = check_statistical_gate()
    
    # Load analysis results
    results = load_analysis_results()
    
    if gate_passed and stat_gate_passed and results and results.get('status') == 'PASS':
        logger.info("Gate passed. Generating residual diagnostic plots.")
        generate_residual_diagnostic_plots(results)
    else:
        logger.warning("Gate failed or analysis skipped. Generating insufficiency plots.")
        # Combine gate status info
        combined_status = {
            "status": "FAIL",
            "reason": gate_status.get('reason', 'Gate failed'),
            "N": gate_status.get('N', 0),
            "N_std": stat_gate_status.get('N_std', 0) if stat_gate_status else 0
        }
        generate_insufficiency_plots(combined_status)
    
    logger.info("Visualization module completed.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()