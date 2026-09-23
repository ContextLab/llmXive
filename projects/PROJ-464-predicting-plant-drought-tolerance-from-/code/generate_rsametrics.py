"""
Task T015: Generate data/derived/rsametrics.csv from preprocessed image data.

This module aggregates RSA metrics extracted by preprocess_images.py into a
single CSV file, applying strict validation to ensure no null values and
positive numerical values for all traits.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

# Import from sibling modules using the verified API surface
from config import ensure_directories, get_config_summary
from preprocess_images import process_directory, RSAMetricsResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def aggregate_and_validate_metrics(
    input_dir: Path,
    output_path: Path
) -> pd.DataFrame:
    """
    Process all images in input_dir, aggregate metrics, validate, and save to CSV.

    Args:
        input_dir: Path to directory containing root images.
        output_path: Path where the output CSV will be written.

    Returns:
        DataFrame containing the validated RSA metrics.

    Raises:
        ValueError: If validation fails (nulls, non-positive values, or no data).
        FileNotFoundError: If input directory is empty or contains no valid images.
    """
    logger.info(f"Starting aggregation for images in: {input_dir}")
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    # Process all images in the directory
    results: List[RSAMetricsResult] = process_directory(input_dir)
    
    if not results:
        raise FileNotFoundError(
            f"No valid images found or processed in {input_dir}. "
            "Pipeline cannot proceed without real data."
        )
    
    logger.info(f"Processed {len(results)} images successfully.")
    
    # Convert results to DataFrame
    records = [r.model_dump() for r in results]
    df = pd.DataFrame(records)
    
    # Ensure required columns exist
    required_cols = ['species_id', 'depth', 'branching_density', 'surface_area']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in output: {missing_cols}")
    
    # Validation: Check for null values
    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        error_msg = (
            f"Validation failed: Found null values in columns: "
            f"{null_counts[null_counts > 0].to_dict()}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validation: Check for positive numerical values
    numeric_cols = ['depth', 'branching_density', 'surface_area']
    for col in numeric_cols:
        if (df[col] <= 0).any():
            error_msg = (
                f"Validation failed: Found non-positive values in column '{col}'. "
                f"Count of non-positive: {(df[col] <= 0).sum()}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    # Ensure species_id is not empty
    if df['species_id'].str.strip().eq('').any():
        error_msg = "Validation failed: Found empty or whitespace-only species_id values."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Validation passed: No nulls, all values positive.")
    
    # Sort for consistency
    df = df.sort_values(by=['species_id', 'depth']).reset_index(drop=True)
    
    # Write to CSV
    ensure_directories([output_path.parent])
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")
    
    return df

def main():
    """Entry point for the script."""
    config = get_config_summary()
    input_dir = Path(config['paths']['raw_images'])
    output_path = Path(config['paths']['derived_rsametrics'])
    
    logger.info(f"Configuration loaded. Input: {input_dir}, Output: {output_path}")
    
    try:
        df = aggregate_and_validate_metrics(input_dir, output_path)
        logger.info("T015 completed successfully.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"T015 FAILED: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during T015 execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())