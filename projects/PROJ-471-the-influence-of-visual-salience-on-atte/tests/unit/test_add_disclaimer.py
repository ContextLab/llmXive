"""
Unit tests for T016: add_disclaimer.py

Tests verify that the disclaimer is correctly appended to the metadata JSON.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the function to test
from ingestion.add_disclaimer import process_json_file, DISCLAIMER_TEXT

class TestAddDisclaimer:
    def test_process_json_file_adds_disclaimer(self, tmp_path):
        """Test that process_json_file adds the disclaimer to an existing file."""
        # Setup
        test_file = tmp_path / "metadata.json"
        initial_data = {
            "items": [{"id": "img_001", "path": "img_001.npy"}],
            "count": 1
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
        
        # Act
        result = process_json_file(test_file)
        
        # Assert
        assert result is True
        assert test_file.exists()
        
        with open(test_file, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        
        assert "disclaimer" in updated_data
        assert updated_data["disclaimer"] == DISCLAIMER_TEXT
        assert "disclaimer_date" in updated_data
        assert "naming_convention" in updated_data
        assert updated_data["naming_convention"] == "{StimulusID}.npy"
        
        # Ensure original data is preserved
        assert "items" in updated_data
        assert len(updated_data["items"]) == 1

    def test_process_json_file_handles_corrupt_json(self, tmp_path, caplog):
        """Test that corrupt JSON returns False and logs an error."""
        test_file = tmp_path / "bad.json"
        test_file.write_text("not valid json {")
        
        result = process_json_file(test_file)
        
        assert result is False
        assert "Failed to decode JSON" in caplog.text

    def test_process_json_file_handles_missing_file(self, tmp_path, caplog):
        """Test that missing file returns False and logs an error."""
        test_file = tmp_path / "nonexistent.json"
        
        result = process_json_file(test_file)
        
        assert result is False
        assert "File not found" in caplog.text

    def test_process_json_file_preserves_structure(self, tmp_path):
        """Test that complex nested structures are preserved."""
        test_file = tmp_path / "complex.json"
        initial_data = {
            "metadata": {
                "version": "1.0",
                "source": "OpenNeuro"
            },
            "items": [
                {"id": "A", "path": "A.npy"},
                {"id": "B", "path": "B.npy"}
            ],
            "stats": {"total": 2}
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
        
        result = process_json_file(test_file)
        
        assert result is True
        
        with open(test_file, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        
        assert updated_data["metadata"]["version"] == "1.0"
        assert len(updated_data["items"]) == 2
        assert updated_data["stats"]["total"] == 2
        assert updated_data["disclaimer"] == DISCLAIMER_TEXT