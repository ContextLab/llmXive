import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from utils.logging import get_logger, setup_logging_for_script
from utils.config import get_project_root, get_figures_path, get_data_path

# Configure logging for this module
logger = get_logger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """Load the processed analysis data from disk."""
    data_path = get_data_path()
    file_path = data_path / "processed" / "analysis_data.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Analysis data not found at {file_path}. Run analysis.py first.")
    return pd.read_csv(file_path)

def plot_flexibility_vs_permeability(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title_suffix: str = "Associational Relationship",
    output_filename: str = "flexibility_permeability_plot.png"
) -> Path:
    """
    Generate a scatter plot with regression line and 95% confidence interval.
    
    Args:
        data: DataFrame containing the data to plot.
        x_col: Column name for the x-axis (flexibility descriptor).
        y_col: Column name for the y-axis (logPapp).
        title_suffix: Suffix for the plot title to explicitly state "Associational Relationship".
        output_filename: Name of the output PNG file.
    
    Returns:
        Path to the generated plot file.
    """
    # Ensure the output directory exists
    figures_dir = get_figures_path()
    figures_dir.mkdir(parents=True, exist_ok=True)
    output_path = figures_dir / output_filename

    # Setup the plot
    plt.figure(figsize=(10, 8))
    
    # Use seaborn regplot for scatter + regression + CI
    # Note: We use 'associational' in the title to strictly comply with FR-009
    # and avoid causal implications.
    sns.regplot(
        data=data, 
        x=x_col, 
        y=y_col, 
        scatter_kws={'alpha': 0.6, 's': 40, 'edgecolor': 'w'},
        line_kws={'color': 'red', 'linewidth': 2},
        ci=95
    )
    
    # Construct the title to explicitly state "Associational Relationship"
    # as required by FR-009.
    main_title = f"{x_col} vs logPapp: {title_suffix}"
    plt.title(main_title, fontsize=16, fontweight='bold')
    plt.xlabel(x_col.replace('_', ' ').title(), fontsize=12)
    plt.ylabel('Log Papp (cm/s)', fontsize=12)
    
    # Add grid for readability
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")
    return output_path

def generate_all_flexibility_plots(
    data: Optional[pd.DataFrame] = None,
    descriptors: Optional[list] = None
) -> Dict[str, Path]:
    """
    Generate plots for all flexibility descriptors against permeability.
    
    Args:
        data: Optional DataFrame. If None, loads from disk.
        descriptors: List of descriptor column names to plot. Defaults to 
                     ['bond_variance', 'angle_variance', 'dihedral_variance'].
    
    Returns:
        Dictionary mapping descriptor name to the Path of the generated plot.
    """
    if data is None:
        data = load_analysis_data()
    
    if descriptors is None:
        descriptors = ['bond_variance', 'angle_variance', 'dihedral_variance']
    
    output_paths = {}
    y_col = 'logPapp'
    
    for desc in descriptors:
        if desc not in data.columns:
            logger.warning(f"Descriptor {desc} not found in data. Skipping.")
            continue
        
        # Generate the plot with the specific "Associational Relationship" title
        # The title_suffix parameter ensures FR-009 compliance.
        out_path = plot_flexibility_vs_permeability(
            data=data,
            x_col=desc,
            y_col=y_col,
            title_suffix="Associational Relationship",
            output_filename=f"{desc}_vs_logPapp_associational.png"
        )
        output_paths[desc] = out_path
    
    return output_paths

def main():
    """Entry point for the visualization module."""
    setup_logging_for_script(__name__)
    logger.info("Starting visualization module.")
    
    try:
        # Load data
        data = load_analysis_data()
        logger.info(f"Loaded {len(data)} records for visualization.")
        
        # Generate plots
        outputs = generate_all_flexibility_plots(data)
        
        logger.info(f"Generated {len(outputs)} plots.")
        for desc, path in outputs.items():
            logger.info(f"  - {desc}: {path}")
            
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred during visualization.")
        sys.exit(1)

if __name__ == "__main__":
    main()
