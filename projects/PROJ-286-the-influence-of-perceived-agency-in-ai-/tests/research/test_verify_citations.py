"""
Tests for T000c: verify_citations.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add the code/research directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from research.verify_citations import verify_citations, load_json_file


class TestVerifyCitations:
    def test_all_valid(self, capsys):
        """Test that all valid citations pass verification."""
        data = {
            "citations": [
                {"citation": "Lee & See (2004)", "status": "valid", "overlap": 0.85},
                {"citation": "Langer (1975)", "status": "valid", "overlap": 0.70}
            ]
        }
        # Should not raise
        verify_citations(data)
        captured = capsys.readouterr()
        assert "Success" in captured.out

    def test_invalid_status(self, capsys):
        """Test that a citation with invalid status fails."""
        data = {
            "citations": [
                {"citation": "Fake Citation", "status": "invalid", "overlap": 0.90}
            ]
        }
        with patch("sys.exit") as mock_exit:
            verify_citations(data)
            mock_exit.assert_called_once_with(1)

    def test_low_overlap(self, capsys):
        """Test that a citation with overlap < 0.7 fails."""
        data = {
            "citations": [
                {"citation": "Lee & See (2004)", "status": "valid", "overlap": 0.69}
            ]
        }
        with patch("sys.exit") as mock_exit:
            verify_citations(data)
            mock_exit.assert_called_once_with(1)

    def test_empty_citations(self, capsys):
        """Test that empty citation list fails."""
        data = {"citations": []}
        with patch("sys.exit") as mock_exit:
            verify_citations(data)
            mock_exit.assert_called_once_with(1)

    def test_load_json_file_success(self, tmp_path):
        """Test successful JSON loading."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value"}
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        result = load_json_file(test_file)
        assert result == test_data

    def test_load_json_file_not_found(self, tmp_path):
        """Test FileNotFoundError for missing JSON."""
        non_existent = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_json_file(non_existent)
