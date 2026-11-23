"""
Unit tests for the uncertainty_flagger module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.uncertainty_flagger import (
    load_metadata,
    flag_default_uncertainty_entries,
    save_flags,
    DEFAULT_UNCERTAINTY_COVERAGE
)
from code.data_ingestion_metadata import parse_uncertainty


class TestParseUncertainty:
    """Tests for the helper function parse_uncertainty used in flagging."""

    def test_parse_explicit_10(self):
        assert parse_uncertainty("±10°C") == 10.0
        assert parse_uncertainty("10") == 10.0

    def test_parse_explicit_5(self):
        assert parse_uncertainty("±5°C") == 5.0

    def test_parse_missing(self):
        # Should return None for empty or None input
        assert parse_uncertainty("") is None
        assert parse_uncertainty(None) is None

    def test_parse_invalid(self):
        # Should return None for unparseable strings
        assert parse_uncertainty("unknown") is None
        assert parse_uncertainty("high") is None


class TestFlagDefaultUncertaintyEntries:
    """Tests for the core flagging logic."""

    def test_missing_uncertainty_flags_default(self):
        """Entry with no uncertainty should be flagged as default."""
        entries = [{"entry_id": "e1", "uncertainty_raw": None}]
        flags = flag_default_uncertainty_entries(entries)
        
        assert len(flags) == 1
        assert flags[0]["is_default_uncertainty"] is True
        assert flags[0]["uncertainty_value"] == DEFAULT_UNCERTAINTY_COVERAGE
        assert flags[0]["source"] == "missing_data_default"

    def test_explicit_default_flags_default(self):
        """Entry with explicit ±10°C should be flagged as default."""
        entries = [{"entry_id": "e2", "uncertainty_raw": "±10°C"}]
        flags = flag_default_uncertainty_entries(entries)
        
        assert len(flags) == 1
        assert flags[0]["is_default_uncertainty"] is True
        assert flags[0]["source"] == "explicit_default"

    def test_explicit_non_default_not_flagged(self):
        """Entry with ±5°C should NOT be flagged as default."""
        entries = [{"entry_id": "e3", "uncertainty_raw": "±5°C"}]
        flags = flag_default_uncertainty_entries(entries)
        
        assert len(flags) == 1
        assert flags[0]["is_default_uncertainty"] is False
        assert flags[0]["uncertainty_value"] == 5.0
        assert flags[0]["source"] == "explicit_custom"

    def test_parse_failure_flags_default(self):
        """Entry with unparseable uncertainty should fall back to default."""
        entries = [{"entry_id": "e4", "uncertainty_raw": "garbage"}]
        flags = flag_default_uncertainty_entries(entries)
        
        assert len(flags) == 1
        assert flags[0]["is_default_uncertainty"] is True
        assert flags[0]["source"] == "parse_failure_default"


class TestLoadMetadata:
    """Tests for loading metadata from JSON."""

    def test_load_list_format(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"entry_id": "x"}], f)
            f.flush()
            path = Path(f.name)
        
        try:
            data = load_metadata(path)
            assert len(data) == 1
            assert data[0]["entry_id"] == "x"
        finally:
            path.unlink()

    def test_load_dict_format(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"entries": [{"entry_id": "y"}]}, f)
            f.flush()
            path = Path(f.name)
        
        try:
            data = load_metadata(path)
            assert len(data) == 1
            assert data[0]["entry_id"] == "y"
        finally:
            path.unlink()

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_metadata(Path("/nonexistent/path.json"))


class TestSaveFlags:
    """Tests for saving flags to JSON."""

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_flags.json"
            flags = [{"entry_id": "z", "is_default_uncertainty": True}]
            
            save_flags(flags, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert len(loaded) == 1
            assert loaded[0]["entry_id"] == "z"