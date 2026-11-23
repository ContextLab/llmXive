"""
Derive the geographic bounding box from the Moral Machine dataset.

This script loads the Moral Machine dataset (or a sample thereof), calculates
the exact geographic bounding box (min/max lat/lon) required for the ERA5 fetch,
and outputs the bounding box to data/external/bounding_box.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

# Add project root to path to allow relative imports if needed, though this script is standalone
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

def ensure_directories():
    """Ensure the output directory exists."""
    output_dir = project_root / "data" / "external"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_moral_machine_data(sample_size: int = None) -> pd.DataFrame:
    """
    Load the Moral Machine dataset.
    
    Args:
        sample_size: If provided, load only the first N rows.
        
    Returns:
        DataFrame containing the dataset.
    """
    # Determine path based on environment override or default
    # The dataset is expected to be at data/raw/moral_machine.csv.gz after T001a validation
    data_path = get_path_env_override(
        "MORAL_MACHINE_DATA_PATH",
        project_root / "data" / "raw" / "moral_machine.csv.gz"
    )
    
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
        
    if not data_path.exists():
        # Fallback to common uncompressed name if compressed doesn't exist
        alt_path = data_path.with_suffix('.csv')
        if alt_path.exists():
            data_path = alt_path
        else:
            raise FileNotFoundError(
                f"Moral Machine dataset not found at {data_path} or {alt_path}. "
                "Please ensure T001a has validated and downloaded the data."
            )

    logger = get_data_quality_logger()
    logger.info(f"Loading Moral Machine dataset from: {data_path}")
    
    try:
        if str(data_path).endswith('.gz'):
            df = pd.read_csv(data_path, compression='gzip')
        else:
            df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    if sample_size:
        logger.info(f"Sampling first {sample_size} rows for bounding box calculation.")
        df = df.head(sample_size)

    # Validate required columns exist
    required_cols = ['latitude', 'longitude']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in Moral Machine data: {missing}")

    return df

def calculate_bounding_box(df: pd.DataFrame) -> dict:
    """
    Calculate the bounding box from latitude and longitude columns.
    
    Args:
        df: DataFrame with 'latitude' and 'longitude' columns.
        
    Returns:
        Dictionary with min_lat, max_lat, min_lon, max_lon.
    """
    # Drop rows with missing coordinates
    valid_df = df.dropna(subset=['latitude', 'longitude'])
    
    if valid_df.empty:
        raise ValueError("No valid latitude/longitude coordinates found in the dataset.")
    
    min_lat = valid_df['latitude'].min()
    max_lat = valid_df['latitude'].max()
    min_lon = valid_df['longitude'].min()
    max_lon = valid_df['longitude'].max()
    
    return {
        "min_lat": float(min_lat),
        "max_lat": float(max_lat),
        "min_lon": float(min_lon),
        "max_lon": float(max_lon)
    }

def save_bounding_box(bbox: dict, output_path: Path):
    """Save the bounding box to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(bbox, f, indent=2)
    logger = get_data_quality_logger()
    logger.info(f"Bounding box saved to: {output_path}")

def main():
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting bounding box derivation (T002).")
    
    try:
        # Ensure output directory
        output_dir = ensure_directories()
        output_file = output_dir / "bounding_box.json"
        
        # Load data (using a sample size if the full dataset is too large for this step,
        # but the task implies loading the dataset or a sample. We'll load the full if possible,
        # or rely on the user to provide a sample if memory is constrained. 
        # Given T001a validated the source, we assume it's accessible.
        # We'll load the full dataset unless an env var specifies a sample size.
        sample_size = os.getenv("BBOX_SAMPLE_SIZE")
        if sample_size:
            df = load_moral_machine_data(sample_size=int(sample_size))
        else:
            df = load_moral_machine_data()
        
        # Calculate bounding box
        bbox = calculate_bounding_box(df)
        
        # Save to file
        save_bounding_box(bbox, output_file)
        
        logger.info(f"Bounding box derived: {bbox}")
        logger.info("T002 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T002 failed: {e}")
        raise

if __name__ == "__main__":
    main()
