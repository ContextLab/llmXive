import json
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from datasets import Dataset

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import fetch_taxonomy, verify_checksum, _compute_file_hash
from config import get_path

class TestFetchTaxonomy:
    """Tests for the fetch_taxonomy function."""
    
    def test_fetch_taxonomy_creates_file(self, tmp_path):
        """Test that fetch_taxonomy creates the taxonomy file."""
        # Mock the load_dataset function to return a simple dataset
        mock_data = [
            {
                "category": "test_category",
                "subcategories": ["sub1", "sub2"],
                "description": "Test description",
                "examples": ["example1", "example2"],
                "metadata": {"source": "test"}
            }
        ]
        
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_data))
            
            output_path = tmp_path / "taxonomy.json"
            result_path = fetch_taxonomy(output_path)
            
            # Verify file was created
            assert result_path.exists()
            assert result_path == output_path
            
            # Verify content
            with open(result_path, 'r') as f:
                content = json.load(f)
            
            assert len(content) == 1
            assert content[0]["category"] == "test_category"
    
    def test_fetch_taxonomy_fails_loudly_on_error(self):
        """Test that fetch_taxonomy raises an error when dataset fetch fails."""
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Network error")
            
            with pytest.raises(RuntimeError, match="Failed to fetch AgentDoG taxonomy"):
                fetch_taxonomy()
    
    def test_fetch_taxonomy_uses_default_path(self):
        """Test that fetch_taxonomy uses the default path when not specified."""
        mock_data = [
            {
                "category": "default_test",
                "subcategories": [],
                "description": "Test",
                "examples": [],
                "metadata": {}
            }
        ]
        
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_data))
            
            # This should use the default path from config
            result_path = fetch_taxonomy()
            
            # Verify the path matches the default
            expected_path = get_path("data/raw/taxonomy.json")
            assert result_path == expected_path

class TestChecksumVerification:
    """Tests for checksum verification functions."""
    
    def test_compute_file_hash(self, tmp_path):
        """Test that file hash computation works correctly."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        hash1 = _compute_file_hash(test_file)
        hash2 = _compute_file_hash(test_file)
        
        # Same file should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex characters
    
    def test_verify_checksum_success(self, tmp_path):
        """Test successful checksum verification."""
        test_file = tmp_path / "test.txt"
        test_content = "Test content"
        test_file.write_text(test_content)
        
        actual_hash = _compute_file_hash(test_file)
        
        assert verify_checksum(test_file, actual_hash) is True
    
    def test_verify_checksum_failure(self, tmp_path):
        """Test failed checksum verification."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        wrong_hash = "0" * 64
        
        assert verify_checksum(test_file, wrong_hash) is False
    
    def test_verify_checksum_file_not_found(self, tmp_path):
        """Test that verify_checksum raises error for missing file."""
        non_existent = tmp_path / "non_existent.txt"
        
        with pytest.raises(FileNotFoundError):
            verify_checksum(non_existent, "some_hash")