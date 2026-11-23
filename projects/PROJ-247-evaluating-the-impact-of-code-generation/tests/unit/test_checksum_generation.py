import os
import sys
import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add the code directory to the path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from code_06_checksum_generation import (
    calculate_file_checksum,
    load_existing_checksums,
    save_checksums,
    generate_checksum_for_manual_labels,
    setup_output_directories
)


class TestCalculateFileChecksum:
    def test_calculate_checksum_known_value(self, tmp_path):
        """Test checksum calculation with a known string."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_file_checksum(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_checksum_empty_file(self, tmp_path):
        """Test checksum calculation with an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = calculate_file_checksum(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_checksum_large_file(self, tmp_path):
        """Test checksum calculation with a larger file to ensure chunking works."""
        test_file = tmp_path / "large.txt"
        # Create a file larger than the 4096 byte chunk size
        content = b"X" * (4096 * 3 + 100)
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_file_checksum(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum(Path("/nonexistent/file.txt"))


class TestLoadExistingChecksums:
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading from a non-existent file returns empty dict."""
        checksum_file = tmp_path / "nonexistent.json"
        result = load_existing_checksums(checksum_file)
        assert result == {}
    
    def test_load_valid_json(self, tmp_path):
        """Test loading from a valid JSON file."""
        checksum_file = tmp_path / "checksums.json"
        data = {"file1.txt": "abc123"}
        checksum_file.write_text(json.dumps(data))
        
        result = load_existing_checksums(checksum_file)
        assert result == data
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading from an invalid JSON file returns empty dict."""
        checksum_file = tmp_path / "bad.json"
        checksum_file.write_text("not valid json")
        
        result = load_existing_checksums(checksum_file)
        assert result == {}


class TestSaveChecksums:
    def test_save_checksums(self, tmp_path):
        """Test saving checksums to a file."""
        checksum_file = tmp_path / "checksums.json"
        data = {"file1.txt": "abc123", "file2.txt": "def456"}
        
        save_checksums(data, checksum_file)
        
        assert checksum_file.exists()
        with open(checksum_file, "r") as f:
            loaded = json.load(f)
        assert loaded == data
    
    def test_save_empty_checksums(self, tmp_path):
        """Test saving an empty dictionary."""
        checksum_file = tmp_path / "checksums.json"
        
        save_checksums({}, checksum_file)
        
        assert checksum_file.exists()
        with open(checksum_file, "r") as f:
            loaded = json.load(f)
        assert loaded == {}


class TestGenerateChecksumForManualLabels:
    @pytest.fixture
    def mock_project_structure(self, tmp_path):
        """Set up a mock project structure for testing."""
        # Create necessary directories
        (tmp_path / "data" / "ground_truth").mkdir(parents=True)
        (tmp_path / "state").mkdir(parents=True)
        
        # Create a fake manual_labels.csv
        manual_labels = tmp_path / "data" / "ground_truth" / "manual_labels.csv"
        manual_labels.write_text("id,label\n1,LLM\n2,Human\n")
        
        return tmp_path

    def test_generate_checksum_updates_state(self, mock_project_structure, monkeypatch):
        """Test that the function updates the state/checksums.json file."""
        # Patch PROJECT_ROOT
        monkeypatch.setattr(
            "code_06_checksum_generation.PROJECT_ROOT", 
            mock_project_structure
        )
        
        state_dir = mock_project_structure / "state"
        checksum_file = state_dir / "checksums.json"
        manual_labels_path = mock_project_structure / "data" / "ground_truth" / "manual_labels.csv"
        
        # Calculate expected checksum
        content = manual_labels_path.read_bytes()
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Run the function
        result = generate_checksum_for_manual_labels(state_dir)
        
        # Verify the result
        assert "manual_labels.csv" in result
        assert result["manual_labels.csv"]["sha256"] == expected_hash
        assert "updated_at" in result["manual_labels.csv"]
        assert "file_path" in result["manual_labels.csv"]
        
        # Verify the file was written
        assert checksum_file.exists()
        with open(checksum_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data["manual_labels.csv"]["sha256"] == expected_hash
    
    def test_generate_checksum_missing_file(self, mock_project_structure, monkeypatch):
        """Test that FileNotFoundError is raised if manual_labels.csv is missing."""
        # Remove the file
        (mock_project_structure / "data" / "ground_truth" / "manual_labels.csv").unlink()
        
        monkeypatch.setattr(
            "code_06_checksum_generation.PROJECT_ROOT", 
            mock_project_structure
        )
        state_dir = mock_project_structure / "state"
        
        with pytest.raises(FileNotFoundError):
            generate_checksum_for_manual_labels(state_dir)
    
    def test_generate_checksum_updates_existing_checksums(self, mock_project_structure, monkeypatch):
        """Test that existing checksums are preserved and updated."""
        monkeypatch.setattr(
            "code_06_checksum_generation.PROJECT_ROOT", 
            mock_project_structure
        )
        state_dir = mock_project_structure / "state"
        checksum_file = state_dir / "checksums.json"
        
        # Pre-populate checksums.json with another file
        initial_data = {"other_file.csv": {"sha256": "oldhash", "updated_at": "2023-01-01"}}
        checksum_file.write_text(json.dumps(initial_data))
        
        # Run the function
        result = generate_checksum_for_manual_labels(state_dir)
        
        # Verify both files are present
        assert "manual_labels.csv" in result
        assert "other_file.csv" in result
        assert result["other_file.csv"]["sha256"] == "oldhash"