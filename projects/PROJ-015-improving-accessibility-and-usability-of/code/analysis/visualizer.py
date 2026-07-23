import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Optional
from scipy import stats

# Ensure we can import from utils
try:
    from utils.logger import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

def plot_sus_score(data: pd.DataFrame, output_path: Optional[str] = None) -> plt.Figure:
    """
    Generates a box plot for SUS scores comparing Traditional vs Explainable interfaces.
    Includes 95% Confidence Interval error bars on the mean.

    Args:
        data: DataFrame containing 'interface_type' and 'sus_score' columns.
        output_path: Optional path to save the figure. If None, figure is returned but not saved.

    Returns:
        matplotlib Figure object.
    """
    if data is None or data.empty:
        logger.error("Input data is empty. Cannot generate SUS score plot.")
        raise ValueError("Input data cannot be empty.")

    # Validate columns
    required_cols = ['interface_type', 'sus_score']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")

    # Ensure interface_type is categorical for consistent ordering
    if 'interface_type' in data.columns:
        data['interface_type'] = pd.Categorical(
            data['interface_type'],
            categories=['Traditional', 'Explainable'],
            ordered=True
        )

    # Filter valid scores (SUS is 0-100)
    valid_data = data[(data['sus_score'] >= 0) & (data['sus_score'] <= 100)]
    
    if valid_data.empty:
        logger.warning("No valid SUS scores found after filtering (0-100 range).")
        # Create an empty plot to indicate failure state but allow execution to continue
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No Valid Data", transform=ax.transAxes, ha='center', va='center')
        ax.set_title("SUS Score Distribution (No Data)")
        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
        return fig

    fig, ax = plt.subplots(figsize=(10, 6))

    # Group by interface type
    groups = valid_data.groupby('interface_type')['sus_score']
    
    # Calculate statistics for plotting
    means = []
    ci_errors = []
    labels = []
    
    for name, group in groups:
        if len(group) > 0:
            mean_val = group.mean()
            # Calculate 95% CI for the mean: mean +/- t * (std / sqrt(n))
            n = len(group)
            std_val = group.std()
            if n > 1:
                # Use t-distribution for small samples
                t_val = stats.t.ppf(0.975, df=n-1)
                se = std_val / np.sqrt(n)
                ci = t_val * se
            else:
                ci = 0.0 # Cannot compute CI for n=1
            
            means.append(mean_val)
            ci_errors.append(ci)
            labels.append(name)

    # Plot boxplot
    bp = ax.boxplot(
        [valid_data[valid_data['interface_type'] == label]['sus_score'].values for label in labels],
        labels=labels,
        patch_artist=True,
        showmeans=True,
        meanprops={"marker":"D", "markerfacecolor":"red", "markersize":8},
        whis=1.5
    )

    # Color the boxes
    colors = ['#ff9999', '#66b3ff']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    # Add mean with error bars (95% CI)
    x_positions = [1, 2]
    ax.errorbar(
        x_positions,
        means,
        yerr=ci_errors,
        fmt='o',
        color='black',
        capsize=5,
        markersize=8,
        linewidth=2,
        label='Mean (95% CI)'
    )

    ax.set_title('System Usability Scale (SUS) Scores by Interface Type', fontsize=14, fontweight='bold')
    ax.set_ylabel('SUS Score (0-100)', fontsize=12)
    ax.set_xlabel('Interface Type', fontsize=12)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(loc='upper right')

    plt.tight_layout()

    if output_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"SUS score plot saved to {output_path}")
    
    return fig

def main():
    """
    Main entry point for generating the SUS score visualization.
    Expects cleaned data at data/processed/cleaned_sessions.csv.
    """
    # Determine paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / 'data' / 'processed' / 'cleaned_sessions.csv'
    output_path = project_root / 'figures' / 'sus_score.png'

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Cannot generate plot.")
        logger.info("Ensure the data cleaning pipeline (T021c) has been run successfully.")
        sys.exit(1)

    try:
        logger.info(f"Loading data from {input_path}...")
        df = pd.read_csv(input_path)
        
        logger.info(f"Generating SUS score plot...")
        fig = plot_sus_score(df, output_path=str(output_path))
        
        logger.info(f"Success: SUS score plot generated at {output_path}")
        
        # Verify file was written
        if output_path.exists():
            logger.info(f"Verification: File exists and size is {output_path.stat().st_size} bytes.")
        else:
            logger.error("Verification failed: File was not written.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error generating SUS score plot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
