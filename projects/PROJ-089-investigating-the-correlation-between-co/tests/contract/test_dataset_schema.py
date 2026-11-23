"""
Contract test for unified_metrics.csv schema.

This test validates that the output of the data preprocessing pipeline
(data/processed/unified_metrics.csv) adheres to the expected schema defined
in contracts/dataset.schema.yaml.

It checks:
1. File existence.
2. Required columns presence.
3. Data types and non-null constraints for critical metrics.
4. Valid ranges for specific fields (e.g., avg_loc > 0).
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from typing import List, Set

# Add project root to path for imports if running from tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories, get_config_summary

# Expected schema based on tasks.md and data-model.md
# Columns: total_lines_changed, debt_score, avg_loc, contributor_count, repo_id, file_path, language
REQUIRED_COLUMNS: Set[str] = {
    "repo_id",
    "file_path",
    "language",
    "total_lines_changed",
    "debt_score",
    "avg_loc",
    "contributor_count"
}

CRITICAL_COLUMNS: Set[str] = {
    "total_lines_changed",
    "debt_score",
    "avg_loc",
    "contributor_count"
}

OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "unified_metrics.csv"

@pytest.fixture(scope="module")
def dataset():
    """Load the dataset once for the module if it exists."""
    ensure_directories()
    if not OUTPUT_PATH.exists():
        pytest.fail(f"Dataset file not found at {OUTPUT_PATH}. "
                    "Run the data extraction and preprocessing pipeline first.")
    
    try:
        df = pd.read_csv(OUTPUT_PATH)
    except Exception as e:
        pytest.fail(f"Failed to read CSV: {e}")
    
    if df.empty:
        pytest.fail("Dataset is empty (0 rows). The pipeline must produce at least one row.")
    
    return df

def test_schema_columns_exist(dataset: pd.DataFrame):
    """Verify all required columns are present."""
    existing_cols = set(dataset.columns)
    missing = REQUIRED_COLUMNS - existing_cols
    assert not missing, f"Missing required columns: {missing}"

def test_no_null_critical_metrics(dataset: pd.DataFrame):
    """Verify critical metric columns contain no null values."""
    for col in CRITICAL_COLUMNS:
        null_count = dataset[col].isna().sum()
        assert null_count == 0, f"Column '{col}' contains {null_count} null values."

def test_data_types_numeric(dataset: pd.DataFrame):
    """Verify critical metrics are numeric."""
    for col in CRITICAL_COLUMNS:
        if not pd.api.types.is_numeric_dtype(dataset[col]):
            # Attempt conversion to check if they are just strings of numbers
            try:
                dataset[col] = pd.to_numeric(dataset[col])
            except (ValueError, TypeError):
                pytest.fail(f"Column '{col}' is not numeric and cannot be converted.")

def test_positive_metrics(dataset: pd.DataFrame):
    """Verify that metrics representing counts/scores are non-negative."""
    # avg_loc must be strictly positive (division by zero check logic usually implies > 0)
    assert (dataset["avg_loc"] > 0).all(), "Found rows with avg_loc <= 0."
    
    # Counts and scores should be >= 0
    assert (dataset["total_lines_changed"] >= 0).all(), "Found negative total_lines_changed."
    assert (dataset["debt_score"] >= 0).all(), "Found negative debt_score."
    assert (dataset["contributor_count"] >= 0).all(), "Found negative contributor_count."

def test_file_path_format(dataset: pd.DataFrame):
    """Verify file_path is not empty and looks like a path."""
    assert (dataset["file_path"].str.len() > 0).all(), "Found empty file_path."
    # Basic check: should contain at least one slash or be a filename
    # This is a soft check as paths can vary by OS, but usually has separators
    # We just ensure it's not just whitespace
    assert not dataset["file_path"].str.isspace().any(), "Found whitespace-only file_path."

def test_repo_id_non_empty(dataset: pd.DataFrame):
    """Verify repo_id is populated."""
    assert (dataset["repo_id"].str.len() > 0).all(), "Found empty repo_id."

def test_language_populated(dataset: pd.DataFrame):
    """Verify language is populated."""
    assert (dataset["language"].str.len() > 0).all(), "Found empty language."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])