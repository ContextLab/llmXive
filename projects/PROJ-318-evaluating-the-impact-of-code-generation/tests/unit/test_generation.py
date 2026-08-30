"""Unit tests for docstring generation functionality."""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, 'code')

from generate import load_method_data, generate_docstring_batch, save_results, GenerationException
from utils.monitor import MemoryLimitException

class TestLoadMethodData:
    """Tests for load_method_data function."""
    
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file with method data."""
        data = [
            {"signature": "test_func(x, y)", "ast_params": ["x", "y"]},
            {"signature": "another_func(a)", "ast_params": ["a"]}
        ]
        json_file = tmp_path / "test.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)
            
        result = load_method_data(json_file)
        assert len(result) == 2
        assert result[0]["signature"] == "test_func(x, y)"
        assert result[0]["ast_params"] == ["x", "y"]
        
    def test_load_empty_list(self, tmp_path):
        """Test loading an empty JSON list."""
        json_file = tmp_path / "empty.json"
        with open(json_file, 'w') as f:
            json.dump([], f)
            
        result = load_method_data(json_file)
        assert result == []
        
    def test_load_not_a_list(self, tmp_path):
        """Test loading a JSON file that is not a list."""
        json_file = tmp_path / "invalid.json"
        with open(json_file, 'w') as f:
            json.dump({"key": "value"}, f)
            
        with pytest.raises(GenerationException, match="Expected list"):
            load_method_data(json_file)
            
    def test_load_file_not_found(self):
        """Test loading a non-existent file."""
        with pytest.raises(GenerationException, match="File not found"):
            load_method_data(Path("nonexistent.json"))
            
    def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON."""
        json_file = tmp_path / "bad.json"
        with open(json_file, 'w') as f:
            f.write("not valid json")
            
        with pytest.raises(GenerationException, match="JSON decode error"):
            load_method_data(json_file)

class TestGenerateDocstringBatch:
    """Tests for generate_docstring_batch function."""
    
    @patch('generate.check_memory_limit')
    def test_generate_success(self, mock_check_mem):
        """Test successful docstring generation."""
        # Mock model and tokenizer
        mock_model = Mock()
        mock_model.device = "cpu"
        
        mock_tokenizer = Mock()
        mock_tokenizer.eos_token_id = 50256
        
        # Mock the generate method to return specific tokens
        mock_output = Mock()
        mock_output.__getitem__ = lambda self, idx: [101, 102, 103]  # Simulated token IDs
        mock_model.generate.return_value = mock_output
        
        # Mock tokenizer.decode
        mock_tokenizer.decode.return_value = "def test_func(x, y):\n    \"\"\"Generated docstring.\"\"\""
        
        methods = [
            {"signature": "test_func(x, y)", "ast_params": ["x", "y"]}
        ]
        
        result = generate_docstring_batch(methods, mock_model, mock_tokenizer, temperature=0.1)
        
        assert len(result) == 1
        assert result[0]["generated_docstring"] is not None
        assert "ast_params" in result[0]  # Preserved
        assert result[0]["generation_status"] == "success"
        
    def test_generate_empty_signature(self):
        """Test handling of empty signature."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        methods = [
            {"signature": "", "ast_params": []},
            {"signature": "valid_func()", "ast_params": []}
        ]
        
        # Mock model.generate to avoid actual generation
        mock_model.device = "cpu"
        mock_tokenizer.eos_token_id = 50256
        mock_output = Mock()
        mock_output.__getitem__ = lambda self, idx: [101]
        mock_model.generate.return_value = mock_output
        mock_tokenizer.decode.return_value = "def valid_func():\n    pass"
        
        result = generate_docstring_batch(methods, mock_model, mock_tokenizer)
        
        assert len(result) == 2
        assert result[0]["generation_status"] == "skipped_empty_signature"
        assert result[1]["generation_status"] == "success"
        
    @patch('generate.check_memory_limit')
    def test_generate_memory_limit_exceeded(self, mock_check_mem):
        """Test that memory limit exception is raised."""
        mock_check_mem.side_effect = MemoryLimitException("RAM limit exceeded")
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        methods = [{"signature": "test()", "ast_params": []}]
        
        with pytest.raises(MemoryLimitException):
            generate_docstring_batch(methods, mock_model, mock_tokenizer)

class TestSaveResults:
    """Tests for save_results function."""
    
    def test_save_results(self, tmp_path):
        """Test saving results to JSON."""
        results = [
            {"signature": "test()", "generated_docstring": "A test function"},
            {"signature": "another()", "generated_docstring": None}
        ]
        output_file = tmp_path / "results.json"
        
        save_results(results, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
            
        assert len(saved_data) == 2
        assert saved_data[0]["signature"] == "test()"
        
    def test_save_creates_directories(self, tmp_path):
        """Test that save_results creates parent directories."""
        results = [{"signature": "test()", "generated_docstring": "test"}]
        output_file = tmp_path / "subdir" / "results.json"
        
        save_results(results, output_file)
        
        assert output_file.exists()
