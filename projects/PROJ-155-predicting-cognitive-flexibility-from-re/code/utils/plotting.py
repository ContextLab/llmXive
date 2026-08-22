import os
import logging
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from code.data.paths import get_results_path, get_processed_path, ensure_dir
from code.analysis.regression import load_regression_dataset
from code.analysis.p_value_formatter import format_p_value

logger = logging.getLogger(__name__)

def load_regression_plot_data() -> pd.DataFrame:
    """
    Loads the final results dataset required for plotting.
    Expects 'data/processed/final_results.csv' to exist (produced by T036).
    Falls back to 'data/processed/metrics.csv' joined with regression summary
    if final_results is not yet available, but prioritizes final_results.
    """
    final_results_path = os.path.join(get_processed_path(), "final_results.csv")
    metrics_path = os.path.join(get_processed_path(), "metrics.csv")
    regression_summary_path = os.path.join(get_results_path(), "regression_summary.json")

    if os.path.exists(final_results_path):
        logger.info(f"Loading plot data from {final_results_path}")
        df = pd.read_csv(final_results_path)
        # Ensure required columns exist
        required_cols = ['Subject_ID', 'Variability_Metric', 'Flexibility_Score', 'Age', 'Sex', 'Mean_FD', 'Total_Scan_Time']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"final_results.csv missing required columns. Found: {df.columns.tolist()}")
        return df
    
    elif os.path.exists(metrics_path) and os.path.exists(regression_summary_path):
        logger.warning("final_results.csv not found. Attempting to construct plot data from metrics.csv and regression_summary.json.")
        df_metrics = pd.read_csv(metrics_path)
        
        import json
        with open(regression_summary_path, 'r') as f:
            summary = json.load(f)
        
        # We need Flexibility_Score, Age, Sex, Mean_FD, Total_Scan_Time to plot properly
        # If they are not in metrics.csv, we cannot plot the full regression context.
        # However, the task implies we plot Variability vs Flexibility.
        # If the full data isn't there, we can't do the full regression line with covariates easily 
        # without re-running the regression logic or having the merged data.
        # Assuming the pipeline ensures final_results.csv exists before this task runs (T036 dependency).
        # If not, we raise an error to prevent partial/fake plotting.
        raise FileNotFoundError(
            f"Cannot generate plot: {final_results_path} is missing. "
            "Task T036 (Merge and produce final_results.csv) must run before T035."
        )
    else:
        raise FileNotFoundError(
            f"Required data files not found. Looked for: {final_results_path}"
        )

def calculate_regression_line(
    x: np.ndarray, 
    y: np.ndarray, 
    covariates: Optional[pd.DataFrame] = None,
    beta: Optional[float] = None,
    intercept: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculates the regression line points for plotting.
    
    If beta and intercept are provided (from the saved summary), uses those.
    Otherwise, performs a simple linear regression on the provided x, y data
    (ignoring covariates for the simple line, which is standard for bivariate plots
    unless partial regression is explicitly requested. The spec asks for "regression line",
    usually implying the fitted line from the model. If the model is multivariate,
    the 2D plot of X vs Y should show the marginal relationship or the partial residual.
    Given the context of "Variability vs Flexibility", a simple bivariate fit
    or the marginal line from the multivariate model (adjusted) is best.
    
    For this implementation, we will calculate the simple linear regression line
    (y = mx + c) on the provided data to visualize the trend, as the full
    multivariate fit cannot be projected into 2D without partial residual logic.
    However, if the user wants the *model* line, they might expect the multivariate prediction.
    Since we only have X (Variability) on the axis, we fit Y ~ X here for the visual line.
    """
    if beta is not None and intercept is not None:
        # If we have the multivariate coefficients, we can't directly plot them
        # against X alone without adjusting for covariates. 
        # We will fall back to simple OLS on the provided data for the visual line,
        # or use the provided beta if it's from a simple regression.
        # Given the ambiguity, we perform simple OLS on the current data points.
        pass

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    x_line = np.array([np.min(x), np.max(x)])
    y_line = slope * x_line + intercept
    return x_line, y_line

def plot_variability_vs_flexibility(
    output_path: Optional[str] = None,
    title: str = "Cognitive Flexibility vs. Functional Connectivity Variability",
    figsize: Tuple[int, int] = (10, 8),
    show_ci: bool = True,
    ci_level: float = 0.95
) -> str:
    """
    Generates a scatter plot of Variability_Metric vs Flexibility_Score with a regression line and confidence interval.
    
    Args:
        output_path: Path to save the figure. If None, returns the path where it would be saved.
        title: Plot title.
        figsize: Figure size (width, height).
        show_ci: Whether to show the confidence interval shading.
        ci_level: Confidence level for the interval (e.g., 0.95 for 95%).
    
    Returns:
        The path where the figure was saved.
    """
    logger.info("Loading data for plotting...")
    df = load_regression_plot_data()

    if df.empty:
        raise ValueError("No data available to plot. The dataset is empty.")

    x_col = 'Variability_Metric'
    y_col = 'Flexibility_Score'

    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Missing required columns. Expected '{x_col}' and '{y_col}'. Found: {df.columns.tolist()}")

    x = df[x_col].dropna()
    y = df[y_col].dropna()
    
    # Ensure alignment
    mask = ~df[x_col].isna() & ~df[y_col].isna()
    x = df.loc[mask, x_col].values
    y = df.loc[mask, y_col].values

    if len(x) == 0:
        raise ValueError("No valid data points after removing NaNs.")

    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Scatter plot
    ax.scatter(x, y, alpha=0.6, edgecolors='w', s=50, label='Subjects')
    
    # Regression line and CI
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    x_line = np.array([np.min(x), np.max(x)])
    y_line = slope * x_line + intercept
    
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression Line (r={r_value:.3f}, p={format_p_value(p_value)})')
    
    if show_ci:
        # Calculate confidence interval for the mean response
        n = len(x)
        x_mean = np.mean(x)
        ss_xx = np.sum((x - x_mean)**2)
        
        # Standard error of the prediction
        # SE = std_err * sqrt(1/n + (x - x_mean)^2 / SS_xx)
        # But for the confidence band of the regression line (mean response):
        # SE_mean = std_err * sqrt(1/n + (x - x_mean)^2 / SS_xx)
        
        t_val = stats.t.ppf(1 - (1 - ci_level) / 2, n - 2)
        
        y_lower = y_line - t_val * std_err * np.sqrt(1/n + (x_line - x_mean)**2 / ss_xx)
        y_upper = y_line + t_val * std_err * np.sqrt(1/n + (x_line - x_mean)**2 / ss_xx)
        
        ax.fill_between(x_line, y_lower, y_upper, color='red', alpha=0.2, label=f'{int(ci_level*100)}% CI')

    # Labels and Title
    ax.set_xlabel('Variability Metric (Mean Edge SD)', fontsize=12)
    ax.set_ylabel('Flexibility Score (DCCS)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    # Determine output path
    if output_path is None:
        output_path = os.path.join(get_results_path(), "variability_vs_flexibility.png")
    
    ensure_dir(output_path)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    logger.info(f"Plot saved to {output_path}")
    return output_path

def main():
    """
    Entry point for generating the variability vs flexibility plot.
    """
    set_seed = 42 # Default seed from config
    try:
        output_path = plot_variability_vs_flexibility()
        print(f"Successfully generated plot: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}")
        raise

if __name__ == "__main__":
    main()