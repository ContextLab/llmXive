import json
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def get_data_path():
    config = get_config()
    return Path(config.get("data_dir", "data"))

def load_analysis_results() -> Dict[str, Any]:
    """
    Load analysis results from JSON file.
    """
    input_path = get_data_path() / "processed" / "analysis_results.json"
    if not input_path.exists():
        logger.error(f"Analysis results file not found: {input_path}")
        return {}
    with open(input_path, 'r') as f:
        return json.load(f)

def load_residuals_data() -> pd.DataFrame:
    """
    Load residuals data for plotting.
    """
    # Assuming residuals are stored in a separate file or can be derived
    # For now, we'll load the standard subset and compute residuals
    input_path = get_data_path() / "processed" / "standard_subset.csv"
    if not input_path.exists():
        logger.error(f"Standard subset file not found: {input_path}")
        return pd.DataFrame()
    df = pd.read_csv(input_path)
    return df

def plot_scatter_with_regression(df: pd.DataFrame, x_col: str, y_col: str, output_path: Path):
    """
    Plot scatter plot with regression line.
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=df[x_col], y=df[y_col])
    
    # Fit regression line
    slope, intercept, r_value, p_value, std_err = stats.linregress(df[x_col], df[y_col])
    x_vals = np.array([df[x_col].min(), df[x_col].max()])
    y_vals = slope * x_vals + intercept
    plt.plot(x_vals, y_vals, 'r-', label=f'Regression Line (R²={r_value**2:.2f})')
    
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f'{y_col} vs {x_col}')
    plt.legend()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved scatter plot to {output_path}")

def generate_correlation_scatter_plots(df: pd.DataFrame, top_features: List[str], target_col: str, output_dir: Path):
    """
    Generate scatter plots for top correlated features.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for feature in top_features:
        output_path = output_dir / f"scatter_{feature}_vs_{target_col}.png"
        plot_scatter_with_regression(df, feature, target_col, output_path)

def plot_residual_histogram(residuals: np.ndarray, output_path: Path):
    """
    Plot histogram of residuals.
    """
    plt.figure(figsize=(10, 6))
    plt.hist(residuals, bins=30, edgecolor='black')
    plt.xlabel('Residuals')
    plt.ylabel('Frequency')
    plt.title('Histogram of Residuals')
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved residual histogram to {output_path}")

def plot_qq_plot(residuals: np.ndarray, output_path: Path):
    """
    Plot QQ plot of residuals.
    """
    plt.figure(figsize=(10, 6))
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title('QQ Plot of Residuals')
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved QQ plot to {output_path}")

def plot_residuals_vs_fitted(y_pred: np.ndarray, residuals: np.ndarray, output_path: Path):
    """
    Plot residuals vs fitted values.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred, residuals)
    plt.axhline(0, color='red', linestyle='--')
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted Values')
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved residuals vs fitted plot to {output_path}")

def generate_residual_diagnostic_plots(y_true: pd.Series, y_pred: np.ndarray, output_dir: Path):
    """
    Generate all residual diagnostic plots.
    """
    residuals = y_true - y_pred
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plot_residual_histogram(residuals, output_dir / "residuals.png")
    plot_qq_plot(residuals, output_dir / "qq_plot.png")
    plot_residuals_vs_fitted(y_pred, residuals, output_dir / "residuals_vs_fitted.png")

def main():
    config = get_config()
    logger.info("Starting visualization")
    
    # Check if data availability gate passed
    # This is a simplified check; in reality, we'd check the actual gate status
    data_dir = get_data_path()
    merged_path = data_dir / "processed" / "merged_drugs.csv"
    if not merged_path.exists():
        logger.warning("Merged dataset not found. Skipping visualization.")
        return
    
    df = pd.read_csv(merged_path)
    if len(df) < 30:
        logger.warning("Data insufficient (N < 30). Skipping visualization.")
        return
    
    # Load analysis results
    results = load_analysis_results()
    if not results:
        logger.error("Analysis results not found. Cannot generate plots.")
        return
    
    # Load standard subset
    standard_df = load_residuals_data()
    if standard_df.empty:
        logger.error("Standard subset not found. Cannot generate plots.")
        return
    
    # Generate correlation scatter plots
    output_dir = data_dir / "outputs"
    top_features = ['tpsa', 'rotatable_bonds', 'mw']  # Example top features
    generate_correlation_scatter_plots(standard_df, top_features, 'half_life', output_dir)
    
    # Generate residual diagnostic plots
    y_pred = LinearRegression().fit(standard_df[top_features], standard_df['half_life']).predict(standard_df[top_features])
    generate_residual_diagnostic_plots(standard_df['half_life'], y_pred, output_dir)
    
    logger.info("Visualization complete")

if __name__ == "__main__":
    main()
