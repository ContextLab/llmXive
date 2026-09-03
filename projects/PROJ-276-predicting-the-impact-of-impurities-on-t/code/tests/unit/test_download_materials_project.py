"""
Unit tests for download_materials_project.py

Tests focus on logic verification without hitting the real API.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.ingestion.download_materials_project import (
    _get_api_key,
    _fetch_mgb2_entries,
    _filter_relevant_entries,
    main,
    API_KEY_ENV
)


class TestGetApiKey:
    def test_api_key_present(self, monkeypatch):
        """Test retrieval of existing API key."""
        test_key = "test_key_123"
        monkeypatch.setenv(API_KEY_ENV, test_key)
        assert _get_api_key() == test_key

    def test_api_key_missing(self, monkeypatch):
        """Test error when API key is missing."""
        monkeypatch.delenv(API_KEY_ENV, raising=False)
        with pytest.raises(ValueError, match="Missing API key"):
            _get_api_key()


class TestFilterRelevantEntries:
    def test_filters_mgb2_correctly(self):
        """Test that MgB2 entries are kept and others filtered."""
        entries = [
            {"formula": "MgB2"},
            {"formula": "MgB4"},
            {"formula": "MgO"},
            {"formula": "MgB2:impurity"},
            {"formula": "B2Mg"}  # Should be caught by 'mg' and 'b' check
        ]
        # Note: Current logic checks 'mgb2' in formula or starts with mg and has b
        # MgB4 starts with mg and has b, so it is kept.
        # MgO starts with mg but no b, so it is filtered.
        result = _filter_relevant_entries(entries)
        
        # Expected: MgB2, MgB4, MgB2:impurity, B2Mg (if 'mg' in 'b2mg' check was different, but logic is starts with mg)
        # Let's trace: 
        # MgB2 -> 'mgb2' in 'mgb2' -> True
        # MgB4 -> 'mgb2' in 'mgb4' False. starts with 'mg' True. 'b' in 'mgb4' True. -> True
        # MgO -> 'mgb2' in 'mgo' False. starts with 'mg' True. 'b' in 'mgo' False. -> False
        # MgB2:impurity -> 'mgb2' in ... True
        # B2Mg -> 'mgb2' in ... False. starts with 'mg' False. -> False
        
        assert len(result) == 3
        assert result[0]["formula"] == "MgB2"
        assert result[1]["formula"] == "MgB4"
        assert result[2]["formula"] == "MgB2:impurity"

    def test_empty_list(self):
        """Test handling of empty input."""
        assert _filter_relevant_entries([]) == []

    def test_fallback_to_all_if_no_mgb2(self):
        """Test that if no MgB2 is found, original list is returned."""
        entries = [{"formula": "MgO"}, {"formula": "MgCl2"}]
        # Logic: if 'mgb2' in formula or (starts with mg and has b)
        # MgO: starts mg, no b -> False
        # MgCl2: starts mg, no b -> False
        # Filtered list is empty -> returns original
        result = _filter_relevant_entries(entries)
        assert len(result) == 2


class TestMain:
    @patch("src.ingestion.download_materials_project._get_api_key")
    @patch("src.ingestion.download_materials_project._fetch_mgb2_entries")
    @patch("src.ingestion.download_materials_project._filter_relevant_entries")
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.ingestion.download_materials_project.OUTPUT_PATH")
    def test_success_flow(self, mock_path, mock_open_file, mock_filter, mock_fetch, mock_get_key, tmp_path):
        """Test successful execution flow."""
        # Setup mocks
        mock_get_key.return_value = "fake_key"
        mock_fetch.return_value = [{"material_id": "mp-123", "formula": "MgB2"}]
        mock_filter.return_value = [{"material_id": "mp-123", "formula": "MgB2"}]
        
        # Mock path to use temp dir
        temp_file = tmp_path / "test_output.json"
        mock_path.__truediv__.return_value = temp_file
        mock_path.__rtruediv__.return_value = temp_file
        mock_path.parent = temp_file.parent
        mock_path.__fspath__ = lambda self: str(temp_file)

        # Run
        result = main()

        # Assertions
        assert result == 0
        mock_open_file.assert_called_once()
        # Verify JSON was written
        handle = mock_open_file()
        written_content = "".join(call[0][0] for call in handle.write.call_args_list)
        data = json.loads(written_content)
        assert data["count"] == 1
        assert data["data"][0]["formula"] == "MgB2"

    @patch("src.ingestion.download_materials_project._get_api_key")
    @patch("src.ingestion.download_materials_project._fetch_mgb2_entries")
    def test_empty_data_returns_error(self, mock_fetch, mock_get_key):
        """Test that empty results return exit code 1."""
        mock_get_key.return_value = "fake_key"
        mock_fetch.return_value = [] # Simulate empty fetch
        
        # Note: _filter_relevant_entries logic returns original if empty filter result,
        # but _fetch_mgb2_entries raises ValueError if empty. 
        # Let's simulate the case where fetch returns empty and the function handles it.
        # Actually, _fetch_mgb2_entries raises ValueError if data is empty.
        # So we need to mock the internal logic to return empty list that passes to filter
        # or mock fetch to return empty list which triggers ValueError inside fetch?
        # In the code: if not results: raise ValueError.
        # So we must mock the response parsing to return empty list but bypass the check?
        # No, we test the logic. If fetch returns empty, it raises.
        # Let's test the filter returning empty and main handling it.
        
        # Actually, looking at code: 
        # raw = fetch() -> raises if empty
        # relevant = filter(raw) -> if empty returns raw (which is empty)
        # if not relevant: return 1
        
        # So if fetch returns empty, it raises ValueError.
        # Let's test the case where fetch returns data but filter removes everything and returns empty?
        # No, filter returns original if empty.
        # So the only way to get 1 is if fetch raises (handled) or if relevant is empty (impossible with current filter logic unless fetch returns empty and we didn't raise? No, fetch raises).
        
        # Wait, if fetch returns empty, it raises ValueError.
        # If fetch returns non-empty, filter returns non-empty (at least the original).
        # So main() should always return 0 if fetch succeeds?
        # Unless the filter logic changes.
        # Let's assume the code logic: if not relevant: return 1.
        # To trigger this, we need _filter_relevant_entries to return empty list.
        # But current implementation returns `entries` if `filtered` is empty.
        # So to test the "no valid entries" path, we need to mock _filter_relevant_entries to return [].
        
        mock_fetch.return_value = [{"formula": "MgO"}]
        mock_filter.return_value = [] # Force empty result from filter logic (simulating a stricter filter)

        # We also need to mock the file write to avoid errors
        with patch("builtins.open", new_callable=mock_open):
            with patch("src.ingestion.download_materials_project.OUTPUT_PATH.parent") as mock_parent:
                mock_parent.mkdir.return_value = None
                result = main()
                assert result == 1