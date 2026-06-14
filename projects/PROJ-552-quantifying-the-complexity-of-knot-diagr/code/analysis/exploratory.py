import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from reproducibility.logs import log_operation, get_logger

# Set random seed for reproducibility per Constitution Principle I
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


def load_cleaned_knots(data_path: Optional[Path] = None) -> pd.DataFrame:
    """Load cleaned knot data from CSV file.
    
    Args:
        data_path: Path to cleaned knot data CSV. Defaults to data/processed/knots_cleaned.csv.
        
    Returns:
        DataFrame containing cleaned knot records.
        
    Raises:
        FileNotFoundError: If the data file does not exist.
    """
    if data_path is None:
        data_path = Path('data/processed/knots_cleaned.csv')
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    return df


def create_stratified_scatter_plot(
    df: pd.DataFrame,
    x_col: str = 'crossing_number',
    y_col: str = 'braid_index',
    hue_col: str = 'is_alternating',
    figsize: Tuple[int, int] = (12, 9),
    dpi: int = 100
) -> plt.Figure:
    """Create a scatter plot of crossing number vs braid index, stratified by alternating/non-alternating classification.
    
    Args:
        df: DataFrame containing knot data.
        x_col: Column name for x-axis values. Defaults to 'crossing_number'.
        y_col: Column name for y-axis values. Defaults to 'braid_index'.
        hue_col: Column name for stratification. Defaults to 'is_alternating'.
        figsize: Figure size in inches (width, height). Defaults to (12, 9).
        dpi: Dots per inch for the figure. Defaults to 100.
        
    Returns:
        matplotlib Figure object containing the scatter plot.
        
    Note:
        With figsize=(12, 9) and dpi=100, the output resolution is 1200x900 pixels.
    """
    # Ensure is_alternating is boolean or categorical for proper legend
    df_plot = df.copy()
    if hue_col in df_plot.columns:
        df_plot[hue_col] = df_plot[hue_col].astype(bool)
    
    # Create figure with specified dimensions
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Create scatter plot stratified by alternating classification
    sns.scatterplot(
        data=df_plot,
        x=x_col,
        y=y_col,
        hue=hue_col,
        ax=ax,
        alpha=0.7,
        s=50,
        edgecolors='black',
        linewidth=0.5
    )
    
    # Set labels and title
    ax.set_xlabel(x_col.replace('_', ' ').title(), fontsize=12)
    ax.set_ylabel(y_col.replace('_', ' ').title(), fontsize=12)
    ax.set_title('Crossing Number vs Braid Index (Stratified by Alternating Classification)',
                fontsize=14, fontweight='bold')
    
    # Add grid for readability
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Set legend
    ax.legend(title='Classification', title_fontsize=10, fontsize=9)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig


def generate_exploratory_plots(
    data_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    plot_name: str = 'crossing_vs_braid',
    resolution: Tuple[int, int] = (1200, 900)
) -> Path:
    """Generate and save exploratory plots for knot complexity analysis.
    
    This function creates scatter plots of crossing number vs braid index,
    stratified by alternating/non-alternating classification, and saves them
    to the specified output directory.
    
    Args:
        data_path: Path to cleaned knot data CSV. Defaults to data/processed/knots_cleaned.csv.
        output_dir: Directory to save plots. Defaults to data/plots.
        plot_name: Base name for the output plot file. Defaults to 'crossing_vs_braid'.
        resolution: Target resolution in pixels (width, height). Defaults to (1200, 900).
        
    Returns:
        Path to the saved plot file.
        
    Note:
        Per T024 requirements, the plot is saved with resolution 1200x900 pixels.
        This is achieved with figsize=(12, 9) inches and dpi=100.
    """
    logger = get_logger()
    
    # Set default output directory
    if output_dir is None:
        output_dir = Path('data/plots')
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load cleaned knot data
    df = load_cleaned_knots(data_path)
    logger.info(f"Loaded {len(df)} knot records for exploratory analysis")
    
    # Calculate figure size from target resolution
    # resolution = (figsize * dpi), so figsize = resolution / dpi
    dpi = 100
    figsize = (resolution[0] / dpi, resolution[1] / dpi)
    
    # Create stratified scatter plot
    fig = create_stratified_scatter_plot(
        df,
        x_col='crossing_number',
        y_col='braid_index',
        hue_col='is_alternating',
        figsize=figsize,
        dpi=dpi
    )
    
    # Save plot to file
    output_path = output_dir / f'{plot_name}.png'
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved exploratory plot to {output_path} with resolution {resolution[0]}x{resolution[1]} pixels")
    
    return output_path


def main():
    """Main entry point for exploratory plot generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate exploratory plots for knot complexity analysis')
    parser.add_argument('--data-path', type=str, default='data/processed/knots_cleaned.csv',
                      help='Path to cleaned knot data CSV')
    parser.add_argument('--output-dir', type=str, default='data/plots',
                      help='Directory to save plots')
    parser.add_argument('--plot-name', type=str, default='crossing_vs_braid',
                      help='Base name for the output plot file')
    parser.add_argument('--width', type=int, default=1200,
                      help='Target width in pixels')
    parser.add_argument('--height', type=int, default=900,
                      help='Target height in pixels')
    
    args = parser.parse_args()
    
    output_path = generate_exploratory_plots(
        data_path=Path(args.data_path),
        output_dir=Path(args.output_dir),
        plot_name=args.plot_name,
        resolution=(args.width, args.height)
    )
    
    print(f"Exploratory plot saved to: {output_path}")


if __name__ == '__main__':
    main()