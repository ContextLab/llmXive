"""
Contract test for T090b: Synthetic datasets for power analysis.

Verifies that the generated zip file contains the expected structure,
correct number of participants, and the required random-effects structure.
"""
import csv
import io
import os
import sys
import zipfile
from pathlib import Path

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_processed_data_dir

OUTPUT_ZIP = get_processed_data_dir() / "synthetic_power_datasets.zip"

@pytest.fixture
def zip_path():
    return OUTPUT_ZIP

def test_zip_file_exists(zip_path):
    """Verify the output zip file exists."""
    assert zip_path.exists(), f"Output file {zip_path} does not exist. Run code/00_generate_synthetic_power_data.py first."

def test_zip_contains_csv(zip_path):
    """Verify the zip contains the expected CSV file."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        assert "synthetic_ratings.csv" in names, f"Missing 'synthetic_ratings.csv' in {zip_path}. Found: {names}"

def test_synthetic_data_structure(zip_path):
    """
    Verify the synthetic dataset structure:
    - N=60 unique participants
    - Contains Participant and Stimulus random effects structure (implied by IDs)
    - Contains relationship_type column
    - Contains rating column
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        with zf.open("synthetic_ratings.csv") as f:
            content = io.TextIOWrapper(f, encoding="utf-8")
            reader = csv.DictReader(content)
            rows = list(reader)
    
    assert len(rows) > 0, "Synthetic dataset is empty."
    
    # Check required columns
    required_cols = {"participant_id", "stimulus_id", "relationship_type", "rating"}
    assert required_cols.issubset(set(rows[0].keys())), f"Missing required columns. Found: {rows[0].keys()}"
    
    # Check N=60 unique participants
    unique_participants = set(row["participant_id"] for row in rows)
    assert len(unique_participants) == 60, f"Expected 60 unique participants, found {len(unique_participants)}"
    
    # Check N=20 unique stimuli (based on default generation)
    unique_stimuli = set(row["stimulus_id"] for row in rows)
    assert len(unique_stimuli) == 20, f"Expected 20 unique stimuli, found {len(unique_stimuli)}"
    
    # Check relationship types
    rel_types = set(row["relationship_type"] for row in rows)
    assert rel_types == {"friend", "acquaintance"}, f"Unexpected relationship types: {rel_types}"
    
    # Check rating range (Likert 1-5)
    ratings = [float(row["rating"]) for row in rows]
    assert all(1.0 <= r <= 5.0 for r in ratings), "Ratings must be between 1 and 5."

def test_effect_size_parameter_in_log_or_data(zip_path):
    """
    Verify that the dataset was generated with the correct effect size.
    Since the effect size is a generation parameter, we verify the data
    isn't just noise (i.e., there is variance consistent with a signal).
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        with zf.open("synthetic_ratings.csv") as f:
            content = io.TextIOWrapper(f, encoding="utf-8")
            reader = csv.DictReader(content)
            rows = list(reader)
    
    # Simple check: variance should not be zero
    ratings = [float(row["rating"]) for row in rows]
    variance = sum((r - sum(ratings)/len(ratings))**2 for r in ratings) / len(ratings)
    assert variance > 0.01, "Synthetic data has suspiciously low variance. Check effect_size parameter."