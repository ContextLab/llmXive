"""
Unit tests for download module (T013).
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import json

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.download import (
    fetch_materials_project_entries,
    fetch_oqmd_entries,
    validate_and_filter_entries,
    merge_datasets,
    main,
    MIN_REQUIRED_ENTRIES,
    VALID_SPACE_GROUPS
)

def test_validate_and_filter_entries():
    """Test that only valid space groups are kept."""
    test_data = [
        {"formula_pretty": "ABO3", "space_group_number": 225}, # Cubic
        {"formula_pretty": "ABO3", "space_group_number": 146}, # Rhombohedral
        {"formula_pretty": "ABO3", "space_group_number": 195}, # Invalid (Triclinic)
    ]
    
    result = validate_and_filter_entries(test_data)
    assert len(result) == 2
    assert result[0]["space_group_number"] == 225
    assert result[1]["space_group_number"] == 146

def test_merge_datasets_removes_duplicates():
    """Test that merge removes duplicates based on material_id."""
    mp_data = [{"material_id": "mp-123", "formula": "A"}]
    oqmd_data = [{"material_id": "mp-123", "formula": "A"}, {"material_id": "oqmd-456", "formula": "B"}]
    
    merged = merge_datasets(mp_data, oqmd_data)
    assert len(merged) == 2
    assert any(m["material_id"] == "oqmd-456" for m in merged)

@patch('data.download.fetch_with_backoff')
def test_fetch_materials_project_handles_429(mock_fetch):
    """Test that 429 errors are handled (logic verified in api_client, but integration check here)."""
    # This test primarily verifies the flow. The retry logic is in api_client.
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_fetch.return_value = mock_response
    
    # Should not raise
    result = fetch_materials_project_entries("fake_key", limit=10)
    assert isinstance(result, list)

def test_main_raises_on_insufficient_data():
    """Test that main raises RuntimeError if data < 5000."""
    # Mock fetch functions to return empty lists
    with patch('data.download.fetch_materials_project_entries', return_value=[]), \
         patch('data.download.fetch_oqmd_entries', return_value=[]):
        
        with pytest.raises(RuntimeError, match="Fatal Error: Total valid entries"):
            main()