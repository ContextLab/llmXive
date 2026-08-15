"""
Integration test for the data generation pipeline (User Story 1).

This test verifies that the teacher ground truth dataset has been generated
correctly according to the specifications:
1. The file `data/raw/teacher_ground_truth.parquet` exists.
2. The dataset contains at least 1000 rows.
3. The `routing_label` column contains valid expert identifiers consistent
   with the known DanceOPD teacher architecture.
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd

# Import configuration to get known expert IDs and paths
# Assuming config is accessible via the project structure
# We will define the known expert IDs here as a fallback if config import fails
# or to ensure the test is self-contained regarding the specific IDs.
KNOWN_EXPERT_IDS = {
    "expert_text_to_image",
    "expert_editing",
    "expert_inpainting",
    "expert_outpainting",
    "expert_super_resolution",
    "expert_style_transfer",
    "expert_depth_estimation",
    "expert_segmentation",
    "expert_denoising",
    "expert_colorization"
}

# Define the expected file path relative to the project root
# The test is run from the project root usually, or we adjust based on cwd
PROJECT_ROOT = Path(__file__).parent.parent.parent
EXPECTED_FILE_PATH = PROJECT_ROOT / "data" / "raw" / "teacher_ground_truth.parquet"


def test_teacher_ground_truth_exists():
    """Verify that the teacher_ground_truth.parquet file exists."""
    assert EXPECTED_FILE_PATH.exists(), (
        f"Expected file {EXPECTED_FILE_PATH} does not exist. "
        "Please ensure T012 and T013a have been executed successfully."
    )


def test_teacher_ground_truth_row_count():
    """Verify that the dataset contains at least 1000 rows."""
    if not EXPECTED_FILE_PATH.exists():
        pytest.skip("File does not exist, skipping row count check.")
    
    df = pd.read_parquet(EXPECTED_FILE_PATH)
    row_count = len(df)
    
    assert row_count >= 1000, (
        f"Dataset has {row_count} rows, which is less than the required minimum of 1000. "
        "Please ensure T012 and T013a generated sufficient data."
    )


def test_teacher_ground_truth_valid_routing_labels():
    """
    Verify that all routing labels in the dataset are valid expert identifiers.
    
    This ensures that T013b (exclusion of undefined routes) was performed correctly
    and that the teacher model produced labels consistent with its architecture.
    """
    if not EXPECTED_FILE_PATH.exists():
        pytest.skip("File does not exist, skipping label validation.")
    
    df = pd.read_parquet(EXPECTED_FILE_PATH)
    
    # Check if 'routing_label' column exists
    assert 'routing_label' in df.columns, (
        f"Column 'routing_label' not found in {EXPECTED_FILE_PATH}. "
        "The dataset schema is invalid."
    )
    
    # Get unique labels
    unique_labels = set(df['routing_label'].unique())
    
    # Check for any invalid labels
    invalid_labels = unique_labels - KNOWN_EXPERT_IDS
    
    assert len(invalid_labels) == 0, (
        f"Found {len(invalid_labels)} invalid routing labels in the dataset: {invalid_labels}. "
        f"Valid labels must be one of: {KNOWN_EXPERT_IDS}. "
        "Please check T013b implementation for undefined route handling."
    )


def test_teacher_ground_truth_required_columns():
    """
    Verify that the dataset contains all required columns for downstream tasks.
    """
    if not EXPECTED_FILE_PATH.exists():
        pytest.skip("File does not exist, skipping column check.")
    
    df = pd.read_parquet(EXPECTED_FILE_PATH)
    
    required_columns = {
        'prompt_embedding',
        'noise_level',
        'routing_label',
        'velocity_vector'
    }
    
    missing_columns = required_columns - set(df.columns)
    
    assert len(missing_columns) == 0, (
        f"Dataset is missing required columns: {missing_columns}. "
        "Please ensure T014 extraction logic is correct."
    )