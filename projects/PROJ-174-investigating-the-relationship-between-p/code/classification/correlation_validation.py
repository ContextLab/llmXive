import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_classification_results(
    predictions_path: Path,
    search_time_path: Path
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load classification predictions and ground truth search time data.

    Args:
        predictions_path: Path to the CSV containing predicted probabilities
        search_time_path: Path to the CSV containing search time ground truth

    Returns:
        Tuple of (predictions_df, search_time_df)
    """
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    if not search_time_path.exists():
        raise FileNotFoundError(f"Search time file not found: {search_time_path}")

    logger.info(f"Loading predictions from {predictions_path}")
    predictions_df = pd.read_csv(predictions_path)

    # Validate required columns in predictions
    required_pred_cols = ['predicted_probability', 'subject_id', 'trial_id']
    for col in required_pred_cols:
        if col not in predictions_df.columns:
            raise ValueError(f"Missing required column '{col}' in predictions file")

    logger.info(f"Loading search time data from {search_time_path}")
    search_time_df = pd.read_csv(search_time_path)

    # Validate required columns in search time
    required_time_cols = ['search_time', 'subject_id', 'trial_id']
    for col in required_time_cols:
        if col not in search_time_df.columns:
            raise ValueError(f"Missing required column '{col}' in search time file")

    return predictions_df, search_time_df

def compute_continuous_correlation(
    predictions_df: pd.DataFrame,
    search_time_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Compute continuous correlation between predicted probability and search time.

    This function merges the two datasets on subject_id and trial_id,
    then calculates Pearson correlation coefficient and p-value.

    Args:
        predictions_df: DataFrame with predicted probabilities
        search_time_df: DataFrame with search time values

    Returns:
        Dictionary containing correlation statistics:
        - correlation: Pearson r value
        - p_value: p-value of the correlation
        - n_samples: Number of paired observations
        - correlation_type: 'pearson'
        - status: 'VALIDATED' or 'UNVALIDATED' based on data source
    """
    # Merge on subject_id and trial_id
    merged_df = pd.merge(
        predictions_df[['subject_id', 'trial_id', 'predicted_probability']],
        search_time_df[['subject_id', 'trial_id', 'search_time']],
        on=['subject_id', 'trial_id'],
        how='inner'
    )

    if merged_df.empty:
        raise ValueError("No overlapping data found between predictions and search time")

    # Remove rows with missing values
    valid_data = merged_df.dropna(subset=['predicted_probability', 'search_time'])
    n_samples = len(valid_data)

    if n_samples < 3:
        raise ValueError(f"Insufficient data points for correlation (n={n_samples})")

    # Extract vectors
    y_pred = valid_data['predicted_probability'].values
    search_time = valid_data['search_time'].values

    # Calculate Pearson correlation
    correlation, p_value = pearsonr(y_pred, search_time)

    logger.info(f"Computed Pearson correlation: r={correlation:.4f}, p={p_value:.6f} (n={n_samples})")

    return {
        'correlation': correlation,
        'p_value': p_value,
        'n_samples': n_samples,
        'correlation_type': 'pearson',
        'status': 'VALIDATED' if 'UNVALIDATED' not in str(predictions_df.get('status', '').iloc[0]) else 'UNVALIDATED'
    }

def save_correlation_report(
    stats: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save correlation statistics to a CSV file.

    Args:
        stats: Dictionary of correlation statistics
        output_path: Path to output CSV file
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame([stats])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation report to {output_path}")

def plot_correlation(
    predictions_df: pd.DataFrame,
    search_time_df: pd.DataFrame,
    stats: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Create a scatter plot of predicted probability vs. search time with regression line.

    Args:
        predictions_df: DataFrame with predicted probabilities
        search_time_df: DataFrame with search time values
        stats: Dictionary of correlation statistics
        output_path: Path to save the figure
    """
    # Merge data
    merged_df = pd.merge(
        predictions_df[['subject_id', 'trial_id', 'predicted_probability']],
        search_time_df[['subject_id', 'trial_id', 'search_time']],
        on=['subject_id', 'trial_id'],
        how='inner'
    ).dropna()

    if merged_df.empty:
        logger.warning("No data available for plotting")
        return

    y_pred = merged_df['predicted_probability'].values
    search_time = merged_df['search_time'].values

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot
    ax.scatter(y_pred, search_time, alpha=0.6, edgecolors='k', linewidth=0.5, s=50)

    # Add trend line (linear regression)
    z = np.polyfit(y_pred, search_time, 1)
    p = np.poly1d(z)
    x_line = np.linspace(y_pred.min(), y_pred.max(), 100)
    ax.plot(x_line, p(x_line), 'r-', linewidth=2, label=f'Trend Line')

    # An annotate with correlation stats
    corr_text = (
        f"Pearson r = {stats['correlation']:.3f}\n"
        f"p-value = {stats['p_value']:.4f}\n"
        f"N = {stats['n_samples']}"
    )
    ax.text(
        0.05, 0.95, corr_text,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='w', edgecolor='gray')
    )

    ax.set_xlabel('Predicted Probability (Cognitive Load)', fontsize=12)
    ax.set_ylabel('Search Time (s)', fontsize=12)
    ax.set_title('Continuous Correlation: Predicted Load vs. Search Time', fontsize=14)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)

    # Save figure
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved correlation plot to {output_path}")

def run_validation_pipeline(
    predictions_path: Path,
    search_time_path: Path,
    output_csv_path: Path,
    output_plot_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute the full validation pipeline: load data, compute correlation, save report, plot.

    Args:
        predictions_path: Path to predictions CSV
        search_time_path: Path to search time CSV
        output_csv_path: Path for correlation report CSV
        output_plot_path: Path for correlation plot
        config: Optional configuration dictionary

    Returns:
        Dictionary containing correlation statistics
    """
    logger.info("Starting continuous correlation validation pipeline")

    # Load data
    predictions_df, search_time_df = load_classification_results(
        predictions_path, search_time_path
    )

    # Compute correlation
    stats = compute_continuous_correlation(predictions_df, search_time_df)

    # Save report
    save_correlation_report(stats, output_csv_path)

    # Generate plot
    plot_correlation(predictions_df, search_time_df, stats, output_plot_path)

    logger.info("Validation pipeline completed successfully")
    return stats

def main():
    """CLI entry point for correlation validation."""
    parser = argparse.ArgumentParser(
        description="Compute continuous correlation between predicted probability and search time"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to CSV containing predicted probabilities"
    )
    parser.add_argument(
        "--search-time",
        type=str,
        required=True,
        help="Path to CSV containing search time data"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="results/correlation_validation.csv",
        help="Path for output correlation statistics CSV"
    )
    parser.add_argument(
        "--output-plot",
        type=str,
        default="figures/correlation_validation.png",
        help="Path for output correlation plot"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to config file"
    )

    args = parser.parse_args()

    # Load config if exists
    config = None
    if os.path.exists(args.config):
        config = load_config(args.config)

    # Convert to Path objects
    predictions_path = Path(args.predictions)
    search_time_path = Path(args.search_time)
    output_csv_path = Path(args.output_csv)
    output_plot_path = Path(args.output_plot)

    # Ensure output directories exist
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_plot_path.parent.mkdir(parents=True, exist_ok=True)

    # Run pipeline
    try:
        stats = run_validation_pipeline(
            predictions_path,
            search_time_path,
            output_csv_path,
            output_plot_path,
            config
        )
        print(f"Correlation r={stats['correlation']:.4f}, p={stats['p_value']:.6f}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
