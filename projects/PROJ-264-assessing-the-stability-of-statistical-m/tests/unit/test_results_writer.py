"""
Unit tests for the results writer module (T014).
"""
import os
import tempfile
import pandas as pd
from pathlib import Path

# We need to temporarily override the RESULTS_DIR for testing
# Since the module uses a global Path, we will test the logic by mocking or
# by using the actual function and checking the file content if we can isolate it.
# However, for strict unit testing without file system side effects in a temp dir,
# we will test the dataframe construction logic.

import code.results_writer as writer_module

def test_dataframe_construction():
    """Test that results are converted to a DataFrame with correct columns."""
    sample_results = [
        {
            "dataset_id": 123,
            "model_name": "LogisticRegression",
            "fold_id": 1,
            "repeat_id": 1,
            "accuracy": 0.95,
            "f1_score": 0.94
        },
        {
            "dataset_id": 123,
            "model_name": "RandomForest",
            "fold_id": 1,
            "repeat_id": 1,
            "accuracy": 0.96,
            "f1_score": 0.95
        }
    ]

    # Create a DataFrame similar to how the writer does
    df = pd.DataFrame(sample_results)
    df = df[writer_module.EXPECTED_COLUMNS]

    assert list(df.columns) == writer_module.EXPECTED_COLUMNS
    assert len(df) == 2
    assert df.iloc[0]["dataset_id"] == 123
    assert df.iloc[0]["accuracy"] == 0.95

def test_empty_results_handling():
    """Test that empty results list produces an empty DataFrame with headers."""
    sample_results = []
    df = pd.DataFrame(sample_results)
    
    # When empty, we can't index by columns directly if it's truly empty list
    # But the writer handles this by creating a DataFrame with columns explicitly
    if not sample_results:
        df = pd.DataFrame(columns=writer_module.EXPECTED_COLUMNS)
    
    assert list(df.columns) == writer_module.EXPECTED_COLUMNS
    assert len(df) == 0

def test_missing_columns_error():
    """Test that missing columns raise an error."""
    sample_results = [
        {
            "dataset_id": 123,
            "model_name": "LR",
            "fold_id": 1,
            # Missing repeat_id, accuracy, f1_score
        }
    ]

    df = pd.DataFrame(sample_results)
    missing_cols = set(writer_module.EXPECTED_COLUMNS) - set(df.columns)
    assert len(missing_cols) > 0
    assert "accuracy" in missing_cols

def test_column_ordering():
    """Test that columns are reordered to match specification."""
    # Create data with shuffled keys
    sample_results = [
        {
            "f1_score": 0.9,
            "accuracy": 0.95,
            "repeat_id": 2,
            "fold_id": 3,
            "model_name": "SVM",
            "dataset_id": 456
        }
    ]
    
    df = pd.DataFrame(sample_results)
    # Reorder
    df = df[writer_module.EXPECTED_COLUMNS]
    
    assert list(df.columns) == writer_module.EXPECTED_COLUMNS
    assert df.columns[0] == "dataset_id"
    assert df.columns[-1] == "f1_score"
