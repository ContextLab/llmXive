"""
Contract test for T013: Verify persistence_images_10x10.csv schema and data integrity.
"""
import os
import sys
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent to path for imports if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "persistence_images_10x10.csv"
RESOLUTION = 10
EXPECTED_IMAGE_COLS = RESOLUTION * RESOLUTION  # 100 columns

def test_file_exists():
    """Verify the output file exists."""
    assert OUTPUT_FILE.exists(), f"Output file {OUTPUT_FILE} does not exist. T013 did not produce the required artifact."

def test_schema_compliance():
    """Verify the CSV schema matches the expected structure."""
    assert OUTPUT_FILE.exists()
    df = pd.read_csv(OUTPUT_FILE)
    
    # Check required base columns
    required_base_cols = ['smiles', 'valid', 'num_nodes', 'num_edges']
    for col in required_base_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check image columns (img_0 to img_99)
    expected_img_cols = [f"img_{i}" for i in range(EXPECTED_IMAGE_COLS)]
    for col in expected_img_cols:
        assert col in df.columns, f"Missing image column: {col}"
    
    # Check TDA scalar columns
    expected_tda_cols = ['tda_total_persistence', 'tda_max_persistence', 'tda_num_features']
    for col in expected_tda_cols:
        assert col in df.columns, f"Missing TDA scalar column: {col}"

def test_no_nan_values():
    """Verify no NaN values in topological columns (image and scalar features)."""
    assert OUTPUT_FILE.exists()
    df = pd.read_csv(OUTPUT_FILE)
    
    tda_cols = [c for c in df.columns if c.startswith('img_') or c.startswith('tda_')]
    
    nan_counts = df[tda_cols].isna().sum()
    total_nans = nan_counts.sum()
    
    assert total_nans == 0, f"Found {total_nans} NaN values in topological columns. Zero-vector fallback may have failed or data corruption occurred."

def test_image_vector_length():
    """Verify each image vector has exactly 100 elements (10x10)."""
    assert OUTPUT_FILE.exists()
    df = pd.read_csv(OUTPUT_FILE)
    
    img_cols = [c for c in df.columns if c.startswith('img_')]
    assert len(img_cols) == EXPECTED_IMAGE_COLS, f"Expected {EXPECTED_IMAGE_COLS} image columns, found {len(img_cols)}."

def test_non_empty_dataset():
    """Verify the dataset is not empty (power analysis requirement N>=128)."""
    assert OUTPUT_FILE.exists()
    df = pd.read_csv(OUTPUT_FILE)
    
    assert len(df) >= 128, f"Dataset size {len(df)} is less than required 128 molecules. Power analysis failed."

def test_valid_molecules_count():
    """Verify we have a reasonable number of valid molecules."""
    assert OUTPUT_FILE.exists()
    df = pd.read_csv(OUTPUT_FILE)
    
    valid_count = df['valid'].sum()
    assert valid_count > 0, "No valid molecules processed."
    # Expect most to be valid if data is clean
    assert valid_count > len(df) * 0.8, f"Too many invalid molecules: {len(df) - valid_count} out of {len(df)}."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])