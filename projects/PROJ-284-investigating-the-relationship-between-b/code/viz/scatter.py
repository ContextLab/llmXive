"""
Scatter plot generator for correlation results.
Task: T031 (Implementation referenced by T029 test)
"""
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import stats
from code.logging_config import get_logger

logger = get_logger(__name__)

def generate_scatter_plot(
    input: str = None,
    input_data: str = None,
    x: str = None,
    y: str = None,
    x_col: str = None,
    y_col: str = None,
    x_label: str = "Metric",
    y_label: str = "Score",
    output: str = None,
    output_path: str = None,
    title: str = "Correlation Plot",
    **kwargs
):
    """
    Generate a scatter plot with regression line and annotations.
    
    This function is designed to be tolerant of different call signatures:
    - Positional args: input, x, y, output
    - Keyword args: input_data, x_col, y_col, output_path, etc.
    
    Args:
        input: Path to input CSV (positional)
        input_data: Path to input CSV (keyword)
        x: X column name (positional)
        y: Y column name (positional)
        x_col: X column name (keyword)
        y_col: Y column name (keyword)
        x_label: Label for X axis
        y_label: Label for Y axis
        output: Output path (positional)
        output_path: Output path (keyword)
        title: Plot title
        **kwargs: Additional arguments (ignored)
    """
    # Resolve input path
    data_path = input or input_data
    if not data_path:
        raise ValueError("Input data path must be provided")
    
    # Resolve column names
    x_column = x or x_col
    if not x_column:
        raise ValueError("X column name must be provided")
    
    y_column = y or y_col
    if not y_column:
        raise ValueError("Y column name must be provided")
    
    # Resolve output path
    out_path = output or output_path
    if not out_path:
        raise ValueError("Output path must be provided")
    
    # Ensure output directory exists
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    # Load data
    logger.log("scatter_plot_load_data", path=data_path)
    df = pd.read_csv(data_path)
    
    if x_column not in df.columns:
        raise ValueError(f"Column '{x_column}' not found in data. Available: {list(df.columns)}")
    if y_column not in df.columns:
        raise ValueError(f"Column '{y_column}' not found in data. Available: {list(df.columns)}")
    
    x_data = df[x_column].dropna()
    y_data = df[y_column].dropna()
    
    # Align indices after dropna
    common_idx = x_data.index.intersection(y_data.index)
    x_data = x_data.loc[common_idx]
    y_data = y_data.loc[common_idx]
    
    if len(x_data) < 2:
        logger.log("scatter_plot_insufficient_data", count=len(x_data))
        raise ValueError("Insufficient data points for correlation (need >= 2)")
    
    # Calculate correlation
    r, p_value = stats.pearsonr(x_data, y_data)
    n = len(x_data)
    
    # Generate plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    ax.scatter(x_data, y_data, alpha=0.6, edgecolors='w', linewidth=0.5, label=f'n={n}')
    
    # Regression line
    if n >= 2:
        slope, intercept, r_val, p_val, std_err = stats.linregress(x_data, y_data)
        x_line = np.linspace(x_data.min(), x_data.max(), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_val:.3f})')
    
    # Annotations
    # Format p-value appropriately (scientific notation if very small)
    if p_value < 0.001:
        p_str = f'< 0.001'
    else:
        p_str = f'{p_value:.3f}'
        
    annotation_text = f'r = {r:.3f}\np = {p_str}\nn = {n}'
    ax.text(0.05, 0.95, annotation_text, transform=ax.transAxes, 
            fontsize=12, verticalalignment='top', 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Labels and title
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save figure
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    logger.log("scatter_plot_saved", path=out_path, r=r, p=p_value, n=n)
    
    plt.close(fig)
    
    return out_path

def main():
    """CLI entry point for scatter plot generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate scatter plot from correlation data")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file path")
    parser.add_argument("--x", required=True, help="X column name")
    parser.add_argument("--y", required=True, help="Y column name")
    parser.add_argument("--output", "-o", required=True, help="Output PNG file path")
    parser.add_argument("--x-label", default="Metric", help="X axis label")
    parser.add_argument("--y-label", default="Score", help="Y axis label")
    parser.add_argument("--title", default="Correlation Plot", help="Plot title")
    
    args = parser.parse_args()
    
    generate_scatter_plot(
        input=args.input,
        x=args.x,
        y=args.y,
        x_label=args.x_label,
        y_label=args.y_label,
        output=args.output,
        title=args.title
    )
    
    print(f"Plot saved to: {args.output}")

if __name__ == "__main__":
    main()
