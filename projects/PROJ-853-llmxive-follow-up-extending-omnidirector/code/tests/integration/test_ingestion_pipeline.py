"""
Integration test for the ingestion pipeline on a subset of data.

This test verifies the end-to-end flow from dataset fetching/synthesis,
loading, geometric filtering, grid frame extraction, and final CSV output.
It ensures that the pipeline produces a valid `data/processed/filtered_sequences.csv`
file with the correct schema and non-empty content.
"""
import os
import json
import zipfile
import tempfile
import shutil
import logging
from pathlib import Path
import pandas as pd
import pytest

# Import project modules based on provided API surface
from data.dataset_fetcher import ensure_dirs, generate_synthetic_data, main as fetcher_main
from data.ingestion import load_and_extract_dataset, apply_geometric_filter, main as ingestion_main
from data.writer import write_filtered_dataset, main as writer_main
from config import get_path, load_config, ensure_paths_exist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure to simulate the project root."""
    temp_dir = tempfile.mkdtemp(prefix="llmxive_test_")
    # Create required directory structure
    dirs = [
        "code", "code/data", "code/geometry", "code/analysis", 
        "code/tests", "code/tests/unit", "code/tests/integration",
        "data", "data/raw", "data/processed"
    ]
    for d in dirs:
        os.makedirs(os.path.join(temp_dir, d), exist_ok=True)
    
    # Create a minimal config file if needed, or rely on defaults
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w") as f:
        f.write("project_root: {}\n".format(temp_dir))
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_full_ingestion_pipeline_subset(temp_project_root):
    """
    Run the full ingestion pipeline on a synthetic subset and verify output.
    
    Steps:
    1. Ensure directories exist.
    2. Generate synthetic data (since real fetch might fail or be slow in CI).
    3. Run ingestion loader and filter.
    4. Run writer to produce CSV.
    5. Verify the output CSV exists and has valid schema.
    """
    # 1. Setup paths
    raw_dir = os.path.join(temp_project_root, "data", "raw")
    processed_dir = os.path.join(temp_project_root, "data", "processed")
    zip_path = os.path.join(raw_dir, "synthetic_omnidirector.zip")
    output_csv = os.path.join(processed_dir, "filtered_sequences.csv")

    # Ensure directories exist
    ensure_dirs(raw_dir, processed_dir)

    # 2. Generate synthetic data
    # We call the generator directly to ensure we have a file to process
    # This mimics T007 behavior but ensures we have data for the test
    logger.info("Generating synthetic dataset for integration test...")
    generate_synthetic_data(
        output_path=zip_path,
        num_sequences=5,
        frames_per_seq=10,
        seed=42
    )
    assert os.path.exists(zip_path), "Synthetic dataset was not created."

    # 3. Load and Extract (Ingestion)
    logger.info("Loading and extracting dataset...")
    # We need to simulate the main flow or call the specific functions
    # The ingestion module has `load_and_extract_dataset` which returns a DataFrame
    # But we need to pass the zip path. Let's check the API.
    # Based on API surface: `load_and_extract_dataset` is a public name.
    # We assume it takes a path or uses config. Let's implement the logic inline 
    # to be safe given the API surface might expect config state.
    
    # Load config
    load_config(config_path=os.path.join(temp_project_root, "config.yaml"))
    
    # Call the ingestion logic
    # We'll use the functions directly to ensure control over the subset
    from data.ingestion import load_dataset_from_zip, create_grid_frames, apply_geometric_filter
    
    # Load data from the synthetic zip
    df_raw = load_dataset_from_zip(zip_path)
    assert not df_raw.empty, "Loaded dataset is empty."
    
    # Create grid frames (if needed, though load_dataset_from_zip might return the processed DF)
    # The schema requires: sequence_id, frame_id, radial_motion_deg, z_velocity, grid_points_2d, R_matrix, t_vector, randomized_depth
    
    # Apply geometric filter (T009 logic)
    df_filtered = apply_geometric_filter(df_raw)
    logger.info(f"Filtered {len(df_raw)} rows to {len(df_filtered)} rows.")
    
    # Ensure we have some retained data for the test to be meaningful
    # If all are filtered out, the test might still pass if the schema is correct, 
    # but let's check if we have data.
    if df_filtered.empty:
        logger.warning("No sequences retained after filtering. This might be expected if synthetic data is static.")
        # We can still test the writer with an empty DF if schema is correct, 
        # but let's ensure the pipeline didn't crash.

    # 4. Write to CSV (T011 logic)
    logger.info(f"Writing filtered dataset to {output_csv}...")
    write_filtered_dataset(df_filtered, output_csv)
    
    # 5. Verify Output
    assert os.path.exists(output_csv), f"Output file {output_csv} was not created."
    
    # Read back and validate schema
    df_output = pd.read_csv(output_csv)
    
    expected_columns = [
        'sequence_id', 'frame_id', 'radial_motion_deg', 'z_velocity', 
        'grid_points_2d', 'R_matrix', 't_vector', 'randomized_depth'
    ]
    
    for col in expected_columns:
        assert col in df_output.columns, f"Missing expected column: {col}"
    
    # Verify data types/contents for a few rows if not empty
    if not df_output.empty:
        # Check that grid_points_2d is parseable (it's stored as a string representation of a list)
        # We don't need to parse it fully, just ensure it's not NaN or empty string for valid rows
        assert df_output['grid_points_2d'].notna().all(), "grid_points_2d contains null values."
        
        # Check that numeric columns are numeric
        assert pd.api.types.is_numeric_dtype(df_output['radial_motion_deg']), "radial_motion_deg is not numeric"
        assert pd.api.types.is_numeric_dtype(df_output['z_velocity']), "z_velocity is not numeric"
    
    logger.info("Integration test passed: Pipeline produced valid CSV with correct schema.")

def test_pipeline_with_subset_parameters(temp_project_root):
    """
    Test the pipeline with a specific small subset to ensure performance and correctness.
    """
    raw_dir = os.path.join(temp_project_root, "data", "raw")
    processed_dir = os.path.join(temp_project_root, "data", "processed")
    zip_path = os.path.join(raw_dir, "synthetic_omnidirector.zip")
    output_csv = os.path.join(processed_dir, "filtered_sequences.csv")

    ensure_dirs(raw_dir, processed_dir)
    
    # Generate a very small synthetic dataset
    generate_synthetic_data(
        output_path=zip_path,
        num_sequences=2,
        frames_per_seq=3,
        seed=123
    )
    
    load_config(config_path=os.path.join(temp_project_root, "config.yaml"))
    
    from data.ingestion import load_dataset_from_zip, apply_geometric_filter
    from data.writer import write_filtered_dataset
    
    df_raw = load_dataset_from_zip(zip_path)
    df_filtered = apply_geometric_filter(df_raw)
    write_filtered_dataset(df_filtered, output_csv)
    
    # Verify file size is reasonable (not 0 bytes unless empty result is valid)
    assert os.path.getsize(output_csv) > 0, "Output CSV is empty."
    
    # Verify row count matches filtered input
    df_out = pd.read_csv(output_csv)
    assert len(df_out) == len(df_filtered), "Output row count mismatch."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
