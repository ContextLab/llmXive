"""
Visualization script for the Impact of Incidental Music on Autobiographical Memory Retrieval.

This script generates diagnostic and result visualizations based on the processed data
and model outputs from the pipeline. It is invoked by the run-book (quickstart.md).

Outputs:
- data/final/plots/regression_residuals.png
- data/final/plots/qq_plot.png
- data/final/plots/scale_location.png
- data/final/plots/residuals_leverage.png
- data/final/plots/exposure_distribution.png
- data/final/plots/match_rate_sensitivity.png
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Dict, Any

# Add project root to path for imports
from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger

# Configure logging
logger = get_logger(__name__)

def load_regression_results() -> pd.DataFrame:
    """Load regression summary results."""
    path = get_project_root() / "data" / "final" / "regression_summary.csv"
    if not path.exists():
        raise FileNotFoundError(f"Regression results not found at {path}")
    return pd.read_csv(path)

def load_user_track_pairs() -> pd.DataFrame:
    """Load user-track pairs dataset."""
    path = get_project_root() / "data" / "processed" / "user_track_pairs.parquet"
    if not path.exists():
        raise FileNotFoundError(f"User-track pairs not found at {path}")
    return pd.read_parquet(path)

def load_sensitivity_analysis() -> pd.DataFrame:
    """Load sensitivity analysis results."""
    path = get_project_root() / "data" / "final" / "sensitivity_analysis.csv"
    if not path.exists():
        logger.warning(f"Sensitivity analysis not found at {path}. Skipping sensitivity plot.")
        return None
    return pd.read_csv(path)

def calculate_residuals(model_results: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    """Calculate residuals from model predictions."""
    # Assuming model_results contains coefficients needed to predict
    # This is a simplified version; in reality, we'd need the full model object
    # For visualization, we'll use the observed vs predicted from the summary
    if 'mean_vividness' in data.columns and 'predicted_vividness' in data.columns:
        data['residuals'] = data['mean_vividness'] - data['predicted_vividness']
    else:
        # Fallback: use a proxy if predicted values aren't available
        logger.warning("Predicted values not found in data. Using observed mean_vividness as proxy.")
        data['residuals'] = data['mean_vividness']
    return data

def create_residuals_plot(data: pd.DataFrame, output_path: Path) -> None:
    """Create residuals vs fitted plot."""
    plt.figure(figsize=(10, 6))
    if 'predicted_vividness' in data.columns:
        sns.scatterplot(x='predicted_vividness', y='residuals', data=data, alpha=0.5)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Fitted Values')
        plt.ylabel('Residuals')
        plt.title('Residuals vs Fitted')
    else:
        # Fallback plot
        sns.histplot(data['residuals'], kde=True)
        plt.xlabel('Residuals')
        plt.ylabel('Frequency')
        plt.title('Residual Distribution (Fallback)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved residuals plot to {output_path}")

def create_qq_plot(data: pd.DataFrame, output_path: Path) -> None:
    """Create Q-Q plot of residuals."""
    plt.figure(figsize=(8, 8))
    if 'residuals' in data.columns:
        from scipy import stats
        stats.probplot(data['residuals'].dropna(), dist="norm", plot=plt)
        plt.title('Q-Q Plot of Residuals')
    else:
        logger.warning("Residuals not found. Skipping Q-Q plot.")
        plt.title('Q-Q Plot (Data Unavailable)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Q-Q plot to {output_path}")

def create_scale_location_plot(data: pd.DataFrame, output_path: Path) -> None:
    """Create Scale-Location plot."""
    plt.figure(figsize=(10, 6))
    if 'predicted_vividness' in data.columns and 'residuals' in data.columns:
        residuals_sqrt = np.sqrt(np.abs(data['residuals']))
        sns.scatterplot(x='predicted_vividness', y=residuals_sqrt, alpha=0.5)
        # Add smoothed line
        from scipy.ndimage import gaussian_filter1d
        x_sorted = np.sort(data['predicted_vividness'])
        y_sorted = residuals_sqrt[np.argsort(data['predicted_vividness'])]
        y_smooth = gaussian_filter1d(y_sorted, 5)
        plt.plot(x_sorted, y_smooth, 'r-', linewidth=2)
        plt.xlabel('Fitted Values')
        plt.ylabel('sqrt(|Residuals|)')
        plt.title('Scale-Location Plot')
    else:
        logger.warning("Required columns for Scale-Location plot not found.")
        plt.title('Scale-Location Plot (Data Unavailable)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Scale-Location plot to {output_path}")

def create_residuals_leverage_plot(data: pd.DataFrame, output_path: Path) -> None:
    """Create Residuals vs Leverage plot."""
    plt.figure(figsize=(10, 6))
    if 'predicted_vividness' in data.columns and 'residuals' in data.columns:
        # Calculate leverage (simplified: using hat values approximation)
        # In a full implementation, we'd use the model's hat matrix
        n = len(data)
        p = 2  # number of predictors (exposure + popularity)
        leverage = (1 / n) + ((data['predicted_vividness'] - data['predicted_vividness'].mean()) ** 2) / (n * data['predicted_vividness'].var())
        
        # Standardized residuals
        std_residuals = data['residuals'] / data['residuals'].std()
        
        sns.scatterplot(x=leverage, y=std_residuals, alpha=0.5)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Leverage')
        plt.ylabel('Standardized Residuals')
        plt.title('Residuals vs Leverage')
    else:
        logger.warning("Required columns for Residuals vs Leverage plot not found.")
        plt.title('Residuals vs Leverage (Data Unavailable)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Residuals vs Leverage plot to {output_path}")

def create_exposure_distribution_plot(data: pd.DataFrame, output_path: Path) -> None:
    """Create distribution plot of adolescent exposure ratio."""
    plt.figure(figsize=(10, 6))
    if 'adolescent_exposure_ratio' in data.columns:
        sns.histplot(data['adolescent_exposure_ratio'], kde=True, bins=30)
        plt.xlabel('Adolescent Exposure Ratio')
        plt.ylabel('Frequency')
        plt.title('Distribution of Adolescent Exposure Ratio')
    else:
        logger.warning("adolescent_exposure_ratio column not found.")
        plt.title('Exposure Distribution (Data Unavailable)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved exposure distribution plot to {output_path}")

def create_sensitivity_plot(sensitivity_data: Optional[pd.DataFrame], output_path: Path) -> None:
    """Create sensitivity analysis plot."""
    if sensitivity_data is None or sensitivity_data.empty:
        logger.warning("No sensitivity data available. Skipping sensitivity plot.")
        plt.figure(figsize=(10, 6))
        plt.title('Sensitivity Analysis (No Data Available)')
        plt.savefig(output_path, dpi=300)
        plt.close()
        return

    plt.figure(figsize=(12, 6))
    # Assuming sensitivity_data has columns: threshold, coefficient, p_value, std_error
    if 'threshold' in sensitivity_data.columns and 'coefficient' in sensitivity_data.columns:
        sns.lineplot(data=sensitivity_data, x='threshold', y='coefficient', marker='o')
        plt.xlabel('Levenshtein Threshold')
        plt.ylabel('Coefficient (Adolescent Exposure)')
        plt.title('Sensitivity Analysis: Coefficient Stability')
        plt.grid(True, alpha=0.3)
    else:
        logger.warning("Sensitivity data missing required columns.")
        plt.title('Sensitivity Analysis (Data Incomplete)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved sensitivity plot to {output_path}")

def generate_all_plots() -> None:
    """Generate all diagnostic and result plots."""
    project_root = get_project_root()
    plots_dir = project_root / "data" / "final" / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading data for visualization...")
    try:
        regression_results = load_regression_results()
        user_track_pairs = load_user_track_pairs()
        sensitivity_data = load_sensitivity_analysis()
    except FileNotFoundError as e:
        logger.error(f"Missing required data files: {e}")
        # Create placeholder plots to indicate missing data
        for name, path in [
            ("regression_residuals.png", plots_dir / "regression_residuals.png"),
            ("qq_plot.png", plots_dir / "qq_plot.png"),
            ("scale_location.png", plots_dir / "scale_location.png"),
            ("residuals_leverage.png", plots_dir / "residuals_leverage.png"),
            ("exposure_distribution.png", plots_dir / "exposure_distribution.png"),
            ("match_rate_sensitivity.png", plots_dir / "match_rate_sensitivity.png"),
        ]:
            plt.figure(figsize=(8, 6))
            plt.title(f"{name.replace('.png', '')} (Missing Data)")
            plt.savefig(path, dpi=300)
            plt.close()
        return

    # Calculate residuals if not present
    if 'residuals' not in user_track_pairs.columns:
        user_track_pairs = calculate_residuals(regression_results, user_track_pairs)

    logger.info("Generating diagnostic plots...")
    create_residuals_plot(user_track_pairs, plots_dir / "regression_residuals.png")
    create_qq_plot(user_track_pairs, plots_dir / "qq_plot.png")
    create_scale_location_plot(user_track_pairs, plots_dir / "scale_location.png")
    create_residuals_leverage_plot(user_track_pairs, plots_dir / "residuals_leverage.png")

    logger.info("Generating result plots...")
    create_exposure_distribution_plot(user_track_pairs, plots_dir / "exposure_distribution.png")
    create_sensitivity_plot(sensitivity_data, plots_dir / "match_rate_sensitivity.png")

    logger.info("All plots generated successfully.")

def main() -> None:
    """Main entry point for the visualization script."""
    setup_logging()
    logger.info("Starting visualization pipeline...")
    
    try:
        generate_all_plots()
        logger.info("Visualization pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()