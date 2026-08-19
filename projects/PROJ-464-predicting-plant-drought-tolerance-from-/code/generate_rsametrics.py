"""
T015: Generate data/derived/rsametrics.csv from preprocessed image data.

This script aggregates the per-image RSA metrics extracted by preprocess_images.py
into a single CSV file. It performs strict validation to ensure:
1. No null values in required columns.
2. All numerical trait values (depth, branching_density, surface_area) are strictly positive.
3. The output file matches the schema: species_id, depth, branching_density, surface_area.

Dependencies:
- code/preprocess_images.py (for data structure definitions)
- code/config.py (for paths)
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

# Import config for path constants
# Assuming config.py has been implemented per T004
try:
    from config import ensure_directories, get_config_summary
except ImportError:
    # Fallback for execution context where config might not be in PYTHONPATH yet
    sys.path.insert(0, str(Path(__file__).parent))
    from config import ensure_directories, get_config_summary

# Import validation logic from preprocess_images if needed, 
# but here we implement the aggregation and final validation.
from preprocess_images import validate_metrics

logger = logging.getLogger(__name__)

def aggregate_and_validate_metrics(input_dir: Path, output_path: Path) -> bool:
    """
    Aggregates individual image processing results (assumed to be JSON or CSV per image)
    or re-runs the directory processing to generate the master CSV.
    
    Since T013 (preprocess_images.py) processes the directory, we assume it either:
    1. Writes a temporary CSV per species/image.
    2. Or we re-invoke the processing logic to collect the final results.
    
    For robustness in this pipeline, we will re-process the directory using the 
    process_directory function from preprocess_images to ensure we have the latest data
    and then aggregate it into the final CSV.
    """
    logger.info(f"Aggregating RSA metrics from: {input_dir}")
    
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist. Did T012 run?")
        return False

    # Import the processing function from preprocess_images
    from preprocess_images import process_directory, RSAMetricsResult

    # Process the directory to get a list of results
    # This function is expected to handle the image loading and feature extraction
    results: List[RSAMetricsResult] = process_directory(input_dir)

    if not results:
        logger.error("No valid RSA metrics found in the input directory.")
        return False

    # Convert to DataFrame
    data = []
    for r in results:
        # Map the result object to the required CSV columns
        # Ensure species_id is the string identifier
        row = {
            "species_id": r.species_id,
            "depth": r.depth,
            "branching_density": r.branching_density,
            "surface_area": r.surface_area
        }
        data.append(row)

    df = pd.DataFrame(data)

    # --- Validation Phase (Strict) ---
    logger.info(f"Validating {len(df)} rows for nulls and positive values...")

    required_cols = ["species_id", "depth", "branching_density", "surface_area"]
    
    # Check for nulls
    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        logger.error(f"Null values found in columns: {null_counts[null_counts > 0].to_dict()}")
        raise ValueError("Validation failed: Null values detected in RSA metrics.")

    # Check for positive values in numerical columns
    numerical_cols = ["depth", "branching_density", "surface_area"]
    for col in numerical_cols:
        if (df[col] <= 0).any():
            negative_count = (df[col] <= 0).sum()
            logger.error(f"Non-positive values found in column '{col}': {negative_count} rows.")
            raise ValueError(f"Validation failed: Non-positive values detected in '{col}'.")

    # Ensure no duplicate species_id + image_id combinations if applicable (aggregation check)
    # For this task, we assume one row per image processed.
    
    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully generated {output_path} with {len(df)} valid rows.")
    return True

def main():
    """Entry point for T015."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Ensure directories exist
    ensure_directories()

    # Define paths based on config
    # Assuming config defines RAW_IMAGE_DIR and DERIVED_DIR
    # We need to import these or construct them. 
    # Based on T012 output: data/raw/nppn_images/
    # Based on T015 output: data/derived/rsametrics.csv
    
    base_path = Path(__file__).parent.parent
    raw_image_dir = base_path / "data" / "raw" / "nppn_images"
    output_path = base_path / "data" / "derived" / "rsametrics.csv"

    if not raw_image_dir.exists():
        logger.critical("Raw images directory not found. Please run T012 (download_images.py) first.")
        sys.exit(1)

    success = aggregate_and_validate_metrics(raw_image_dir, output_path)

    if not success:
        logger.critical("Failed to generate valid rsametrics.csv.")
        sys.exit(1)
    
    logger.info("T015 completed successfully.")

if __name__ == "__main__":
    main()