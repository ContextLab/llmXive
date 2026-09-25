"""
Unit tests for T037b: Synthetic Unit-Test Dataset generation.
Verifies that the generated dataset has the correct structure and properties.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add parent directory to path to import code modules if needed
# For this test, we assume the script is run or we test the logic directly
# Since we are testing the output of the script, we can run the script in a temp dir
# or import the functions if they were structured that way. 
# Here we test the output file after generation.

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

@pytest.fixture
def generated_dataset_path():
    """Path to the generated dataset file."""
    return PROJECT_ROOT / "data" / "raw" / "mock_oxford_pets.parquet"

def test_dataset_exists(generated_dataset_path):
    """Test that the dataset file was created."""
    assert generated_dataset_path.exists(), f"Dataset file not found at {generated_dataset_path}"

def test_dataset_schema(generated_dataset_path):
    """Test that the dataset has the required columns."""
    df = pd.read_parquet(generated_dataset_path)
    required_columns = [
        "image_path", "species_id", "prompt_text", 
        "teacher_scores", "student_scalar", "human_annotations", "primary_dimension"
    ]
    assert list(df.columns) == required_columns, f"Missing columns: {set(required_columns) - set(df.columns)}"

def test_sample_count(generated_dataset_path):
    """Test that the dataset has the expected number of samples (N=50)."""
    df = pd.read_parquet(generated_dataset_path)
    assert len(df) == 50, f"Expected 50 samples, got {len(df)}"

def test_teacher_scores_shape(generated_dataset_path):
    """Test that teacher_scores are lists of length 4."""
    df = pd.read_parquet(generated_dataset_path)
    for scores in df["teacher_scores"]:
        assert isinstance(scores, list), "teacher_scores must be a list"
        assert len(scores) == 4, f"teacher_scores must have 4 dimensions, got {len(scores)}"
        # Check range (0-10)
        for s in scores:
            assert 0 <= s <= 10, f"Teacher score {s} out of range [0, 10]"

def test_human_annotations_independence(generated_dataset_path):
    """
    Test that human annotations are generated independently of teacher scores.
    This is a structural check; we verify they exist and have the right shape.
    A true independence check would require statistical analysis, which is out of scope for unit tests.
    """
    df = pd.read_parquet(generated_dataset_path)
    for annotations in df["human_annotations"]:
        assert isinstance(annotations, list), "human_annotations must be a list"
        assert len(annotations) == 4, f"human_annotations must have 4 dimensions, got {len(annotations)}"
        # Check range (0-1)
        for a in annotations:
            assert 0 <= a <= 1, f"Human annotation {a} out of range [0, 1]"

def test_primary_dimension_calculation(generated_dataset_path):
    """Test that primary_dimension is derived correctly from prompt_text."""
    import hashlib
    df = pd.read_parquet(generated_dataset_path)
    for idx, row in df.iterrows():
        prompt = row["prompt_text"]
        expected_dim = int(hashlib.sha256(prompt.encode()).hexdigest(), 16) % 4
        assert row["primary_dimension"] == expected_dim, \
            f"Primary dimension mismatch for prompt {prompt}: expected {expected_dim}, got {row['primary_dimension']}"

def test_validation_log_updated(generated_dataset_path):
    """Test that validation_log.json was updated."""
    log_path = PROJECT_ROOT / "data" / "raw" / "validation_log.json"
    assert log_path.exists(), "validation_log.json not found"
    
    with open(log_path, 'r') as f:
        logs = json.load(f)
    
    # Find the entry for mock_oxford_pets
    mock_entry = None
    for log in logs:
        if log.get("source") == "mock_oxford_pets":
            mock_entry = log
            break
    
    assert mock_entry is not None, "No log entry found for mock_oxford_pets"
    assert mock_entry["status"] == "generated"
    assert mock_entry["n_samples"] == 50
    assert mock_entry["seed"] == 42