"""
Visualization module for plotting correlation between control proxy and anxiety scores.
Generates a scatter plot with a regression line and axis labels.
"""
import json
import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_analysis_data(data_path: Path) -> pd.DataFrame:
    """
    Load the final analysis dataset containing control_proxy and anxiety_score.
    
    Args:
        data_path: Path to the CSV file (data/processed/final_analysis.csv)
        
    Returns:
        DataFrame with required columns
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Analysis data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    required_cols = ['control_proxy', 'anxiety_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {data_path}: {missing}")
    
    # Drop rows with NaN in critical columns
    df = df.dropna(subset=required_cols)
    logger.info(f"Loaded {len(df)} rows for visualization after dropping NaNs")
    return df

def calculate_regression_line(x: np.ndarray, y: np.ndarray) -> tuple:
    """
    Calculate the regression line parameters (slope, intercept) using OLS.
    Falls back to a robust rank-based approach if OLS fails.
    
    Args:
        x: Independent variable (control_proxy)
        y: Dependent variable (anxiety_score)
        
    Returns:
        Tuple of (slope, intercept)
    """
    try:
        # Try standard OLS first
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return slope, intercept
    except Exception as e:
        logger.warning(f"OLS regression failed ({e}), falling back to rank-based (Theil-Sen) approach")
        # Fallback: Theil-Sen estimator for robustness
        from sklearn.linear_model import TheilSenRegressor
        x_reshaped = x.reshape(-1, 1)
        model = TheilSenRegressor(random_state=42)
        model.fit(x_reshaped, y)
        return model.coef_[0], model.intercept_

def generate_scatter_plot(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Correlation: Perceived Control vs Anxiety",
    x_label: str = "Control Proxy Score",
    y_label: str = "Anxiety Score",
    figsize: tuple = (10, 8)
) -> None:
    """
    Generate a scatter plot with a regression line and save it.
    
    Args:
        df: DataFrame with 'control_proxy' and 'anxiety_score'
        output_path: Path to save the plot (e.g., data/processed/correlation_plot.png)
        title: Plot title
        x_label: X-axis label
        y_label: Y-axis label
        figsize: Figure size (width, height)
    """
    if output_path.exists():
        output_path.unlink()
    
    plt.figure(figsize=figsize)
    sns.set_style("whitegrid")
    
    x = df['control_proxy'].values
    y = df['anxiety_score'].values
    
    # Scatter plot
    sns.scatterplot(
        x=x,
        y=y,
        alpha=0.6,
        edgecolor='k',
        s=40,
        color='steelblue'
    )
    
    # Regression line
    slope, intercept = calculate_regression_line(x, y)
    x_range = np.linspace(x.min(), x.max(), 100)
    y_pred = slope * x_range + intercept
    
    plt.plot(x_range, y_pred, 'r-', linewidth=2.5, label=f'Fit: y = {slope:.3f}x + {intercept:.3f}')
    
    # Calculate and display correlation coefficient
    corr, _ = stats.pearsonr(x, y)
    plt.text(
        0.05, 0.95,
        f'Pearson r = {corr:.3f}',
        transform=plt.gca().transAxes,
        fontsize=12,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.legend()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, format='png')
    plt.close()
    
    logger.info(f"Visualization saved to: {output_path}")

def run_visualization_pipeline(
    input_data_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Main entry point to run the visualization pipeline.
    
    Args:
        input_data_path: Path to final_analysis.csv (defaults to project config)
        output_path: Path to save the plot (defaults to project config)
        
    Returns:
        Path to the generated plot
    """
    # Default paths based on project structure
    if input_data_path is None:
        input_data_path = Path("data/processed/final_analysis.csv")
    if output_path is None:
        output_path = Path("data/processed/correlation_plot.png")
    
    logger.info(f"Starting visualization pipeline...")
    logger.info(f"Input data: {input_data_path}")
    logger.info(f"Output plot: {output_path}")
    
    # Load data
    df = load_analysis_data(input_data_path)
    
    # Generate plot
    generate_scatter_plot(df, output_path)
    
    logger.info("Visualization pipeline completed successfully.")
    return output_path

if __name__ == "__main__":
    run_visualization_pipeline()
