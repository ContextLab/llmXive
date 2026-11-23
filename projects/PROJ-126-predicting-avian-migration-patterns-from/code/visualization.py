"""
Visualization Module for Avian Migration Pipeline.
Handles regional map generation and other visual outputs.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import matplotlib.pyplot as plt

from config import DATA_OUTPUTS, get_logger

logger = get_logger(__name__)

def generate_regional_map(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Generates a regional map of predicted arrival dates.
    
    Args:
        df: DataFrame with grid_id, lat, lon, arrival_date.
        output_path: Path to save the map image.
    """
    if output_path is None:
        output_path = DATA_OUTPUTS / "lake_powell_arrival_map.png"
    
    if df.empty:
        logger.warning("No data provided for regional map.")
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot for arrival dates
    scatter = ax.scatter(
        df["lon"], 
        df["lat"], 
        c=pd.to_datetime(df["arrival_date"]).map(pd.Timestamp.toordinal),
        cmap="viridis",
        alpha=0.7,
        edgecolors="w",
        s=50
    )
    
    plt.colorbar(scatter, label="Arrival Date (Ordinal)")
    ax.set_title("Lake Powell Region: Predicted First Arrival Dates")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Regional map saved to {output_path}")

def main():
    """Main entry point for visualization."""
    logger.info("Starting visualization pipeline...")
    # Load data (placeholder)
    input_path = DATA_OUTPUTS.parent / "processed" / "modeling_features.csv"
    if input_path.exists():
        df = pd.read_csv(input_path)
        generate_regional_map(df)
    else:
        logger.warning("No modeling data found for visualization.")
    logger.info("Visualization pipeline completed.")

if __name__ == "__main__":
    main()
