"""
Visualization module for User Story 2 (EDA).
Generates variogram plots and correlation heatmaps.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns

# Import from local project structure
from utils.logging import get_logger
from eda import calculate_variogram, calculate_correlation_matrix, load_raster_as_dataframe
from config import DATA_RESULTS_PATH, FIGURES_PATH

logger = get_logger(__name__)


def plot_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    output_path: Optional[Path] = None,
    title: str = "Correlation Heatmap"
) -> Path:
    """
    Generate and save a correlation heatmap.

    Args:
        corr_matrix: DataFrame containing correlation coefficients.
        output_path: Path to save the figure. Defaults to DATA_RESULTS_PATH/figures/correlation_heatmap.png.
        title: Plot title.

    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        output_path = FIGURES_PATH / "correlation_heatmap.png"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 10))
    # Create a mask for the upper triangle
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(230, 20, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(
        corr_matrix, 
        mask=mask, 
        cmap=cmap, 
        vmax=1.0, 
        vmin=-1.0, 
        center=0,
        square=True, 
        linewidths=.5, 
        cbar_kws={"shrink": .5},
        annot=True,
        fmt=".2f"
    )

    plt.title(title, fontsize=16)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.info(f"Correlation heatmap saved to {output_path}")
    return output_path


def plot_variogram(
    variogram_data: Dict[str, Any],
    output_path: Optional[Path] = None,
    title: str = "Experimental Variogram"
) -> Path:
    """
    Generate and save a variogram plot.

    Args:
        variogram_data: Dictionary containing 'distances' and 'semivariances' keys.
        output_path: Path to save the figure. Defaults to DATA_RESULTS_PATH/figures/variogram.png.
        title: Plot title.

    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        output_path = FIGURES_PATH / "variogram.png"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    distances = variogram_data.get('distances', [])
    semivariances = variogram_data.get('semivariances', [])

    if not distances or not semivariances:
        logger.warning("No valid variogram data to plot.")
        # Create a placeholder figure indicating no data
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No Variogram Data Available", ha='center', va='center')
        plt.title(title)
        plt.savefig(output_path, dpi=300)
        plt.close()
        return output_path

    plt.figure(figsize=(10, 6))
    plt.scatter(distances, semivariances, alpha=0.6, s=50, color='darkblue', edgecolors='black')
    
    # Optionally fit a model line if available in data (not strictly required by task, but good practice)
    # For now, just plotting the experimental points as per task description "Visualize variogram"
    
    plt.xlabel("Distance (meters)", fontsize=12)
    plt.ylabel("Semivariance", fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.info(f"Variogram plot saved to {output_path}")
    return output_path


def generate_eda_visualizations(
    raster_paths: Dict[str, str],
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """
    Orchestrates the generation of all EDA visualizations:
    1. Correlation Heatmap (requires loading data into memory)
    2. Variogram Plot (requires computing variogram)

    Args:
        raster_paths: Dict mapping variable names to file paths.
        output_dir: Directory to save outputs.

    Returns:
        Dict mapping artifact names to their saved paths.
    """
    if output_dir is None:
        output_dir = FIGURES_PATH
    
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    # 1. Generate Correlation Heatmap
    try:
        logger.info("Loading data for correlation analysis...")
        # Load all rasters into a single DataFrame
        # Assuming load_raster_as_dataframe returns a DataFrame with columns for each variable
        df = load_raster_as_dataframe(raster_paths)
        
        if df is None or df.empty:
            logger.warning("No data loaded for correlation analysis. Skipping heatmap.")
        else:
            logger.info("Calculating correlation matrix...")
            corr_matrix = calculate_correlation_matrix(df)
            
            logger.info("Plotting correlation heatmap...")
            heatmap_path = plot_correlation_heatmap(
                corr_matrix, 
                output_path=output_dir / "correlation_heatmap.png",
                title="Correlation Matrix: OSM Features vs Temperature"
            )
            results['correlation_heatmap'] = heatmap_path
    except Exception as e:
        logger.error(f"Failed to generate correlation heatmap: {e}", exc_info=True)

    # 2. Generate Variogram Plot
    try:
        logger.info("Calculating variogram for temperature...")
        # We assume the temperature column is named 'temperature' or similar.
        # The calculate_variogram function in eda.py should handle the input.
        # If it expects a specific column, we might need to extract it.
        # Based on typical usage, we pass the full df or specific column.
        # Let's assume the eda function handles the extraction or we pass the series.
        
        # If calculate_variogram expects a Series:
        temp_col = None
        for col in df.columns:
            if 'temp' in col.lower():
                temp_col = col
                break
        
        if temp_col:
            variogram_result = calculate_variogram(df[temp_col])
            
            if variogram_result:
                logger.info("Plotting variogram...")
                variogram_path = plot_variogram(
                    variogram_result,
                    output_path=output_dir / "variogram.png",
                    title="Experimental Variogram of Temperature"
                )
                results['variogram'] = variogram_path
            else:
                logger.warning("Variogram calculation returned no data.")
        else:
            logger.warning("Temperature column not found in dataframe for variogram.")
    except Exception as e:
        logger.error(f"Failed to generate variogram plot: {e}", exc_info=True)

    return results


def main():
    """
    Main entry point to run visualizations.
    Expects aligned rasters to exist in data/processed/ as per previous tasks.
    """
    logger.info("Starting EDA Visualization generation (Task T022)...")

    # Define input paths based on standard project structure
    # These paths should match what T015 produced
    processed_dir = Path("data/processed")
    
    # Heuristic to find the stack or specific files
    # Assuming files are named like: temperature.tif, buildings.tif, etc.
    # Or a single stack file. For this script, we assume individual GeoTIFFs
    # or a known set of variables.
    
    # Let's construct a map of expected variables to files
    # In a real scenario, this might be read from metadata.json
    expected_vars = {
        "temperature": "temperature.tif",
        "building_density": "building_density.tif",
        "tree_coverage": "tree_coverage.tif",
        "road_density": "road_density.tif"
    }

    raster_paths = {}
    for var_name, filename in expected_vars.items():
        full_path = processed_dir / filename
        if full_path.exists():
            raster_paths[var_name] = str(full_path)
        else:
            logger.warning(f"Expected raster file not found: {full_path}")

    if not raster_paths:
        logger.error("No input raster files found in data/processed/. "
                     "Please ensure T015 (Aligned GeoTIFF stack output) has been completed.")
        return

    output_dir = FIGURES_PATH
    output_dir.mkdir(parents=True, exist_ok=True)

    results = generate_eda_visualizations(raster_paths, output_dir)

    if results:
        logger.info(f"Successfully generated {len(results)} visualization(s):")
        for name, path in results.items():
            logger.info(f"  - {name}: {path}")
    else:
        logger.warning("No visualizations were generated.")

    logger.info("Task T022 completed.")


if __name__ == "__main__":
    main()
