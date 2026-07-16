"""
Integration tests for the metric extraction pipeline (User Story 2).

This test verifies that the extraction pipeline runs successfully on a
specific subject (sub-01) and produces the expected output file with
the correct schema.
"""
import os
import pytest
from pathlib import Path
import pandas as pd

# Import the pipeline function from the extract module
from code.extract import run_extraction_pipeline


@pytest.mark.integration
def test_metric_extraction_sub_01():
    """
    Integration test: Run extraction on sub-01, assert results/metrics.csv
    exists with required columns: standard_amplitude, deviant_amplitude, peak_detected.
    
    This test assumes that the preprocessing pipeline (T018) has successfully
    generated `data/processed/epo_raw.fif` for subject 'sub-01' with conditions
    'standard' and 'deviant'.
    """
    # Define project root and expected paths
    # Assuming the test runs from the project root or the path is relative to the repo
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    results_dir = project_root / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = results_dir / "metrics.csv"
    
    # Clean up any existing output file to ensure a fresh run
    if output_file.exists():
        output_file.unlink()
    
    # Define the subject ID to test
    subject_id = "sub-01"
    
    # Run the extraction pipeline
    # The pipeline is expected to:
    # 1. Load epochs from data/processed/epo_raw.fif
    # 2. Compute average ERPs for standard and deviant
    # 3. Compute difference wave
    # 4. Extract peak metrics (amplitude, latency)
    # 5. Calculate SNR
    # 6. Save to results/metrics.csv
    try:
        run_extraction_pipeline(subject_ids=[subject_id])
    except Exception as e:
        # If the pipeline fails (e.g., because input data is missing),
        # the test fails. This is expected if T018 hasn't run or data is missing.
        # We do not catch this to allow pytest to report the failure clearly.
        raise RuntimeError(f"Extraction pipeline failed for {subject_id}: {e}") from e
    
    # Assert that the output file exists
    assert output_file.exists(), f"Expected output file {output_file} was not created."
    
    # Load the CSV and verify schema
    df = pd.read_csv(output_file)
    
    # Check that the file is not empty (should have at least one row for sub-01)
    assert len(df) > 0, f"Output file {output_file} is empty."
    
    # Verify the required columns exist
    required_columns = [
        "standard_amplitude",
        "deviant_amplitude",
        "peak_detected"
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    assert len(missing_columns) == 0, (
        f"Missing required columns in {output_file}: {missing_columns}. "
        f"Found columns: {list(df.columns)}"
    )
    
    # Additional sanity checks on data types/values if possible
    # Ensure 'peak_detected' is boolean-like (or at least present)
    assert df["peak_detected"].dtype in [bool, "bool", "object", "int64", "float64"], \
        f"Column 'peak_detected' has unexpected dtype: {df['peak_detected'].dtype}"
    
    # If the test passes, the integration is successful
    # No return value needed; pytest passes if no assertion fails