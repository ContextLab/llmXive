"""
Plotting utilities for User Story 3: Statistical Analysis and Reporting.

Generates scatter plots with regression lines and residual diagnostics
for the ANCOVA analysis results.
"""
import os
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import seaborn as sns

# Configure logging
logger = logging.getLogger(__name__)

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')

def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "Scatter Plot with Regression Line",
    x_label: str = "X Variable",
    y_label: str = "Y Variable",
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a scatter plot with a regression line.
    
    Args:
        data: DataFrame containing the data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Plot title
        x_label: X-axis label
        y_label: Y-axis label
        output_path: Path to save the plot (if None, returns in-memory)
        
    Returns:
        Path to the saved plot file
    """
    if x_col not in data.columns or y_col not in data.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in data. Available: {list(data.columns)}")
    
    # Remove NaN values
    clean_data = data[[x_col, y_col]].dropna()
    
    if len(clean_data) < 2:
        raise ValueError(f"Not enough data points ({len(clean_data)}) to generate a regression plot.")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    ax.scatter(clean_data[x_col], clean_data[y_col], alpha=0.6, edgecolors='w', linewidth=0.5)
    
    # Regression line
    slope, intercept = np.polyfit(clean_data[x_col], clean_data[y_col], 1)
    x_line = np.linspace(clean_data[x_col].min(), clean_data[x_col].max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression: y = {slope:.3f}x + {intercept:.3f}')
    
    # R-squared calculation
    residuals = clean_data[y_col] - (slope * clean_data[x_col] + intercept)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((clean_data[y_col] - clean_data[y_col].mean()) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    ax.set_title(f"{title} (R² = {r_squared:.3f})")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Scatter plot saved to {output_path}")
        return output_path
    
    return output_path

def generate_regression_line_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    fitted_col: str,
    title: str = "Observed vs Fitted Values",
    x_label: str = "Observed",
    y_label: str = "Fitted",
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a plot comparing observed vs fitted values.
    
    Args:
        data: DataFrame containing observed and fitted values
        x_col: Column name for observed values
        y_col: Column name for fitted values (or vice versa)
        fitted_col: Column name for the other set of values
        title: Plot title
        x_label: X-axis label
        y_label: Y-axis label
        output_path: Path to save the plot
        
    Returns:
        Path to the saved plot file
    """
    if x_col not in data.columns or y_col not in data.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in data.")
    
    clean_data = data[[x_col, y_col]].dropna()
    
    if len(clean_data) < 2:
        raise ValueError(f"Not enough data points ({len(clean_data)}) to generate the plot.")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter of observed vs fitted
    ax.scatter(clean_data[x_col], clean_data[y_col], alpha=0.6, edgecolors='w')
    
    # Ideal line (y = x)
      # Calculate min/max for the line
    min_val = min(clean_data[x_col].min(), clean_data[y_col].min())
    max_val = max(clean_data[x_col].max(), clean_data[y_col].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', label='Ideal (y=x)')
    
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Regression line plot saved to {output_path}")
        return output_path
    
    return output_path

def generate_residual_plot(
    data: pd.DataFrame,
    residuals_col: str,
    fitted_col: str,
    title: str = "Residuals vs Fitted Values",
    x_label: str = "Fitted Values",
    y_label: str = "Residuals",
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a residual diagnostic plot.
    
    Args:
        data: DataFrame containing residuals and fitted values
        residuals_col: Column name for residuals
        fitted_col: Column name for fitted values
        title: Plot title
        x_label: X-axis label
        y_label: Y-axis label
        output_path: Path to save the plot
        
    Returns:
        Path to the saved plot file
    """
    if residuals_col not in data.columns or fitted_col not in data.columns:
        raise ValueError(f"Columns {residuals_col} or {fitted_col} not found in data.")
    
    clean_data = data[[residuals_col, fitted_col]].dropna()
    
    if len(clean_data) < 2:
        raise ValueError(f"Not enough data points ({len(clean_data)}) to generate the plot.")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Residuals vs Fitted
    ax1.scatter(clean_data[fitted_col], clean_data[residuals_col], alpha=0.6, edgecolors='w')
    ax1.axhline(y=0, color='r', linestyle='--')
    ax1.set_title("Residuals vs Fitted")
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)
    ax1.grid(True, alpha=0.3)
    
    # Q-Q Plot for residuals
    from scipy import stats
    qq_data = clean_data[residuals_col].dropna()
    if len(qq_data) > 1:
        stats.probplot(qq_data, dist="norm", plot=ax2)
        ax2.set_title("Normal Q-Q")
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Residual plot saved to {output_path}")
        return output_path
    
    return output_path

def run_analysis(
    results_path: Path,
    output_dir: Path,
    pre_col: str = "pre_treatment_score",
    post_col: str = "post_treatment_score",
    metric_col: str = "global_efficiency",
    confounds_cols: Optional[List[str]] = None
) -> Dict[str, Path]:
    """
    Run all plotting analyses for the statistical results.
    
    Args:
        results_path: Path to the statistical results CSV
        output_dir: Directory to save generated plots
        pre_col: Column name for pre-treatment scores
        post_col: Column name for post-treatment scores
        metric_col: Column name for the network metric
        confounds_cols: Optional list of confound column names
        
    Returns:
        Dictionary mapping plot types to their file paths
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    logger.info(f"Loading results from {results_path}")
    df = pd.read_csv(results_path)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plots_generated = {}
    
    # 1. Pre vs Post Scatter Plot
    try:
        plot_path = output_dir / "scatter_pre_post.png"
        generate_scatter_plot(
            data=df,
            x_col=pre_col,
            y_col=post_col,
            title="Pre-treatment vs Post-treatment Scores",
            x_label="Pre-treatment Score",
            y_label="Post-treatment Score",
            output_path=plot_path
        )
        plots_generated["pre_post_scatter"] = plot_path
    except Exception as e:
        logger.warning(f"Failed to generate pre-post scatter plot: {e}")
    
    # 2. Metric vs Post-treatment Scatter Plot
    try:
        plot_path = output_dir / "scatter_metric_post.png"
        generate_scatter_plot(
            data=df,
            x_col=metric_col,
            y_col=post_col,
            title=f"{metric_col} vs Post-treatment Scores",
            x_label=metric_col.replace('_', ' ').title(),
            y_label="Post-treatment Score",
            output_path=plot_path
        )
        plots_generated["metric_post_scatter"] = plot_path
    except Exception as e:
        logger.warning(f"Failed to generate metric-post scatter plot: {e}")
    
    # 3. Residual Diagnostics (if residuals are available)
    if 'residuals' in df.columns and 'fitted_values' in df.columns:
        try:
            plot_path = output_dir / "residual_diagnostics.png"
            generate_residual_plot(
                data=df,
                residuals_col='residuals',
                fitted_col='fitted_values',
                title="Residual Diagnostics",
                output_path=plot_path
            )
            plots_generated["residual_diagnostics"] = plot_path
        except Exception as e:
            logger.warning(f"Failed to generate residual diagnostics: {e}")
    
    # 4. Observed vs Fitted Plot
    if 'fitted_values' in df.columns and post_col in df.columns:
        try:
            plot_path = output_dir / "observed_vs_fitted.png"
            generate_regression_line_plot(
                data=df,
                x_col=post_col,
                y_col='fitted_values',
                title="Observed vs Fitted Post-treatment Scores",
                x_label="Observed Post-treatment",
                y_label="Fitted Post-treatment",
                output_path=plot_path
            )
            plots_generated["observed_vs_fitted"] = plot_path
        except Exception as e:
            logger.warning(f"Failed to generate observed vs fitted plot: {e}")
    
    logger.info(f"Generated {len(plots_generated)} plots in {output_dir}")
    return plots_generated

def main():
    """Main entry point for plotting analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate plots for statistical analysis results")
    parser.add_argument(
        "--results-path",
        type=str,
        required=True,
        help="Path to the statistical results CSV file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/figures",
        help="Directory to save generated plots"
    )
    parser.add_argument(
        "--pre-col",
        type=str,
        default="pre_treatment_score",
        help="Column name for pre-treatment scores"
    )
    parser.add_argument(
        "--post-col",
        type=str,
        default="post_treatment_score",
        help="Column name for post-treatment scores"
    )
    parser.add_argument(
        "--metric-col",
        type=str,
        default="global_efficiency",
        help="Column name for the network metric"
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    results_path = Path(args.results_path)
    output_dir = Path(args.output_dir)
    
    try:
        plots = run_analysis(
            results_path=results_path,
            output_dir=output_dir,
            pre_col=args.pre_col,
            post_col=args.post_col,
            metric_col=args.metric_col
        )
        
        logger.info("Plot generation completed successfully")
        for plot_type, path in plots.items():
            logger.info(f"  - {plot_type}: {path}")
            
    except Exception as e:
        logger.error(f"Plot generation failed: {e}")
        raise

if __name__ == "__main__":
    main()