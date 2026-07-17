"""
Scatter plot generator for metric vs. score analysis.
Generates publication-quality plots with regression lines and annotated statistics.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Import from project modules
from code.logging_config import get_logger
from code.config import get_config

logger = get_logger(__name__)

# Ensure output directories exist
FIGURES_DIR = Path("data/analysis")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Style configuration
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.figsize"] = (10, 8)
plt.rcParams["font.size"] = 12
plt.rcParams["axes.labelsize"] = 14
plt.rcParams["axes.titlesize"] = 16

def load_correlation_results(csv_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load correlation results from CSV file.
    
    Args:
        csv_path: Path to the correlations CSV file. Defaults to data/analysis/correlations.csv
        
    Returns:
        DataFrame with correlation results
        
    Raises:
        FileNotFoundError: If the CSV file does not exist
    """
    if csv_path is None:
        csv_path = Path("data/analysis/correlations.csv")
    else:
        csv_path = Path(csv_path)
        
    if not csv_path.exists():
        raise FileNotFoundError(f"Correlation results file not found: {csv_path}")
        
    df = pd.read_csv(csv_path)
    logger.log("load_correlation_results", file=str(csv_path), rows=len(df))
    return df

def generate_scatter_plot(
    x_data: Union[np.ndarray, List[float], pd.Series],
    y_data: Union[np.ndarray, List[float], pd.Series],
    x_label: str,
    y_label: str,
    title: str,
    output_path: Union[str, Path],
    correlation_result: Optional[Dict[str, Any]] = None,
    color: str = "#2E86AB",
    marker: str = "o",
    size: int = 50,
    alpha: float = 0.6,
    show_regression: bool = True,
    show_confidence_interval: bool = True,
    confidence_level: float = 0.95,
) -> str:
    """
    Generate a scatter plot with optional regression line and statistical annotations.
    
    Args:
        x_data: X-axis data (metric values)
        y_data: Y-axis data (score values)
        x_label: Label for X-axis
        y_label: Label for Y-axis
        title: Plot title
        output_path: Path to save the plot (PNG or PDF)
        correlation_result: Optional dict with 'r', 'p', 'q' keys for annotation
        color: Color of data points
        marker: Marker style
        size: Marker size
        alpha: Transparency of markers
        show_regression: Whether to draw regression line
        show_confidence_interval: Whether to show 95% CI band
        confidence_level: Confidence level for interval
        
    Returns:
        Path to the saved figure
    """
    x = np.asarray(x_data)
    y = np.asarray(y_data)
    
    if len(x) != len(y):
        raise ValueError(f"x_data ({len(x)}) and y_data ({len(y)}) must have same length")
        
    if len(x) == 0:
        raise ValueError("Data arrays cannot be empty")
        
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    ax.scatter(x, y, c=color, marker=marker, s=size, alpha=alpha, label="Data points")
    
    # Regression line
    if show_regression and len(x) >= 2:
        # Fit linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Create regression line points
        x_line = np.array([x.min(), x.max()])
        y_line = slope * x_line + intercept
        
        # Plot regression line
        ax.plot(x_line, y_line, color="#A23B72", linewidth=2, label=f"Regression (r={r_value:.3f})")
        
        # Confidence interval
        if show_confidence_interval and len(x) >= 3:
            # Calculate confidence interval for regression
            n = len(x)
            x_mean = np.mean(x)
            ss_x = np.sum((x - x_mean) ** 2)
            
            # Predicted values and standard error
            y_pred = slope * x_line + intercept
            se_fit = std_err * np.sqrt(1/n + (x_line - x_mean)**2 / ss_x)
            
            # t-value for confidence level
            t_val = stats.t.ppf((1 + confidence_level) / 2, n - 2)
            
            # Confidence interval bounds
            ci_lower = y_pred - t_val * se_fit
            ci_upper = y_pred + t_val * se_fit
            
            ax.fill_between(x_line, ci_lower, ci_upper, color="#A23B72", alpha=0.2, 
                            label=f"{int(confidence_level*100)}% CI")
    
    # Annotate statistics
    if correlation_result:
        r = correlation_result.get('r', 0)
        p = correlation_result.get('p', 1.0)
        q = correlation_result.get('q', 1.0)
        
        # Format p-value
        if p < 0.001:
            p_str = "p < 0.001"
        else:
            p_str = f"p = {p:.3f}"
            
        # Format q-value (FDR corrected)
        if q < 0.05:
            sig_marker = " *"
        else:
            sig_marker = ""
            
        annotation_text = (
            f"r = {r:.3f}\n"
            f"{p_str}\n"
            f"FDR q = {q:.3f}{sig_marker}"
        )
        
        # Position annotation in upper left
        ax.annotate(
            annotation_text,
            xy=(0.05, 0.95),
            xycoords='axes fraction',
            verticalalignment='top',
            horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=11
        )
    
    # Labels and title
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    
    # Legend
    ax.legend(loc='best')
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.log("generate_scatter_plot", output=str(output_path), title=title)
    return str(output_path)

def generate_all_scatter_plots(
    correlations_df: Optional[pd.DataFrame] = None,
    metrics_df: Optional[pd.DataFrame] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> List[str]:
    """
    Generate scatter plots for all significant correlations.
    
    Args:
        correlations_df: DataFrame with correlation results (r, p, q, metric_name, subject_id)
        metrics_df: DataFrame with raw metric values and scores
        output_dir: Directory to save plots (defaults to data/analysis)
        
    Returns:
        List of paths to generated plot files
    """
    if output_dir is None:
        output_dir = Path("data/analysis")
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_plots = []
    
    # Load data if not provided
    if correlations_df is None:
        try:
            correlations_df = load_correlation_results()
        except FileNotFoundError:
            logger.log("generate_all_scatter_plots", warning="No correlations file found, skipping plot generation")
            return generated_plots
            
    if metrics_df is None:
        # Try to load from default location
        metrics_path = Path("data/processed/aggregated_metrics.csv")
        if metrics_path.exists():
            metrics_df = pd.read_csv(metrics_path)
        else:
            logger.log("generate_all_scatter_plots", warning="No metrics file found, skipping plot generation")
            return generated_plots
    
    # Filter for significant correlations (q < 0.05)
    significant_corrs = correlations_df[correlations_df['q'] < 0.05]
    
    if significant_corrs.empty:
        logger.log("generate_all_scatter_plots", info="No significant correlations to plot")
        # Still generate plots for top correlations even if not significant
        significant_corrs = correlations_df.nlargest(3, 'abs_r')
    
    # Generate plot for each significant correlation
    for _, row in significant_corrs.iterrows():
        metric_name = row['metric_name']
        r = row['r']
        p = row['p']
        q = row['q']
        
        # Get data for this metric
        if metric_name not in metrics_df.columns:
            logger.log("generate_all_scatter_plots", warning=f"Metric {metric_name} not found in data, skipping")
            continue
            
        x_data = metrics_df[metric_name]
        
        # Assuming motor_score or similar is the Y variable
        y_col = 'motor_score' if 'motor_score' in metrics_df.columns else metrics_df.columns[-1]
        y_data = metrics_df[y_col]
        
        # Create correlation result dict
        corr_result = {'r': r, 'p': p, 'q': q}
        
        # Generate plot
        plot_filename = f"scatter_{metric_name}.png"
        plot_path = output_dir / plot_filename
        
        try:
            generate_scatter_plot(
                x_data=x_data,
                y_data=y_data,
                x_label=metric_name.replace('_', ' ').title(),
                y_label=y_col.replace('_', ' ').title(),
                title=f"{metric_name.replace('_', ' ').title()} vs {y_col.replace('_', ' ').title()}",
                output_path=plot_path,
                correlation_result=corr_result,
            )
            generated_plots.append(str(plot_path))
            logger.log("generate_all_scatter_plots", success=True, plot=str(plot_path))
        except Exception as e:
            logger.log("generate_all_scatter_plots", error=str(e), metric=metric_name)
            
    return generated_plots

def main():
    """
    Main entry point for scatter plot generation.
    Loads correlation results and generates plots for all significant correlations.
    """
    logger.log("main", step="scatter_plot_generation")
    
    try:
        # Load correlation results
        correlations_df = load_correlation_results()
        
        # Load metrics data
        metrics_path = Path("data/processed/aggregated_metrics.csv")
        if not metrics_path.exists():
            logger.log("main", error="Metrics file not found", path=str(metrics_path))
            sys.exit(1)
            
        metrics_df = pd.read_csv(metrics_path)
        
        # Generate plots
        output_dir = Path("data/analysis")
        plots = generate_all_scatter_plots(
            correlations_df=correlations_df,
            metrics_df=metrics_df,
            output_dir=output_dir
        )
        
        logger.log("main", success=True, plots_generated=len(plots))
        print(f"Generated {len(plots)} scatter plots in {output_dir}")
        
    except Exception as e:
        logger.log("main", error=str(e))
        print(f"Error generating scatter plots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()