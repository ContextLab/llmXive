import json
import logging
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from code.config import CONFIG
import seaborn as sns

logger = logging.getLogger(__name__)

def load_analysis_data():
    """
    Loads the final analysis data from the merged CSV file.
    
    Returns:
        pd.DataFrame: The loaded analysis data with control_proxy and anxiety_score columns.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    input_path = CONFIG.OUTPUT_DIR / "final_analysis.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['control_proxy', 'anxiety_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    # Drop rows with NaN values in required columns
    df = df.dropna(subset=required_cols)
    
    logger.info(f"Loaded {len(df)} records for visualization from {input_path}")
    return df

def calculate_regression_line(x: np.ndarray, y: np.ndarray):
    """
    Calculates the regression line for the scatter plot.
    
    Args:
        x: Array of control_proxy values.
        y: Array of anxiety_score values.
        
    Returns:
        tuple: (x_sorted, y_regression) sorted by x values.
    """
    # Calculate linear regression coefficients
    slope, intercept = np.polyfit(x, y, 1)
    
    # Create sorted x values for smooth line
    x_sorted = np.sort(x)
    y_regression = slope * x_sorted + intercept
    
    return x_sorted, y_regression

def generate_scatter_plot(df: pd.DataFrame):
    """
    Generates a scatter plot with regression line showing the correlation
    between control_proxy and anxiety_score.
    
    Args:
        df: DataFrame containing control_proxy and anxiety_score columns.
        
    Returns:
        tuple: (fig, ax) matplotlib figure and axis objects.
    """
    # Set the style
    sns.set_style("darkgrid")
    
    # Extract data
    x = df['control_proxy'].values
    y = df['anxiety_score'].values
    
    # Create figure with specified dimensions: 8x6 inches
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    
    # Create scatter plot
    ax.scatter(x, y, alpha=0.6, s=30, edgecolors='w', linewidth=0.5, label='Data Points')
    
    # Calculate and plot regression line
    x_reg, y_reg = calculate_regression_line(x, y)
    ax.plot(x_reg, y_reg, 'r-', linewidth=2, label='Regression Line')
    
    # Labels and title
    ax.set_xlabel('Control Proxy Score', fontsize=12, fontweight='bold')
    ax.set_ylabel('Anxiety Score', fontsize=12, fontweight='bold')
    ax.set_title('Correlation Between Perceived Control and Anxiety', fontsize=14, fontweight='bold')
    
    # Add legend
    ax.legend(loc='best', fontsize=10)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Ensure layout is tight
    plt.tight_layout()
    
    return fig, ax

def run_visualization_pipeline():
    """
    Runs the complete visualization pipeline:
    1. Load analysis data
    2. Generate scatter plot with regression line
    3. Return figure and axis for saving
    
    Returns:
        tuple: (fig, ax) matplotlib figure and axis objects.
        
    Raises:
        FileNotFoundError: If input data file is missing.
        ValueError: If data processing fails.
    """
    logger.info("Starting visualization pipeline...")
    
    # Load data
    df = load_analysis_data()
    
    # Generate plot
    fig, ax = generate_scatter_plot(df)
    
    logger.info("Visualization pipeline completed successfully.")
    return fig, ax
