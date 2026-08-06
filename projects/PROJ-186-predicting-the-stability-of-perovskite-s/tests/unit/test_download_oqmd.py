"""
Unit tests for OQMD ingestion logic (T013).
"""
import os
import sys
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.download_oqmd import fetch_oqmd_entries, merge_oqmd_with_mp

@patch('code.data.download_oqmd.requests.get')
def test_fetch_oqmd_entries_returns_dataframe(mock_get):
    """Test that fetch_oqmd_entries returns a DataFrame with correct columns."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'entries': [
            {'formula': 'BaTiO3', 'space_group': 221, 'decomposition_energy': -0.5},
            {'formula': 'SrZrO3', 'space_group': 148, 'decomposition_energy': -0.3}
        ]
    }
    mock_get.return_value = mock_response

    df = fetch_oqmd_entries(limit=100)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'formula' in df.columns
    assert 'space_group' in df.columns
    assert 'decomposition_energy' in df.columns
    assert df.loc[0, 'formula'] == 'BaTiO3'
    assert df.loc[0, 'space_group'] == 221

@patch('code.data.download_oqmd.requests.get')
def test_fetch_oqmd_entries_raises_on_error(mock_get):
    """Test that fetch_oqmd_entries raises an error on request failure."""
    mock_get.side_effect = Exception("Network error")
    
    with pytest.raises(RuntimeError):
        fetch_oqmd_entries(limit=100)

def test_merge_oqmd_with_mp_skips_when_mp_sufficient():
    """Test that OQMD is skipped if MP data is >= threshold."""
    mp_df = pd.DataFrame({'formula': ['A'], 'space_group': [221], 'decomposition_energy': [-0.5]})
    oqmd_df = pd.DataFrame({'formula': ['B'], 'space_group': [221], 'decomposition_energy': [-0.4]})
    
    result_df, status = merge_oqmd_with_mp(mp_df, oqmd_df, mp_threshold=1)
    
    assert len(result_df) == 1
    assert 'OQMD skipped' in status

def test_merge_oqmd_with_mp_merges_when_mp_insufficient():
    """Test that OQMD is merged if MP data is < threshold."""
    mp_df = pd.DataFrame({'formula': ['A'], 'space_group': [221], 'decomposition_energy': [-0.5]})
    oqmd_df = pd.DataFrame({'formula': ['B'], 'space_group': [148], 'decomposition_energy': [-0.4]})
    
    result_df, status = merge_oqmd_with_mp(mp_df, oqmd_df, mp_threshold=5)
    
    assert len(result_df) == 2
    assert 'OQMD merged' in status
    assert 'source' in result_df.columns
    assert result_df.loc[0, 'source'] == 'MaterialsProject'
    assert result_df.loc[1, 'source'] == 'OQMD'