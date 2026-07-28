import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
from logging_config import logger

def plot_scatter_with_regression(x: np.ndarray, y: np.ndarray, xlabel: str, ylabel: str, output_path: str):
    """
    Generate a scatter plot with a regression line and annotations.
    """
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    # Scatter
    plt.scatter(x, y, alpha=0.6, label='Data Points')
    
    # Regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    line_x = np.linspace(min(x), max(x), 100)
    line_y = slope * line_x + intercept
    plt.plot(line_x, line_y, 'r-', label=f'Regression (r={r_value:.3f})')
    
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f'{ylabel} vs {xlabel}')
    plt.legend()
    
    # Save
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved plot to {output_path}")
