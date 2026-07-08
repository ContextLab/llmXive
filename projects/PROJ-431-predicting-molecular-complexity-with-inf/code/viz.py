import os
import logging
from typing import Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for script execution
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

logger = logging.getLogger(__name__)

def compute_regression_metrics(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Compute linear regression metrics: slope, intercept, r_value, p_value, std_err.
    
    Args:
        x: Independent variable array
        y: Dependent variable array
        
    Returns:
        Dictionary containing regression statistics
    """
    # Handle NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        logger.warning("Insufficient valid data points for regression calculation.")
        return {
            'slope': np.nan,
            'intercept': np.nan,
            'r_value': np.nan,
            'p_value': np.nan,
            'std_err': np.nan,
            'r_squared': np.nan
        }
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r_value': float(r_value),
        'p_value': float(p_value),
        'std_err': float(std_err),
        'r_squared': float(r_value ** 2)
    }

def plot_entropy_vs_property(
    df: pd.DataFrame,
    entropy_col: str,
    property_col: str,
    output_path: str,
    title: str = "Entropy vs Property",
    xlabel: str = "Entropy",
    ylabel: str = "Property Value"
) -> None:
    """
    Generate a scatter plot with regression line and R² annotation.
    
    Ensures:
    - Output is saved as PNG with ≥300 DPI resolution (SC-004)
    - Proper axis labels are present
    - Regression line is overlaid
    - R² value is annotated on the plot
    
    Args:
        df: DataFrame containing the data
        entropy_col: Column name for entropy values
        property_col: Column name for property values (logS or logP)
        output_path: Full path to save the PNG file
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
    """
    # Extract data
    x = df[entropy_col].values
    y = df[property_col].values
    
    # Compute regression metrics
    metrics = compute_regression_metrics(x, y)
    
    # Create figure
    plt.figure(figsize=(10, 8))
    
    # Scatter plot
    plt.scatter(x, y, alpha=0.6, edgecolors='w', linewidth=0.5, s=50)
    
    # Regression line
    if not np.isnan(metrics['slope']):
        x_line = np.linspace(np.nanmin(x), np.nanmax(x), 100)
        y_line = metrics['slope'] * x_line + metrics['intercept']
        plt.plot(x_line, y_line, 'r-', linewidth=2, label='Linear Fit')
        
        # Annotation
        r_squared = metrics['r_squared']
        p_value = metrics['p_value']
        annotation = f"R² = {r_squared:.4f}\np = {p_value:.4g}"
        plt.text(
            0.05, 0.95, annotation,
            transform=plt.gca().transAxes,
            fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
        
        plt.legend(loc='best')
    
    # Labels and title (SC-004: Proper axis labels)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save with high resolution (SC-004: ≥300 dpi)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, format='png')
    plt.close()
    
    logger.info(f"Plot saved to {output_path} (300 dpi)")

def plot_all_correlations(
    df: pd.DataFrame,
    output_dir: str,
    entropy_cols: list = None,
    property_cols: list = None
) -> Dict[str, str]:
    """
    Generate all correlation plots between entropy columns and property columns.
    
    Args:
        df: DataFrame with entropy and property columns
        output_dir: Directory to save plot files
        entropy_cols: List of entropy column names (default: ['atom_entropy', 'bond_entropy'])
        property_cols: List of property column names (default: ['logS', 'logP'])
        
    Returns:
        Dictionary mapping plot type to file path
    """
    if entropy_cols is None:
        entropy_cols = ['atom_entropy', 'bond_entropy']
    if property_cols is None:
        property_cols = ['logS', 'logP']
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    generated_files = {}
    
    for ent_col in entropy_cols:
        if ent_col not in df.columns:
            logger.warning(f"Entropy column '{ent_col}' not found in DataFrame. Skipping.")
            continue
            
        for prop_col in property_cols:
            if prop_col not in df.columns:
                logger.warning(f"Property column '{prop_col}' not found in DataFrame. Skipping.")
                continue
                
            # Construct output filename
            prop_name = prop_col.replace('_', ' ').upper()
            ent_name = ent_col.replace('_', ' ').upper()
            filename = f"{ent_name}_vs_{prop_name}.png".replace(' ', '_').lower()
            output_path = os.path.join(output_dir, filename)
            
            # Create title and labels
            title = f"{ent_name} vs {prop_name}"
            xlabel = ent_name
            ylabel = prop_name
            
            # Generate plot
            plot_entropy_vs_property(
                df=df,
                entropy_col=ent_col,
                property_col=prop_col,
                output_path=output_path,
                title=title,
                xlabel=xlabel,
                ylabel=ylabel
            )
            
            generated_files[filename] = output_path
    
    return generated_files

def main():
    """
    CLI entry point for generating plots.
    Expects command line arguments or can be called programmatically.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate entropy vs property correlation plots")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory for plots")
    parser.add_argument("--entropy-cols", type=str, nargs='+', default=None, help="Entropy columns to plot")
    parser.add_argument("--property-cols", type=str, nargs='+', default=None, help="Property columns to plot")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    # Generate plots
    logger.info("Generating plots...")
    results = plot_all_correlations(
        df=df,
        output_dir=args.output_dir,
        entropy_cols=args.entropy_cols,
        property_cols=args.property_cols
    )
    
    logger.info(f"Generated {len(results)} plots:")
    for name, path in results.items():
        logger.info(f"  - {name} -> {path}")

if __name__ == "__main__":
    main()