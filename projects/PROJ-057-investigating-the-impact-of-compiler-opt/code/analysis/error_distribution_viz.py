import os
import json
import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_RESULTS_DIR = Path("data/results")
STABILITY_METRICS_PATH = DATA_RESULTS_DIR / "stability_metrics.csv"
OUTPUT_PLOT_PATH = DATA_RESULTS_DIR / "error_distribution_per_optimization_level.png"
ERROR_THRESHOLD = 1e-5

def load_stability_metrics() -> pd.DataFrame:
    """Load stability metrics from CSV."""
    if not STABILITY_METRICS_PATH.exists():
        raise FileNotFoundError(f"Stability metrics not found at {STABILITY_METRICS_PATH}")
    
    df = pd.read_csv(STABILITY_METRICS_PATH)
    logger.info(f"Loaded {len(df)} records from {STABILITY_METRICS_PATH}")
    return df

def parse_optimization_level(config_id: str) -> str:
    """Extract optimization level from config_id (e.g., 'matmul_O2_512' -> 'O2')."""
    parts = config_id.split('_')
    if len(parts) >= 2:
        # Assume second part is the optimization level (e.g., O0, O1, O2, O3, Os)
        opt_level = parts[1]
        # Validate it looks like an optimization flag
        if opt_level.startswith('O') and (opt_level[1:].isdigit() or opt_level[1:] in ['s', 'fast', 'march']):
            return opt_level
    return "Unknown"

def plot_error_distribution(df: pd.DataFrame, output_path: Path) -> None:
    """
    Plot error distribution per optimization level.
    
    Creates a boxplot and violin plot showing:
    - L2 relative error distribution per optimization level
    - Highlights unstable configurations (error > 1e-5)
    """
    if df.empty:
        logger.warning("Empty dataframe, cannot plot error distribution")
        return

    # Filter out configurations with NaN errors
    df_clean = df.dropna(subset=['l2_error'])
    
    if df_clean.empty:
        logger.warning("No valid error data after cleaning, cannot plot")
        return

    # Extract optimization levels
    df_clean = df_clean.copy()
    df_clean['opt_level'] = df_clean['config_id'].apply(parse_optimization_level)
    
    # Separate stable and unstable
    df_stable = df_clean[df_clean['l2_error'] <= ERROR_THRESHOLD]
    df_unstable = df_clean[df_clean['l2_error'] > ERROR_THRESHOLD]

    # Prepare data for plotting
    opt_levels = df_clean['opt_level'].unique()
    opt_levels = sorted(opt_levels, key=lambda x: (x.startswith('O'), x))  # Sort O0, O1, O2, O3, Os, etc.

    # Create figure with subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Error Distribution per Optimization Level', fontsize=16, fontweight='bold')

    # Plot 1: Boxplot of L2 error by optimization level
    ax1 = axes[0]
    ax1.set_title('L2 Relative Error Distribution')
    ax1.set_xlabel('Optimization Level')
    ax1.set_ylabel('L2 Relative Error')
    ax1.set_yscale('log')  # Log scale for better visibility of small errors

    box_data = []
    box_labels = []
    
    for opt in opt_levels:
        subset = df_stable[df_stable['opt_level'] == opt]['l2_error']
        if len(subset) > 0:
            box_data.append(subset.values)
            box_labels.append(opt)

    if box_data:
        bp = ax1.boxplot(box_data, labels=box_labels, patch_artist=True, 
                       showfliers=True, flierprops=dict(marker='o', markersize=4))
        
        # Color the boxes
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(box_data)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

    # Plot unstable points as red dots on the same plot
    if not df_unstable.empty:
        for _, row in df_unstable.iterrows():
            opt = row['opt_level']
            if opt in box_labels:
                idx = box_labels.index(opt)
                ax1.plot([idx + 1], [row['l2_error']], 'ro', markersize=6, 
                        label='Unstable (error > 1e-5)' if _ == df_unstable.index[0] else "")

    ax1.axhline(y=ERROR_THRESHOLD, color='r', linestyle='--', 
               label=f'Stability Threshold ({ERROR_THRESHOLD})', alpha=0.7)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    # Plot 2: Violin plot for distribution shape
    ax2 = axes[1]
    ax2.set_title('L2 Error Distribution (Violin Plot)')
    ax2.set_xlabel('Optimization Level')
    ax2.set_ylabel('L2 Relative Error')
    ax2.set_yscale('log')

    if box_data:
        parts = ax2.violinplot(box_data, showmeans=True, showmedians=True)
        
        # Color the violins
        for pc, color in zip(parts['bodies'], colors):
            pc.set_facecolor(color)
            pc.set_alpha(0.7)
            pc.set_edgecolor('black')
        
        # Style means and medians
        for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians', 'cmeans'):
            vp = parts[partname]
            vp.set_edgecolor('black')
            vp.set_linewidth(1)

    if not df_unstable.empty:
        for _, row in df_unstable.iterrows():
            opt = row['opt_level']
            if opt in box_labels:
                idx = box_labels.index(opt)
                ax2.plot([idx + 1], [row['l2_error']], 'ro', markersize=6,
                        label='Unstable (error > 1e-5)' if _ == df_unstable.index[0] else "")

    ax2.axhline(y=ERROR_THRESHOLD, color='r', linestyle='--', 
               label=f'Stability Threshold ({ERROR_THRESHOLD})', alpha=0.7)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)

    # Add summary statistics as text
    summary_text = f"Total configs: {len(df_clean)}\n"
    summary_text += f"Stable (≤{ERROR_THRESHOLD}): {len(df_stable)}\n"
    summary_text += f"Unstable (> {ERROR_THRESHOLD}): {len(df_unstable)}"
    
    fig.text(0.02, 0.02, summary_text, fontsize=9, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Error distribution plot saved to {output_path}")

def generate_error_distribution_summary(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Generate summary statistics for error distribution per optimization level."""
    df_clean = df.dropna(subset=['l2_error']).copy()
    df_clean['opt_level'] = df_clean['config_id'].apply(parse_optimization_level)
    
    summary = {}
    for opt_level in df_clean['opt_level'].unique():
        subset = df_clean[df_clean['opt_level'] == opt_level]['l2_error']
        if len(subset) > 0:
            summary[opt_level] = {
                'count': len(subset),
                'mean': float(subset.mean()),
                'median': float(subset.median()),
                'std': float(subset.std()),
                'min': float(subset.min()),
                'max': float(subset.max()),
                'stable_count': int((subset <= ERROR_THRESHOLD).sum()),
                'unstable_count': int((subset > ERROR_THRESHOLD).sum())
            }
    return summary

def main():
    """Main entry point for generating error distribution visualization."""
    logger.info("Starting error distribution visualization generation...")
    
    try:
        # Ensure output directory exists
        OUTPUT_PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Load data
        df = load_stability_metrics()
        
        if df.empty:
            logger.warning("No data found in stability metrics. Exiting.")
            return
        
        # Generate plot
        plot_error_distribution(df, OUTPUT_PLOT_PATH)
        
        # Generate and log summary
        summary = generate_error_distribution_summary(df)
        logger.info("Error distribution summary:")
        for opt_level, stats_dict in summary.items():
            logger.info(f"  {opt_level}: {stats_dict}")
        
        logger.info(f"Visualization complete. Output: {OUTPUT_PLOT_PATH}")
        
    except Exception as e:
        logger.error(f"Error generating visualization: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()