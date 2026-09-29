import pytest
import pandas as pd
import os
from analysis.pathway import validate_kegg_ids, _build_kegg_valid_cache, load_kegg_mapping

def test_validate_kegg_ids_valid_and_invalid():
    """
    Test that validate_kegg_ids correctly separates valid and invalid IDs.
    This test relies on the cache built from the existing mapping file.
    """
    # Ensure the cache is built
    valid_cache = _build_kegg_valid_cache()
    
    # Prepare a list of test IDs: some known valid (from cache), some clearly invalid
    test_ids = list(valid_cache)[:5] + ["INVALID_ID_1", "C99999", ""]
    
    if not valid_cache:
        # If no cache is available (e.g., mapping file missing), all should be invalid
        valid, invalid = validate_kegg_ids(test_ids)
        assert len(valid) == 0
        assert len(invalid) == len(test_ids)
        return

    valid_ids, invalid_ids = validate_kegg_ids(test_ids)
    
    # Check that valid IDs are returned
    assert set(valid_ids).issubset(set(valid_cache))
    assert len(valid_ids) == 5
    
    # Check that invalid IDs are detected
    assert "INVALID_ID_1" in invalid_ids
    assert "C99999" in invalid_ids
    assert "" in invalid_ids

def test_validate_kegg_ids_empty_list():
    """Test handling of empty input."""
    valid, invalid = validate_kegg_ids([])
    assert valid == []
    assert invalid == []

def test_validate_kegg_ids_all_valid():
    """Test when all IDs are valid."""
    valid_cache = _build_kegg_valid_cache()
    if not valid_cache:
        pytest.skip("KEGG mapping cache not available for test")
    
    test_ids = list(valid_cache)[:3]
    valid, invalid = validate_kegg_ids(test_ids)
    assert len(valid) == 3
    assert len(invalid) == 0

def test_validate_kegg_ids_all_invalid():
    """Test when all IDs are invalid."""
    test_ids = ["FAKE1", "FAKE2", "FAKE3"]
    valid, invalid = validate_kegg_ids(test_ids)
    assert len(valid) == 0
    assert len(invalid) == 3
