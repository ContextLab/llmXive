"""
tests/unit/test_download.py

Unit tests for the download module.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import validate_and_filter_entries, TARGET_SPACE_GROUPS

def test_validate_and_filter_entries_filters_wrong_space_group():
    """Test that entries with non-target space groups are excluded."""
    entries = [
        {
            "material_id": "mp-1",
            "formula_pretty": "ABC3",
            "space_group": {"number": 221}, # Target
            "decomposition_energy_per_atom": -0.5
        },
        {
            "material_id": "mp-2",
            "formula_pretty": "DEF3",
            "space_group": {"number": 225}, # Not target
            "decomposition_energy_per_atom": -0.5
        },
        {
            "material_id": "mp-3",
            "formula_pretty": "GHI3",
            "space_group": {"number": 148}, # Target
            "decomposition_energy_per_atom": -0.5
        }
    ]

    filtered, count = validate_and_filter_entries(entries)

    assert len(filtered) == 2
    assert count == 1
    assert filtered[0]["material_id"] == "mp-1"
    assert filtered[1]["material_id"] == "mp-3"

def test_validate_and_filter_entries_excludes_missing_energy():
    """Test that entries with missing decomposition energy are excluded."""
    entries = [
        {
            "material_id": "mp-1",
            "formula_pretty": "ABC3",
            "space_group": {"number": 221},
            "decomposition_energy_per_atom": -0.5
        },
        {
            "material_id": "mp-2",
            "formula_pretty": "DEF3",
            "space_group": {"number": 221},
            "decomposition_energy_per_atom": None
        }
    ]

    filtered, count = validate_and_filter_entries(entries)

    assert len(filtered) == 1
    assert count == 1
    assert filtered[0]["material_id"] == "mp-1"

def test_validate_and_filter_entries_missing_fields():
    """Test that entries with missing material_id are excluded."""
    entries = [
        {
            "material_id": "mp-1",
            "formula_pretty": "ABC3",
            "space_group": {"number": 221},
            "decomposition_energy_per_atom": -0.5
        },
        {
            "material_id": None,
            "formula_pretty": "DEF3",
            "space_group": {"number": 221},
            "decomposition_energy_per_atom": -0.5
        }
    ]

    filtered, count = validate_and_filter_entries(entries)

    assert len(filtered) == 1
    assert count == 1
    assert filtered[0]["material_id"] == "mp-1"

@patch('code.data.download.fetch_with_backoff')
@patch('code.data.download.get_api_key')
def test_fetch_materials_project_handles_api_error(mock_key, mock_fetch):
    """Test that fetch handles API errors gracefully."""
    from code.data.download import fetch_materials_project_entries
    
    mock_key.return_value = "fake-key"
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_fetch.return_value = mock_response

    with pytest.raises(RuntimeError, match="Failed to fetch data"):
        fetch_materials_project_entries()
