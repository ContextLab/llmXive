"""
Visualization module for the Neural Correlates of Error Monitoring project.

This module provides functions to generate plots for the analysis results,
specifically focusing on the relationship between MFN amplitude and error magnitude.
"""
import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Ensure the plot backend works in headless environments
plt.switch_backend('Agg')

# Set seaborn style for publication-quality figures
sns.set(style="whitegrid")
sns.set_palette("deep")

def load_processed_data_for_viz(data_path: str) -> pd.DataFrame:
    """
    Load the processed data containing MFN features and error magnitudes.
    
    Args:
        data_path: Path to the processed CSV file (e.g., data/processed/mfn_features.csv).
        
    Returns:
        DataFrame containing the necessary columns for plotting.
        
    Raises:
        FileNotFoundError: If the data file does not exist.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")
    
    df = pd.read_csv(path)
    
    # Ensure required columns exist
    required_cols = ['participant_id', 'error_magnitude', 'mean_amplitude', 'electrode']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def generate_scatter_plot_with_regression(
    df: pd.DataFrame,
    electrode: str = 'FCz',
    output_path: Optional[str] = None,
    title: Optional[str] = None
) -> str:
    """
    Generate a scatter plot of MFN amplitude vs. error magnitude with a regression line.
    
    This function creates a visualization for a specific electrode, showing the
    relationship between the mean amplitude of the MFN (Medial Frontal Negativity)
    and the calculated error magnitude.
    
    Args:
        df: DataFrame containing 'error_magnitude', 'mean_amplitude', and 'electrode'.
        electrode: The electrode to filter the data for (default: 'FCz').
        output_path: Path to save the figure. If None, saves to results/figures/.
        title: Custom title for the plot. If None, a default title is generated.
        
    Returns:
        The absolute path to the saved figure file.
        
    Raises:
        ValueError: If no data is found for the specified electrode.
    """
    # Filter data for the specified electrode
    electrode_data = df[df['electrode'] == electrode]
    
    if electrode_data.empty:
        raise ValueError(f"No data found for electrode: {electrode}")
    
    # Prepare the plot
    plt.figure(figsize=(10, 8))
    
    # Create the scatter plot with regression line using seaborn
    # We use regplot to automatically calculate and plot the linear regression
    sns.regplot(
        data=electrode_data,
        x='error_magnitude',
        y='mean_amplitude',
        scatter_kws={'alpha': 0.6, 's': 60, 'edgecolor': 'w'},
        line_kws={'color': 'red', 'linewidth': 2},
        ci=95
    )
    
    # Customize the plot
    if title is None:
        title = f"MFN Mean Amplitude vs. Error Magnitude ({electrode})"
    
    plt.title(title, fontsize=16, pad=15)
    plt.xlabel('Error Magnitude (degrees)', fontsize=12)
    plt.ylabel('MFN Mean Amplitude (µV)', fontsize=12)
    
    # Add a grid for better readability
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    
    # Ensure output directory exists
    if output_path is None:
        output_dir = Path('results/figures')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"mfn_vs_error_{electrode}.png"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to: {output_path}")
    return str(output_path)

def generate_multi_electrode_comparison(
    df: pd.DataFrame,
    electrodes: Optional[list] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate a grid of scatter plots for multiple electrodes.
    
    Args:
        df: DataFrame containing 'error_magnitude', 'mean_amplitude', and 'electrode'.
        electrodes: List of electrodes to include. If None, uses all unique electrodes.
        output_path: Path to save the figure.
        
    Returns:
        The absolute path to the saved figure file.
    """
    if electrodes is None:
        electrodes = df['electrode'].unique().tolist()
    
    if not electrodes:
        raise ValueError("No electrodes specified or found in data.")
    
    # Create subplots
    n_electrodes = len(electrodes)
    cols = 3
    rows = (n_electrodes + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
    if n_electrodes == 1:
        axes = np.array([axes])
    axes = axes.flatten()
    
    for i, electrode in enumerate(electrodes):
        if i >= len(axes):
            break
        
        ax = axes[i]
        electrode_data = df[df['electrode'] == electrode]
        
        if electrode_data.empty:
            ax.text(0.5, 0.5, f"No data\nfor {electrode}", 
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{electrode} (No Data)")
            continue
        
        sns.regplot(
            data=electrode_data,
            x='error_magnitude',
            y='mean_amplitude',
            ax=ax,
            scatter_kws={'alpha': 0.5, 's': 40},
            line_kws={'color': 'red'}
        )
        
        ax.set_title(f"{electrode}")
        ax.set_xlabel('Error Magnitude (deg)')
        ax.set_ylabel('MFN Mean Amp (µV)')
    
    # Remove empty subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    
    plt.suptitle("MFN Amplitude vs. Error Magnitude by Electrode", fontsize=16, y=1.02)
    plt.tight_layout()
    
    if output_path is None:
        output_dir = Path('results/figures')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "mfn_vs_error_multi_electrode.png"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Multi-electrode comparison plot saved to: {output_path}")
    return str(output_path)

def main():
    """
    Main entry point for the visualization script.
    
    This function loads the processed data, generates the primary scatter plot
    for FCz (as per the primary analysis plan), and saves it to the results directory.
    """
    logger.info("Starting visualization script...")
    
    # Define paths based on project structure
    # Assuming processed data is in data/processed/ as per T014
    processed_data_path = 'data/processed/mfn_features.csv'
    
    try:
        # Load data
        df = load_processed_data_for_viz(processed_data_path)
        
        # Generate primary plot for FCz
        # The primary metric is defined at FCz in the plan
        primary_electrode = 'FCz'
        output_file = generate_scatter_plot_with_regression(
            df=df,
            electrode=primary_electrode,
            output_path='results/figures/mfn_vs_error_FCz.png'
        )
        
        # Generate multi-electrode comparison if other electrodes exist
        unique_electrodes = df['electrode'].unique()
        if len(unique_electrodes) > 1:
            generate_multi_electrode_comparison(
                df=df,
                electrodes=list(unique_electrodes),
                output_path='results/figures/mfn_vs_error_comparison.png'
            )
        
        logger.info(f"Visualization complete. Output: {output_file}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}")
        raise

if __name__ == "__main__":
    # Initialize logging for the script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()