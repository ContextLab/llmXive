"""
Define ERA5 Bounding Box (Dynamic) based on Moral Machine dataset.

This script reads the Moral Machine dataset, calculates the min/max latitude
and longitude, expands the bounds by 2 degrees, and saves the result to
data/external/bounding_box.json.
"""

import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

# Ensure project root is in path for imports if running as script
# but primarily we rely on the environment setup
from config import get_path_env_override

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path("data/external")
    log_dir = Path("results/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    return output_dir, log_dir

def load_moral_machine_data(input_path):
    """
    Load the Moral Machine dataset from the specified path.

    Args:
        input_path (str or Path): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded dataframe.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Moral Machine dataset not found at {input_path}. "
                                "Please run T000 (download_moral_machine.py) first.")
    
    # Read compressed CSV
    df = pd.read_csv(input_path, compression='gzip')
    return df

def calculate_bounding_box(df, expand_degrees=2.0):
    """
    Calculate the bounding box from latitude and longitude columns.

    Args:
        df (pd.DataFrame): Dataset with 'latitude' and 'longitude' columns.
        expand_degrees (float): Degrees to expand the bounds.

    Returns:
        dict: Dictionary containing min_lat, max_lat, min_lon, max_lon.
    """
    # Filter out rows with missing coordinates
    valid_df = df.dropna(subset=['latitude', 'longitude'])
    
    if valid_df.empty:
        raise ValueError("No valid latitude/longitude data found in the dataset.")

    min_lat = valid_df['latitude'].min()
    max_lat = valid_df['latitude'].max()
    min_lon = valid_df['longitude'].min()
    max_lon = valid_df['longitude'].max()

    # Expand bounds
    min_lat_expanded = min_lat - expand_degrees
    max_lat_expanded = max_lat + expand_degrees
    min_lon_expanded = min_lon - expand_degrees
    max_lon_expanded = max_lon + expand_degrees

    return {
        "min_lat": float(min_lat_expanded),
        "max_lat": float(max_lat_expanded),
        "min_lon": float(min_lon_expanded),
        "max_lon": float(max_lon_expanded),
        "expand_degrees": expand_degrees,
        "source_records": len(valid_df)
    }

def save_bounding_box(bbox_data, output_path):
    """
    Save the bounding box data to a JSON file.

    Args:
        bbox_data (dict): Bounding box data.
        output_path (str or Path): Output file path.
    """
    with open(output_path, 'w') as f:
        json.dump(bbox_data, f, indent=2)
    logging.info(f"Bounding box saved to {output_path}")

def main():
    """Main execution function."""
    # Setup logging
    log_dir = Path("results/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "bbox_status.json"
    
    # Configure basic logging to console and file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "bbox_creation.log")
        ]
    )

    # Paths
    input_path = Path("data/raw/moral_machine.csv.gz")
    output_path = Path("data/external/bounding_box.json")
    
    output_dir, _ = ensure_directories()

    try:
        logging.info(f"Loading Moral Machine data from {input_path}...")
        df = load_moral_machine_data(input_path)
        
        logging.info(f"Calculating bounding box with expansion of 2 degrees...")
        bbox_data = calculate_bounding_box(df, expand_degrees=2.0)
        
        logging.info(f"Calculated bounds: {bbox_data}")
        
        save_bounding_box(bbox_data, output_path)
        
        # Log success to status file
        status = {
            "status": "success",
            "file": str(output_path),
            "bounds": bbox_data,
            "timestamp": str(pd.Timestamp.now())
        }
        with open(log_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        logging.info("Task T002a completed successfully.")
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        status = {"status": "failed", "reason": str(e)}
        with open(log_file, 'w') as f:
            json.dump(status, f, indent=2)
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Value error: {e}")
        status = {"status": "failed", "reason": str(e)}
        with open(log_file, 'w') as f:
            json.dump(status, f, indent=2)
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        status = {"status": "failed", "reason": str(e)}
        with open(log_file, 'w') as f:
            json.dump(status, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()
