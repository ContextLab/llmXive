"""
Integration test for data completeness check (T011).

Verifies that the data completeness check correctly identifies
when the dataset has <95% valid records and triggers an error.

This test uses the real dataset from HuggingFace (codeparliament/github-code-search)
and validates the completeness logic implemented in code/data/preprocess.py.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.config import set_global_seed, get_seed
from code.utils.logger import get_logger, log_data_completeness, log_validation_error
from code.data.preprocess import check_data_completeness, validate_dataset


@pytest.fixture(scope="module")
def real_dataset():
    """
    Load the real dataset from HuggingFace for integration testing.
    This fixture ensures we're testing with actual data, not mocks.
    """
    try:
        from datasets import load_dataset
        # Load a small subset for faster testing
        dataset = load_dataset(
            "codeparliament/github-code-search",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
        # Convert to pandas for easier manipulation
        df_list = []
        count = 0
        for item in dataset:
            df_list.append(item)
            count += 1
            if count >= 1000:  # Limit to 1000 records for testing
                break
        return pd.DataFrame(df_list)
    except Exception as e:
        pytest.skip(f"Could not load real dataset: {e}")
        return pd.DataFrame()


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_completeness_check_with_real_data(real_dataset, temp_output_dir):
    """
    Test that completeness check runs on real data and reports correctly.
    
    This test verifies:
    1. The completeness check function executes without errors
    2. It correctly calculates the percentage of valid records
    3. It returns the expected structure
    """
    if real_dataset.empty:
        pytest.skip("Real dataset not available")
    
    # Set seed for reproducibility
    set_global_seed(42)
    
    # Run completeness check
    result = check_data_completeness(real_dataset)
    
    # Verify result structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "total_records" in result, "Result should contain total_records"
    assert "valid_records" in result, "Result should contain valid_records"
    assert "completeness_percentage" in result, "Result should contain completeness_percentage"
    assert "missing_fields" in result, "Result should contain missing_fields"
    
    # Verify calculations
    assert result["total_records"] > 0, "Should have records to check"
    assert 0 <= result["completeness_percentage"] <= 100, "Percentage should be between 0 and 100"
    
    # Log the result
    log_data_completeness(
        completeness=result["completeness_percentage"],
        total_records=result["total_records"],
        valid_records=result["valid_records"]
    )


def test_completeness_threshold_failure(temp_output_dir):
    """
    Test that completeness check correctly triggers an error when <95% valid.
    
    This test creates a synthetic dataset with known missing data to verify
    the error triggering logic works correctly.
    """
    # Create a dataset with 50% missing critical fields
    data = {
        "pr_id": [f"pr_{i}" for i in range(100)],
        "code_diff": [f"diff_{i}" if i % 2 == 0 else None for i in range(100)],
        "review_comments": [f"comment_{i}" if i % 2 == 0 else None for i in range(100)],
        "merge_timestamp": [f"ts_{i}" if i % 2 == 0 else None for i in range(100)],
    }
    df = pd.DataFrame(data)
    
    # Run completeness check
    result = check_data_completeness(df)
    
    # Verify it detected the low completeness
    assert result["completeness_percentage"] < 95, "Should detect <95% completeness"
    
    # Test validate_dataset which should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        validate_dataset(df, min_completeness=95.0, output_dir=temp_output_dir)
    
    # Verify error message contains relevant info
    error_msg = str(exc_info.value)
    assert "completeness" in error_msg.lower(), "Error message should mention completeness"
    assert "95" in error_msg, "Error message should mention threshold"
    
    # Verify error report was written
    error_report_path = temp_output_dir / "error_report.json"
    assert error_report_path.exists(), "Error report should be written to disk"
    
    with open(error_report_path, 'r') as f:
        error_report = json.load(f)
    
    assert "reason" in error_report, "Error report should contain reason"
    assert error_report["reason"] == "Data completeness below threshold"
    assert error_report["completeness_percentage"] < 95


def test_completeness_threshold_success(temp_output_dir):
    """
    Test that completeness check passes when >=95% valid records.
    """
    # Create a dataset with 98% valid records
    data = {
        "pr_id": [f"pr_{i}" for i in range(100)],
        "code_diff": [f"diff_{i}" for i in range(100)],
        "review_comments": [f"comment_{i}" for i in range(100)],
        "merge_timestamp": [f"ts_{i}" for i in range(100)],
    }
    # Introduce 2 missing values (98% completeness)
    data["code_diff"][98] = None
    data["code_diff"][99] = None
    
    df = pd.DataFrame(data)
    
    # This should NOT raise an error
    result = validate_dataset(df, min_completeness=95.0, output_dir=temp_output_dir)
    
    assert result["completeness_percentage"] >= 95, "Should pass 95% threshold"
    assert result["status"] == "pass", "Validation status should be 'pass'"


def test_missing_fields_detection(temp_output_dir):
    """
    Test that the check correctly identifies which fields are missing.
    """
    data = {
        "pr_id": [f"pr_{i}" for i in range(50)],
        "code_diff": [f"diff_{i}" for i in range(50)],
        "review_comments": [None] * 50,  # All missing
        "merge_timestamp": [f"ts_{i}" for i in range(50)],
    }
    df = pd.DataFrame(data)
    
    result = check_data_completeness(df)
    
    assert "review_comments" in result["missing_fields"], \
        "Should detect 'review_comments' as missing field"
    assert result["missing_fields"]["review_comments"] == 50, \
        "Should count 50 missing values in review_comments"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
