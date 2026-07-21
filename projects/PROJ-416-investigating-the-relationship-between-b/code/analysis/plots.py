import os
import logging
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from code.config import Config

logger = logging.getLogger(__name__)

def generate_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, output_path: Path) -> None:
    """
    Generate scatter plot with regression line.
    
    Args:
        df: DataFrame with data
        x_col: X-axis column name
        y_col: Y-axis column name
        output_path: Output file path
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.6)
    
    # Add regression line
    z = np.polyfit(df[x_col], df[y_col], 1)
    p = np.poly1d(z)
    plt.plot(df[x_col], p(df[x_col]), "r--")
    
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f"{y_col} vs {x_col}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved scatter plot to {output_path}")

def generate_regression_line_plot(df: pd.DataFrame, x_col: str, y_col: str, output_path: Path) -> None:
    """
    Generate regression line plot.
    
    Args:
        df: DataFrame with data
        x_col: X-axis column name
        y_col: Y-axis column name
        output_path: Output file path
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.6, label='Data')
    
    # Regression
    z = np.polyfit(df[x_col], df[y_col], 1)
    p = np.poly1d(z)
    plt.plot(df[x_col], p(df[x_col]), "r--", label=f'Fit: y={z[0]:.2f}x+{z[1]:.2f}')
    
    plt.legend()
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f"Regression: {y_col} ~ {x_col}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved regression plot to {output_path}")

def generate_residual_plot(df: pd.DataFrame, x_col: str, y_col: str, output_path: Path) -> None:
    """
    Generate residual plot.
    
    Args:
        df: DataFrame with data
        x_col: X-axis column name
        y_col: Y-axis column name
        output_path: Output file path
    """
    # Calculate residuals
    z = np.polyfit(df[x_col], df[y_col], 1)
    p = np.poly1d(z)
    residuals = df[y_col] - p(df[x_col])
    
    plt.figure(figsize=(10, 6))
    plt.scatter(p(df[x_col]), residuals, alpha=0.6)
    plt.axhline(0, color='r', linestyle='--')
    
    plt.xlabel("Fitted values")
    plt.ylabel("Residuals")
    plt.title("Residual Plot")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved residual plot to {output_path}")

def run_analysis(config: Config) -> None:
    """
    Run plotting analysis.
    
    Args:
        config: Configuration object
    """
    metrics_path = config.METRICS_DIR / "network_metrics.csv"
    if not metrics_path.exists():
        logger.warning(f"Metrics file not found: {metrics_path}")
        return
        
    df = pd.read_csv(metrics_path)
    
    if len(df) < 2:
        logger.warning("Insufficient data for plotting")
        return
        
    # Generate plots
    plots_dir = config.REPORTS_DIR / "figures"
    
    generate_scatter_plot(df, "modularity", "post_treatment_score", plots_dir / "scatter_modularity.png")
    generate_regression_line_plot(df, "modularity", "post_treatment_score", plots_dir / "regression_modularity.png")
    generate_residual_plot(df, "modularity", "post_treatment_score", plots_dir / "residual_modularity.png")
    
    logger.info("Plotting complete.")

def ensure_directories(config: Config) -> None:
    """
    Ensure required directories exist.
    
    Args:
        config: Configuration object
    """
    (config.REPORTS_DIR / "figures").mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point."""
    config = Config()
    ensure_directories(config)
    run_analysis(config)

if __name__ == "__main__":
    main()
