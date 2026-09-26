"""
Scatter plot generation for predicted vs. measured hardness with % CI error bars.
Requires T031b predictions (data/processed/predictions.csv).
"""
import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# Ensure non-interactive backend for headless execution
matplotlib.use('Agg')

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging_config import get_logger
from config import get_data_processed_dir, get_data_outputs_dir

logger = get_logger(__name__)


def load_predictions() -> pd.DataFrame:
    """
    Load predictions from T031b output.
    Expected columns: 'hardness_hv' (actual), 'predicted_hv', 'ci_lower', 'ci_upper'
    """
    predictions_path = get_data_processed_dir() / "predictions.csv"
    if not predictions_path.exists():
        raise FileNotFoundError(
            f"Predictions file not found at {predictions_path}. "
            "Ensure T031b has been executed successfully."
        )
    
    df = pd.read_csv(predictions_path)
    
    required_cols = {'hardness_hv', 'predicted_hv'}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"Predictions file missing required columns. "
            f"Expected: {required_cols}, Found: {set(df.columns)}"
        )
    
    # Check for CI columns
    if 'ci_lower' in df.columns and 'ci_upper' in df.columns:
        logger.info("Found CI columns in predictions, will use for error bars.")
        has_ci = True
    else:
        logger.warning("No CI columns found in predictions. Error bars will be omitted or set to 0.")
        has_ci = False
        df['ci_lower'] = df['predicted_hv']
        df['ci_upper'] = df['predicted_hv']
    
    return df, has_ci


def generate_scatter_plot(
    df: pd.DataFrame,
    has_ci: bool,
    output_path: Path,
    title: str = "Predicted vs. Measured Vickers Hardness",
    x_label: str = "Measured Hardness (HV)",
    y_label: str = "Predicted Hardness (HV)",
    ci_label: str = "95% Confidence Interval"
) -> None:
    """
    Generate scatter plot with error bars if CI data is available.
    """
    # Filter out rows with NaN values
    valid_mask = df['hardness_hv'].notna() & df['predicted_hv'].notna()
    if has_ci:
        valid_mask &= df['ci_lower'].notna() & df['ci_upper'].notna()
    
    df_plot = df[valid_mask]
    
    if len(df_plot) == 0:
        raise ValueError("No valid data points found for plotting.")
    
    logger.info(f"Plotting {len(df_plot)} data points.")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    x_vals = df_plot['hardness_hv'].values
    y_vals = df_plot['predicted_hv'].values
    
    # Plot scatter
    scatter = ax.scatter(x_vals, y_vals, alpha=0.6, c='steelblue', edgecolors='w', s=50, label='Data Points')
    
    # Plot 1:1 line
    min_val = min(x_vals.min(), y_vals.min())
    max_val = max(x_vals.max(), y_vals.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Ideal Prediction (y=x)')
    
    # Add error bars if CI data is available
    if has_ci:
        ci_lower = df_plot['ci_lower'].values
        ci_upper = df_plot['ci_upper'].values
        
        # Calculate error lengths for asymmetric error bars
        yerr_lower = y_vals - ci_lower
        yerr_upper = ci_upper - y_vals
        
        ax.errorbar(
            x_vals, y_vals, 
            yerr=[yerr_lower, yerr_upper], 
            fmt='none', 
            ecolor='gray', 
            capsize=3, 
            linewidth=0.5, 
            alpha=0.7,
            label=ci_label
        )
    
    # Labels and Title
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14)
    
    # Grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Legend
    ax.legend(loc='upper left')
    
    # Ensure equal aspect ratio for the 1:1 line visualization
    ax.set_aspect('equal', adjustable='box')
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Scatter plot saved to {output_path}")


def main():
    """Main entry point for scatter plot generation."""
    logger.info("Starting scatter plot generation (T036).")
    
    try:
        # Load predictions
        df, has_ci = load_predictions()
        
        # Define output path
        output_dir = get_data_outputs_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "predicted_vs_measured_scatter.png"
        
        # Generate plot
        generate_scatter_plot(
            df=df,
            has_ci=has_ci,
            output_path=output_path
        )
        
        logger.info("Scatter plot generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during scatter plot generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()