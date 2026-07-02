"""
Unit tests for data_loader module.
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.data_loader import _parse_string_file, _get_organism_code

class TestStringParsing:
    def test_parse_string_file_with_threshold(self, tmp_path):
        # Create a mock STRING file
        mock_data = """#protein1	protein2	combined_score
        A	A	900
        A	B	500
        B	C	800
        C	D	700
        """
        file_path = tmp_path / "test.actions.txt"
        file_path.write_text(mock_data)
        
        df = _parse_string_file(file_path, threshold=700)
        
        assert len(df) == 3 # 900, 800, 700
        assert set(df["protein1"]) == {"A", "B", "C"}
        assert all(df["score"] >= 700)

    def test_parse_string_file_no_header(self, tmp_path):
        mock_data = """A	A	900
        A	B	500
        B	C	800
        """
        file_path = tmp_path / "test_no_header.txt"
        file_path.write_text(mock_data)
        
        df = _parse_string_file(file_path, threshold=700)
        
        assert len(df) == 2
        assert list(df.columns) == ["protein1", "protein2", "score"]

class TestOrganismCode:
    def test_known_organism(self):
        assert _get_organism_code("saccharomyces_cerevisiae") == "sce"
        assert _get_organism_code("homo_sapiens") == "hsa"
    
    def test_unknown_organism(self):
        # Should return first 3 chars or fallback
        code = _get_organism_code("unknown_organism")
        assert len(code) <= 3 or code == "unknown_organism" # Depending on implementation logic
        # Based on current code: clean_name[:3] if len >= 3 else clean_name
        assert code == "unk"

class TestFallback:
    def test_load_local_ppi_missing(self, tmp_path, monkeypatch):
        # Mock get_path to return tmp_path
        monkeypatch.setattr("code.data_loader.get_path", lambda x: str(tmp_path))
        # Ensure directory doesn't exist
        fallback_dir = Path(tmp_path) / "raw" / "string_ppi"
        
        with pytest.raises(RuntimeError, match="No local PPI files found"):
            from code.data_loader import _load_local_ppi
            _load_local_ppi("test_org")

    def test_load_local_ppi_success(self, tmp_path, monkeypatch):
        # Setup
        fallback_dir = Path(tmp_path) / "raw" / "string_ppi"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        mock_file = fallback_dir / "4932.actions.txt"
        mock_file.write_text("A\tB\t800\nC\tD\t600\n")
        
        monkeypatch.setattr("code.data_loader.get_path", lambda x: str(tmp_path))
        
        from code.data_loader import _load_local_ppi
        df = _load_local_ppi("test_org")
        
        assert len(df) == 2
        assert list(df.columns) == ["protein1", "protein2", "score"]