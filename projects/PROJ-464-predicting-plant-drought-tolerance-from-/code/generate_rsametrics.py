"""
T015: Generate data/derived/rsametrics.csv from processed image data.

This script aggregates the per-image RSA metrics extracted in T013
into a single CSV file, performing validation to ensure no null values
and that all numerical traits are positive.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from preprocess_images import process_directory, RSAMetricsResult
from config import DATA_RAW_PATH, DATA_DERIVED_PATH

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def aggregate_and_validate_metrics(
    input_dir: Path,
    output_path: Path,
    image_extensions: tuple = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')
) -> pd.DataFrame:
    """
    Process all images in input_dir, aggregate metrics, validate, and save to CSV.
    
    Args:
        input_dir: Path to directory containing root images.
        output_path: Path where the output CSV will be saved.
        image_extensions: Tuple of valid image file extensions.
        
    Returns:
        DataFrame containing the validated RSA metrics.
        
    Raises:
        ValueError: If validation fails (nulls or non-positive values found).
    """
    logger.info(f"Starting aggregation of images from: {input_dir}")
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
        
    # Process all images in the directory
    results: List[RSAMetricsResult] = []
    image_files = [f for f in input_dir.iterdir() if f.suffix.lower() in image_extensions]
    
    if not image_files:
        raise ValueError(f"No image files found in {input_dir} with extensions: {image_extensions}")
        
    logger.info(f"Found {len(image_files)} image files to process.")
    
    for img_path in image_files:
        try:
            result = process_single_image(img_path)
            if result is not None:
                results.append(result)
                logger.debug(f"Processed: {img_path.name} -> depth={result.depth:.2f}, "
                             f"branching={result.branching_density:.4f}, "
                             f"area={result.surface_area:.2f}")
        except Exception as e:
            logger.error(f"Failed to process {img_path.name}: {e}", exc_info=True)
            continue
    
    if not results:
        raise ValueError("No valid metrics extracted from any images. Check input data and preprocessing logic.")
    
    # Convert to DataFrame
    df = pd.DataFrame([r.to_dict() for r in results])
    
    # Ensure columns are in expected order and types
    expected_cols = ['species_id', 'depth', 'branching_density', 'surface_area']
    if not all(col in df.columns for col in expected_cols):
        raise ValueError(f"Missing expected columns. Found: {list(df.columns)}, Expected: {expected_cols}")
    
    df = df[expected_cols]
    
    # Convert to numeric, coercing errors to NaN
    for col in ['depth', 'branching_density', 'surface_area']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Validation: Check for null values
    null_counts = df[['depth', 'branching_density', 'surface_area']].isnull().sum()
    if null_counts.any():
        error_msg = f"Null values found in metrics:\n{null_counts[null_counts > 0]}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validation: Check for positive values
    # Depth and surface area must be > 0. Branching density should be >= 0 (can be 0 for unbranched).
    # However, spec says "positive numerical values", so we enforce > 0 for all to be strict.
    # If a biological case allows 0 branching, we might relax this, but "positive" usually means > 0.
    # Let's check strictly > 0 first. If 0 is acceptable for branching, we'd adjust.
    # Given "positive numerical values" in prompt, we assume > 0.
    for col in ['depth', 'branching_density', 'surface_area']:
        if (df[col] <= 0).any():
            count_zero = (df[col] <= 0).sum()
            error_msg = f"Non-positive values found in '{col}': {count_zero} rows."
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    logger.info(f"Validation passed. All {len(df)} rows have non-null, positive values.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved validated RSA metrics to: {output_path}")
    
    return df

def main():
    """Main entry point for T015."""
    # Define paths based on config
    # T012 downloads to DATA_RAW_PATH / "nppn_images"
    raw_images_dir = DATA_RAW_PATH / "nppn_images"
    output_csv_path = DATA_DERIVED_PATH / "rsametrics.csv"
    
    try:
        df = aggregate_and_validate_metrics(raw_images_dir, output_csv_path)
        logger.info("T015 completed successfully.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"T015 failed: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error in T015: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())