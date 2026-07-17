"""
Integration test for T019: Output structured CSV.

Verifies that the output pipeline generates a valid CSV file with the correct
schema and non-null values for the expected fields.
"""
import os
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from code.config import get_project_root, get_path, ensure_dirs
from code.output_metrics import run_output_pipeline, process_image_file
from code.synthetic_data import generate_synthetic_dataset, set_seed

@pytest.fixture
def synthetic_data_setup():
    """
    Setup a temporary directory with synthetic microglia images for testing.
    Uses the existing synthetic_data generator to create real image data.
    """
    # Create a temporary directory for this test run
    temp_root = Path(tempfile.mkdtemp(prefix="t019_test_"))
    input_dir = temp_root / "raw_images"
    output_dir = temp_root / "processed"
    output_dir.mkdir(parents=True)
    input_dir.mkdir(parents=True)

    # Generate synthetic dataset into the input directory
    # We use the existing generator which creates PNG/TIFF files
    set_seed(42)
    
    # Generate a small dataset (e.g., 5 images)
    # The synthetic_data.py generates images and ground truth
    # We need to ensure images are saved to our temp input_dir
    # Since generate_synthetic_dataset usually writes to a specific config path,
    # we will manually generate images and save them to our temp dir.
    
    from code.synthetic_data import generate_microglia_cell, generate_ground_truth_metrics
    
    num_images = 5
    for i in range(num_images):
        img, meta = generate_microglia_cell(seed=i)
        # Save image with a filename that includes the required metadata
        # Expected format: <subject_id>_<brain_region>_<time_point>.png
        filename = f"subj_{i}_{meta['brain_region']}_{meta['time_point']}.png"
        save_path = input_dir / filename
        
        # Convert to uint8 if necessary (assuming generate_microglia_cell returns float)
        if img.dtype != 'uint8':
            img = (img * 255).astype('uint8')
        
        from PIL import Image
        Image.fromarray(img).save(save_path)

    yield {
        "temp_root": temp_root,
        "input_dir": input_dir,
        "output_dir": output_dir
    }

    # Cleanup
    shutil.rmtree(temp_root)

def test_t019_csv_generation(synthetic_data_setup):
    """
    Test that run_output_pipeline creates a valid CSV with required columns.
    """
    input_dir = synthetic_data_setup["input_dir"]
    output_dir = synthetic_data_setup["output_dir"]
    output_csv = output_dir / "morphological_metrics.csv"

    # Run the pipeline
    result_path = run_output_pipeline(
        input_dir=input_dir,
        output_path=output_csv,
        force_regenerate=True
    )

    # Assert file exists
    assert result_path.exists(), f"Output CSV was not created at {result_path}"

    # Load and validate
    df = pd.read_csv(result_path)

    # Check required columns (T019 requirement: brain_region tag + metrics)
    required_columns = [
        'file_name', 'brain_region', 'subject_id', 'time_point',
        'branch_points', 'soma_area', 'total_process_length',
        'sholl_max_intersections', 'sholl_decay_rate', 'processing_status'
    ]
    
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    # Check that brain_region is not null (T011 constraint)
    assert df['brain_region'].notna().all(), "Found null values in brain_region column"
    
    # Check that we have some data (since we generated 5 images)
    assert len(df) > 0, "No data was extracted from the synthetic images"
    
    # Check that processing_status is 'success' for all
    assert (df['processing_status'] == 'success').all(), "Some images failed processing"

    # Verify plausible values (T010 requirement: non-null, plausible)
    assert (df['branch_points'] >= 0).all(), "Branch points cannot be negative"
    assert (df['soma_area'] > 0).all(), "Soma area must be positive"
    assert (df['total_process_length'] > 0).all(), "Total length must be positive"

def test_t019_empty_input_handling(synthetic_data_setup):
    """
    Test that the pipeline handles an empty input directory gracefully.
    """
    empty_input = synthetic_data_setup["input_dir"].parent / "empty_input"
    empty_input.mkdir(exist_ok=True)
    output_csv = synthetic_data_setup["output_dir"] / "empty_metrics.csv"

    try:
        result_path = run_output_pipeline(
            input_dir=empty_input,
            output_path=output_csv,
            force_regenerate=True
        )

        assert result_path.exists()
        df = pd.read_csv(result_path)
        
        # Should have columns but no rows
        assert len(df) == 0
        assert 'brain_region' in df.columns
    finally:
        if empty_input.exists():
            shutil.rmtree(empty_input)