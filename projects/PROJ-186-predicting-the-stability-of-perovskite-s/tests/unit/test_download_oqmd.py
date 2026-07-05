import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.download_oqmd import fetch_oqmd_entries, validate_and_filter_oqmd, merge_oqmd_with_mp, main

class TestOQMDIngestion:
    """Tests for OQMD ingestion logic."""

    def test_fetch_oqmd_entries_success(self):
        """Test successful fetch of OQMD data."""
        mock_response = MagicMock()
        mock_response.text = "formula,space_group_number,decomposition_energy\nCaTiO3,221,-0.5\nBaZrO3,221,-0.6"
        mock_response.raise_for_status = MagicMock()
        
        with patch('code.data.download_oqmd.requests.get', return_value=mock_response):
            df = fetch_oqmd_entries("http://fake-url.com/data.csv")
            assert len(df) == 2
            assert 'formula' in df.columns
            assert 'space_group_number' in df.columns
            assert 'decomposition_energy' in df.columns

    def test_fetch_oqmd_entries_failure(self):
        """Test fetch failure raises RuntimeError."""
        with patch('code.data.download_oqmd.requests.get', side_effect=Exception("Network error")):
            with pytest.raises(RuntimeError, match="OQMD fetch failed"):
                fetch_oqmd_entries("http://fake-url.com/data.csv")

    def test_validate_and_filter_oqmd_missing_columns(self):
        """Test validation fails if required columns are missing."""
        df = pd.DataFrame({'wrong_col': [1, 2]})
        with pytest.raises(ValueError, match="missing required columns"):
            validate_and_filter_oqmd(df)

    def test_validate_and_filter_oqmd_removes_nulls(self):
        """Test that null decomposition_energy and invalid space groups are removed."""
        df = pd.DataFrame({
            'formula': ['A', 'B', 'C', 'D'],
            'space_group_number': [221, 221, None, 148],
            'decomposition_energy': [-0.5, None, -0.6, -0.7]
        })
        
        filtered_df, excluded_count = validate_and_filter_oqmd(df)
        
        # Should keep 'A' (valid), 'D' (valid). 'B' has null energy, 'C' has null space group.
        assert len(filtered_df) == 2
        assert excluded_count == 2
        assert 'formula' in filtered_df.columns
        assert 'space_group_number' in filtered_df.columns
        assert 'decomposition_energy' in filtered_df.columns

    def test_merge_oqmd_with_mp(self):
        """Test merging OQMD and MP data."""
        mp_df = pd.DataFrame({
            'formula': ['MP_A'],
            'space_group': [221],
            'decomposition_energy': [-0.5]
        })
        oqmd_df = pd.DataFrame({
            'formula': ['OQMD_A'],
            'space_group_number': [221],
            'decomposition_energy': [-0.6]
        })
        
        merged = merge_oqmd_with_mp(mp_df, oqmd_df)
        
        assert len(merged) == 2
        assert 'space_group' in merged.columns
        assert 'formula' in merged.columns
        assert 'decomposition_energy' in merged.columns

    @patch('code.data.download_oqmd.fetch_oqmd_entries')
    @patch('code.data.download_oqmd.validate_and_filter_oqmd')
    def test_main_skips_oqmd_if_mp_sufficient(self, mock_validate, mock_fetch):
        """Test that OQMD fetch is skipped if MP data is sufficient."""
        mp_df = pd.DataFrame({'formula': ['A'] * 6000, 'space_group': [221], 'decomposition_energy': [-0.5]})
        
        result = main(mp_df=mp_df, min_total_entries=5000)
        
        mock_fetch.assert_not_called()
        mock_validate.assert_not_called()
        assert len(result) == 6000

    @patch('code.data.download_oqmd.fetch_oqmd_entries')
    @patch('code.data.download_oqmd.validate_and_filter_oqmd')
    def test_main_fetches_oqmd_if_mp_insufficient(self, mock_validate, mock_fetch):
        """Test that OQMD is fetched if MP data is insufficient."""
        mp_df = pd.DataFrame({'formula': ['A'] * 1000, 'space_group': [221], 'decomposition_energy': [-0.5]})
        mock_fetch.return_value = pd.DataFrame({'formula': ['B'] * 5000, 'space_group_number': [221], 'decomposition_energy': [-0.6]})
        mock_validate.return_value = (pd.DataFrame({'formula': ['B'] * 5000, 'space_group_number': [221], 'decomposition_energy': [-0.6]}), 0)
        
        result = main(mp_df=mp_df, min_total_entries=5000)
        
        mock_fetch.assert_called_once()
        mock_validate.assert_called_once()
        assert len(result) == 6000

    @patch('code.data.download_oqmd.fetch_oqmd_entries')
    def test_main_raises_if_both_insufficient(self, mock_fetch):
        """Test that main raises RuntimeError if both MP and OQMD are insufficient."""
        mp_df = pd.DataFrame({'formula': ['A'] * 1000, 'space_group': [221], 'decomposition_energy': [-0.5]})
        mock_fetch.side_effect = RuntimeError("Fetch failed")
        
        with pytest.raises(RuntimeError, match="OQMD fetch failed and MP data was insufficient"):
            main(mp_df=mp_df, min_total_entries=5000)
