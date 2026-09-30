import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from reproducibility_check import (
    get_file_hash,
    load_json_safe,
    normalize_floats,
    compare_results,
    run_reproducibility_check
)

class TestFileHashing:
    """Test file hashing functionality."""
    
    def test_get_file_hash(self, tmp_path):
        """Test that hash is calculated correctly."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        hash1 = get_file_hash(test_file)
        hash2 = get_file_hash(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_different_content_different_hash(self, tmp_path):
        """Test that different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_bytes(b"Content 1")
        file2.write_bytes(b"Content 2")
        
        hash1 = get_file_hash(file1)
        hash2 = get_file_hash(file2)
        
        assert hash1 != hash2

class TestJsonLoading:
    """Test JSON loading functionality."""
    
    def test_load_json_valid(self, tmp_path):
        """Test loading valid JSON."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(test_data))
        
        loaded = load_json_safe(test_file)
        assert loaded == test_data
    
    def test_load_json_not_found(self, tmp_path):
        """Test that missing file raises error."""
        test_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_json_safe(test_file)
    
    def test_load_json_invalid(self, tmp_path):
        """Test that invalid JSON raises error."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{invalid json}")
        
        with pytest.raises(json.JSONDecodeError):
            load_json_safe(test_file)

class TestFloatNormalization:
    """Test float normalization for comparison."""
    
    def test_round_float(self):
        """Test that floats are rounded correctly."""
        data = {"value": 3.141592653589793}
        normalized = normalize_floats(data)
        
        assert normalized["value"] == 3.1415926536  # Rounded to 10 decimals
    
    def test_nested_floats(self):
        """Test normalization of nested structures."""
        data = {
            "level1": {
                "level2": [1.123456789012345, 2.987654321098765]
            }
        }
        normalized = normalize_floats(data)
        
        assert normalized["level1"]["level2"][0] == 1.123456789
        assert normalized["level1"]["level2"][1] == 2.987654321
    
    def test_mixed_types(self):
        """Test normalization with mixed data types."""
        data = {
            "string": "test",
            "int": 42,
            "float": 3.141592653589793,
            "list": [1, 2.5, "three"]
        }
        normalized = normalize_floats(data)
        
        assert normalized["string"] == "test"
        assert normalized["int"] == 42
        assert normalized["float"] == 3.1415926536
        assert normalized["list"] == [1, 2.5, "three"]

class TestResultComparison:
    """Test result comparison functionality."""
    
    def test_identical_results(self):
        """Test that identical results compare as equal."""
        data = {"value": 3.141592653589793, "list": [1, 2, 3]}
        
        assert compare_results(data, data) is True
    
    def test_float_tolerance(self):
        """Test that floats within tolerance compare as equal."""
        data1 = {"value": 3.141592653589793}
        data2 = {"value": 3.141592653589794}  # Tiny difference
        
        assert compare_results(data1, data2) is True
    
    def test_different_results(self):
        """Test that significantly different results compare as unequal."""
        data1 = {"value": 1.0}
        data2 = {"value": 2.0}
        
        assert compare_results(data1, data2) is False
    
    def test_nested_structures(self):
        """Test comparison of nested structures."""
        data1 = {
            "level1": {
                "level2": [1.1, 2.2, 3.3]
            }
        }
        data2 = {
            "level1": {
                "level2": [1.1, 2.2, 3.3]
            }
        }
        
        assert compare_results(data1, data2) is True

class TestReproducibilityCheck:
    """Test the main reproducibility check function."""
    
    @patch('reproducibility_check.verify_and_apply_seed')
    @patch('reproducibility_check.load_json_safe')
    @patch('reproducibility_check.Path.exists')
    def test_check_with_existing_files(
        self, 
        mock_exists, 
        mock_load_json, 
        mock_apply_seed,
        tmp_path
    ):
        """Test check when files exist."""
        # Setup mocks
        mock_exists.return_value = True
        mock_load_json.return_value = {"test": 3.141592653589793}
        
        # Create mock file paths
        with patch('reproducibility_check.Path') as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_class.return_value = mock_path
            
            results = run_reproducibility_check(seed=42)
            
            assert results['seed'] == 42
            assert len(results['files_checked']) > 0
            assert 'all_passed' in results
    
    @patch('reproducibility_check.verify_and_apply_seed')
    @patch('reproducibility_check.Path.exists')
    def test_check_with_missing_files(
        self, 
        mock_exists, 
        mock_apply_seed,
        tmp_path
    ):
        """Test check when files are missing."""
        # Setup mocks
        mock_exists.return_value = False
        
        with patch('reproducibility_check.Path') as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path_class.return_value = mock_path
            
            results = run_reproducibility_check(seed=42)
            
            assert results['all_passed'] is False
            assert any(not r['exists'] for r in results['details'].values())

if __name__ == "__main__":
    pytest.main([__file__, "-v"])