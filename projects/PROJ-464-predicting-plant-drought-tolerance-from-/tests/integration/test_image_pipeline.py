"""
Integration tests for the full image processing pipeline (User Story 1).

This module verifies that the end-to-end pipeline (download -> preprocess -> aggregate)
produces a valid CSV file with non-null, positive numerical values for all RSA traits.

Dependencies:
  - T012: code/download_images.py (must have run to populate data/raw/nppn_images/)
  - T013: code/preprocess_images.py (must have run to generate intermediate metrics)
  - T015: code/generate_rsametrics.py (must have run to produce data/derived/rsametrics.csv)
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories

# Expected output paths
OUTPUT_CSV_PATH = project_root / "data" / "derived" / "rsametrics.csv"
RAW_IMAGES_DIR = project_root / "data" / "raw" / "nppn_images"

REQUIRED_COLUMNS = ["species_id", "depth", "branching_density", "surface_area"]

@pytest.fixture(scope="module")
def pipeline_output():
    """
    Ensure the pipeline has been run and returns the resulting DataFrame.
    If the output file does not exist, this test assumes the pipeline
    (T012, T013, T015) has not been executed yet.
    """
    if not OUTPUT_CSV_PATH.exists():
        pytest.skip(
            f"Output file {OUTPUT_CSV_PATH} not found. "
            "Please run T012 (download), T013 (preprocess), and T015 (aggregate) first."
        )
    
    return pd.read_csv(OUTPUT_CSV_PATH)

def test_full_pipeline_generates_non_null_csv(pipeline_output):
    """
    Asserts the output CSV has a consistent number of rows with no nulls 
    and positive values for all numerical traits.
    """
    # 1. Check file is not empty
    assert not pipeline_output.empty, "Output CSV is empty."
    
    # 2. Check required columns exist
    missing_cols = set(REQUIRED_COLUMNS) - set(pipeline_output.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"
    
    # 3. Check for null values in the entire dataset
    assert pipeline_output.isnull().sum().sum() == 0, (
        "Output CSV contains null values. "
        f"Null counts per column:\n{pipeline_output.isnull().sum()}"
    )
    
    # 4. Check for positive numerical values in RSA traits
    #    (depth, branching_density, surface_area must be > 0)
    numerical_cols = ["depth", "branching_density", "surface_area"]
    for col in numerical_cols:
        if col in pipeline_output.columns:
            # Check if all values are positive
            non_positive = pipeline_output[pipeline_output[col] <= 0]
            assert non_positive.empty, (
                f"Column '{col}' contains zero or negative values. "
                f"Invalid rows:\n{non_positive}"
            )
            
            # Check for non-finite values (inf, -inf)
            assert pd.api.types.is_numeric_dtype(pipeline_output[col]), (
                f"Column '{col}' is not numeric."
            )
            if not (pd.isna(pipeline_output[col]) | (pipeline_output[col] == float('inf')) | 
                    (pipeline_output[col] == float('-inf'))).any():
                pass # No inf values found, which is good
            else:
                # Explicit check for inf just in case
                assert not (pipeline_output[col] == float('inf')).any() and not (pipeline_output[col] == float('-inf')).any(), (
                    f"Column '{col}' contains infinite values."
                )
    
    # 5. Verify species_id is not empty string
    if "species_id" in pipeline_output.columns:
        empty_species = pipeline_output[pipeline_output["species_id"].str.strip() == ""]
        assert empty_species.empty, "Output CSV contains rows with empty species_id."

def test_pipeline_consistency_with_source_images(pipeline_output):
    """
    Optional check: Ensure the number of processed images roughly matches
    the number of files in the raw directory (allowing for some skips due to corruption).
    """
    if not RAW_IMAGES_DIR.exists():
        pytest.skip("Raw images directory not found.")
    
    raw_files = list(RAW_IMAGES_DIR.glob("*"))
    # Filter for common image extensions
    image_files = [f for f in raw_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']]
    
    if not image_files:
        pytest.skip("No image files found in raw directory.")
    
    # The pipeline might skip corrupted images, so we expect output_rows <= input_images
    # But we expect at least some successful processing if the pipeline ran correctly
    output_rows = len(pipeline_output)
    
    # If we have images, we should have processed at least one (unless all were corrupted)
    # This is a soft check to ensure the pipeline actually did work
    assert output_rows > 0, (
        f"Pipeline produced 0 rows despite {len(image_files)} images found in {RAW_IMAGES_DIR}. "
        "Check logs for errors in preprocessing."
    )
    
    # Note: We don't assert output_rows == len(image_files) because T013 handles
    # corrupted images by skipping them, which is valid behavior.