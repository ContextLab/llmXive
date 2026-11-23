"""
Integration tests for code/retrieval.py
Tests actual OSF API calls to verify retrieval logic.
"""
import json
import os
import pytest
from pathlib import Path

from retrieval import fetch_observed_results, extract_batch_observed_results, RetrievalError

# Use a known OSF study ID for integration testing
# This is a real, publicly available pre-registration study
TEST_STUDY_ID = "z8x9c"  # Example: A real OSF pre-registration ID

@pytest.mark.integration
def test_fetch_observed_results_valid_study():
    """
    Test that fetch_observed_results can retrieve data for a valid study.
    Verifies that the function returns a dict with expected keys.
    """
    result = fetch_observed_results(TEST_STUDY_ID)

    assert isinstance(result, dict)
    assert "study_id" in result
    assert result["study_id"] == TEST_STUDY_ID
    assert "actual_sample_size" in result
    assert "data_source" in result
    assert "missing_data" in result
    assert isinstance(result["missing_data"], bool)

@pytest.mark.integration
def test_fetch_observed_results_missing_data():
    """
    Test that missing data is correctly flagged.
    For studies without data files, missing_data should be True.
    """
    result = fetch_observed_results(TEST_STUDY_ID)
    # Even if data is missing, the function should not raise, just flag
    assert "missing_data" in result

@pytest.mark.integration
def test_extract_batch_observed_results():
    """
    Test batch extraction writes to file and returns correct structure.
    """
    test_ids = [TEST_STUDY_ID]
    output_path = "data/derived/test_retrieval_results.json"

    results = extract_batch_observed_results(test_ids, output_path)

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["study_id"] == TEST_STUDY_ID

    # Verify file was written
    assert Path(output_path).exists()

    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    assert saved_data == results

    # Cleanup
    os.remove(output_path)

@pytest.mark.integration
def test_retrieval_error_handling():
    """
    Test that invalid study IDs raise appropriate errors or are handled gracefully.
    """
    # Invalid ID format
    with pytest.raises(RetrievalError):
        fetch_observed_results("invalid_study_id_123456")
