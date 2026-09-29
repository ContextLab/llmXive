"""
Unit tests for Task T021b: Write Aggregated Dataset.

Verifies that the aggregated dataset retains the 'village_id' column,
has N >= 300 records, and that 'village_id' is unique per row.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path for imports if running from project root
CODE_ROOT = Path(__file__).parent.parent.parent / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

DATA_PATH = Path("data/processed/analysis_dataset_village_aggregated.csv")

def test_aggregated_dataset_exists():
    """Verify the aggregated dataset file exists."""
    assert DATA_PATH.exists(), f"Aggregated dataset file not found at {DATA_PATH}"

def test_aggregated_dataset_has_village_id_column():
    """Verify the dataset retains the 'village_id' column."""
    if not DATA_PATH.exists():
        pytest.skip("Dataset file does not exist yet.")
    
    df = pd.read_csv(DATA_PATH)
    assert "village_id" in df.columns, "Column 'village_id' is missing from the dataset."

def test_aggregated_dataset_n_ge_300():
    """Verify the dataset has N >= 300 records."""
    if not DATA_PATH.exists():
        pytest.skip("Dataset file does not exist yet.")
    
    df = pd.read_csv(DATA_PATH)
    n_rows = len(df)
    assert n_rows >= 300, f"Dataset has {n_rows} rows, which is less than the required 300."

def test_aggregated_dataset_village_id_unique():
    """Verify that 'village_id' is unique per row."""
    if not DATA_PATH.exists():
        pytest.skip("Dataset file does not exist yet.")
    
    df = pd.read_csv(DATA_PATH)
    # Check for duplicates in the village_id column
    duplicates = df["village_id"].duplicated().sum()
    assert duplicates == 0, f"Found {duplicates} duplicate village_ids. Each row must have a unique village_id after aggregation."