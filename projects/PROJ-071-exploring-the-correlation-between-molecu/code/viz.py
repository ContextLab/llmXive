import json
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from scipy import stats
from config import get_config
from logging_config import get_logger

# Use config for paths
def get_data_path(relative_path: str) -> Path:
    config = get_config()
    return Path(config.get("data_dir", "data")) / relative_path

def load_analysis_results() -> Dict[str, Any]:
    """
    Loads analysis results from JSON.
    """
    path = get_data_path("processed/analysis_results.json")
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def load_residuals_data() -> Tuple[pd.Series, pd.Series]:
    """
    Loads residuals data for plotting.
    """
    # Assuming residuals are calculated in analysis.py and saved
    # For now, we'll re-calculate or load from a file if available
    # This is a placeholder implementation
    return pd.Series(), pd.Series()

def plot_scatter_with_regression(x: pd.Series, y: pd.Series, title: str, output_path: Path):
    """
    Plots scatter plot with regression line.
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=x, y=y)
    
    # Fit regression line
    model = LinearRegression()
    model.fit(x.values.reshape(-1, 1), y)
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = model.predict(x_line.reshape(-1, 1))
    plt.plot(x_line, y_line, color='red', label='Regression Line')
    
    plt.title(title)
    plt.xlabel(x.name)
    plt.ylabel(y.name)
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def generate_correlation_scatter_plots(df: pd.DataFrame, feature_cols: List[str], target_col: str, output_dir: Path):
    """
    Generates scatter plots for top correlated features.
    """
    logger = get_logger(__name__)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for col in feature_cols:
        title = f"{col} vs {target_col}"
        output_path = output_dir / f"scatter_{col}_vs_{target_col}.png"
        plot_scatter_with_regression(df[col], df[target_col], title, output_path)
        logger.info(f"Saved plot to {output_path}")

def plot_residual_histogram(residuals: pd.Series, output_path: Path):
    """
    Plots histogram of residuals.
    """
    plt.figure(figsize=(10, 6))
    plt.hist(residuals, bins=30, edgecolor='black')
    plt.title('Residual Histogram')
    plt.xlabel('Residuals')
    plt.ylabel('Frequency')
    plt.savefig(output_path)
    plt.close()

def plot_qq_plot(residuals: pd.Series, output_path: Path):
    """
    Plots QQ plot of residuals.
    """
    plt.figure(figsize=(10, 6))
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title('QQ Plot of Residuals')
    plt.savefig(output_path)
    plt.close()

def plot_residuals_vs_fitted(y_true: pd.Series, y_pred: pd.Series, output_path: Path):
    """
    Plots residuals vs fitted values.
    """
    residuals = y_true - y_pred
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred, residuals)
    plt.axhline(0, color='red', linestyle='--')
    plt.title('Residuals vs Fitted')
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.savefig(output_path)
    plt.close()

def generate_residual_diagnostic_plots(y_true: pd.Series, y_pred: pd.Series, output_dir: Path):
    """
    Generates residual diagnostic plots.
    """
    logger = get_logger(__name__)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    residuals = y_true - y_pred
    
    # Histogram
    plot_residual_histogram(residuals, output_dir / "residual_histogram.png")
    
    # QQ Plot
    plot_qq_plot(residuals, output_dir / "qq_plot.png")
    
    # Residuals vs Fitted
    plot_residuals_vs_fitted(y_true, y_pred, output_dir / "residuals_vs_fitted.png")
    
    # Combined residuals plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    axes[0].hist(residuals, bins=30, edgecolor='black')
    axes[0].set_title('Residual Histogram')
    axes[0].set_xlabel('Residuals')
    axes[0].set_ylabel('Frequency')
    
    stats.probplot(residuals, dist="norm", plot=axes[1])
    axes[1].set_title('QQ Plot')
    
    axes[2].scatter(y_pred, residuals)
    axes[2].axhline(0, color='red', linestyle='--')
    axes[2].set_title('Residuals vs Fitted')
    axes[2].set_xlabel('Fitted Values')
    axes[2].set_ylabel('Residuals')
    
    plt.tight_layout()
    plt.savefig(output_dir / "residuals.png")
    plt.close()
    logger.info(f"Saved residual diagnostic plots to {output_dir}")

def main():
    """
    Main entry point for visualization.
    """
    logger = get_logger(__name__)
    logger.info("Starting visualization pipeline...")
    
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    outputs_dir = data_dir / "outputs"
    processed_dir = data_dir / "processed"
    
    # Check if data availability gate passed
    merged_path = processed_dir / "merged_drugs.csv"
    if not merged_path.exists():
        logger.warning("Merged dataset not found. Skipping visualization.")
        return
    
    df = pd.read_csv(merged_path)
    if len(df) < 30:
        logger.warning("Data insufficient (N < 30). Skipping visualization.")
        return
    
    # Generate correlation scatter plots
    feature_cols = ['tpsa', 'rotatable_bonds', 'mw', 'aromatic_rings', 'wiener_index', 'zagreb_index']
    target_col = 'half_life'
    generate_correlation_scatter_plots(df, feature_cols, target_col, outputs_dir)
    
    # Generate residual diagnostic plots
    # Assuming we have y_pred from analysis
    # For now, we'll use a simple linear model
    from sklearn.linear_model import LinearRegression
    X = df[feature_cols]
    y = df[target_col]
    model = LinearRegression().fit(X, y)
    y_pred = model.predict(X)
    generate_residual_diagnostic_plots(y, y_pred, outputs_dir)
    
    logger.info("Visualization pipeline completed.")

if __name__ == "__main__":
    main()
