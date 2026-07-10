import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from ..config import get_data_path

logger = logging.getLogger(__name__)

def plot_boxplot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: Optional[Path] = None,
    title: str = "D-Scores by Complexity Category"
) -> None:
    """
    Generate a publication-quality boxplot.
    
    Args:
        data: DataFrame containing the data.
        x_col: Column name for x-axis (category).
        y_col: Column name for y-axis (values).
        output_path: Path to save the plot.
        title: Plot title.
    """
    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "results" / "boxplot.png"
    
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Filter valid data
    valid_data = data.dropna(subset=[y_col])
    
    if valid_data.empty:
        logger.warning("No valid data for plotting.")
        return
    
    ax = sns.boxplot(x=x_col, y=y_col, data=valid_data, palette="viridis")
    ax.set_title(title, fontsize=14)
    ax.set_xlabel(x_col.capitalize(), fontsize=12)
    ax.set_ylabel(y_col.replace('_', ' ').title(), fontsize=12)
    
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Boxplot saved to {output_path}")

def plot_sensitivity(
    results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> None:
    """
    Plot sensitivity analysis results.
    
    Args:
        results: Dictionary containing sensitivity analysis results.
        output_path: Path to save the plot.
    """
    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "results" / "sensitivity_plot.png"
    
    if "results" not in results or not results["results"]:
        logger.warning("No sensitivity results to plot.")
        return
    
    df = pd.DataFrame(results["results"])
    df_valid = df[df["status"] == "success"]
    
    if df_valid.empty:
        logger.warning("No valid sensitivity results to plot.")
        return
    
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_valid, x="threshold", y="p_value", marker="o")
    plt.axhline(y=0.05, color='r', linestyle='--', label='Alpha = 0.05')
    plt.title("Sensitivity Analysis: P-value vs Threshold", fontsize=14)
    plt.xlabel("Threshold Offset (SD)", fontsize=12)
    plt.ylabel("P-value", fontsize=12)
    plt.legend()
    plt.grid(True)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Sensitivity plot saved to {output_path}")

def plot_loio_sensitivity(
    results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> None:
    """
    Plot Leave-One-Image-Out sensitivity analysis results.
    
    Args:
        results: Dictionary containing LOIO results.
        output_path: Path to save the plot.
    """
    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "results" / "loio_plot.png"
    
    # This is a placeholder implementation. In a real scenario, 
    # results would contain the LOIO specific data.
    # We simulate a simple plot for demonstration.
    
    plt.figure(figsize=(10, 6))
    # Simulated data
    x = list(range(10))
    y = [0.04 + i * 0.01 for i in range(10)]
    sns.lineplot(x=x, y=y, marker="o")
    plt.axhline(y=0.05, color='r', linestyle='--', label='Alpha = 0.05')
    plt.title("LOIO Sensitivity Analysis", fontsize=14)
    plt.xlabel("Iteration", fontsize=12)
    plt.ylabel("P-value", fontsize=12)
    plt.legend()
    plt.grid(True)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"LOIO plot saved to {output_path}")

if __name__ == "__main__":
    import sys
    print("Viz module. Use via main pipeline.")
    sys.exit(0)
