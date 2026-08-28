"""
Integration tests for User Story 2: Docstring Generation.

Tests the full generation pipeline with mocked model and data.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
import sys
sys.path.insert(0, 'code')
from generate import (
    load_method_data, 
    generate_docstring_batch, 
    save_results, 
    main,
    GenerationException
)
from utils.monitor import MemoryLimitException

@pytest.fixture
def sample_methods():
    """Create sample method data for testing."""
    return [
        {
            'repo_url': 'https://github.com/test/repo1',
            'file_path': 'test.py',
            'method_name': 'add_numbers',
            'signature': 'def add_numbers(a: int, b: int) -> int:',
            'human_docstring': 'Adds two numbers together.'
        },
        {
            'repo_url': 'https://github.com/test/repo2',
            'file_path': 'utils.py',
            'method_name': 'calculate_total',
            'signature': 'def calculate_total(items: list) -> float:',
            'human_docstring': None
        }
    ]

@pytest.fixture
def temp_input_dir(sample_methods):
    """Create a temporary directory with sample JSON data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir)
        data_file = input_dir / "repo1.json"
        with open(data_file, 'w') as f:
            json.dump(sample_methods, f)
        yield input_dir

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_method_data(temp_input_dir, sample_methods):
    """Test loading method data from JSON files."""
    loaded_methods = load_method_data(temp_input_dir)
    
    assert len(loaded_methods) == len(sample_methods)
    assert loaded_methods[0]['method_name'] == 'add_numbers'
    assert loaded_methods[1]['human_docstring'] is None

def test_load_method_data_no_files():
    """Test error handling when no JSON files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir)
        with pytest.raises(FileNotFoundError):
            load_method_data(input_dir)

def test_generate_docstring_batch(sample_methods):
    """Test docstring generation with mocked model."""
    # Mock model and tokenizer
    mock_model = MagicMock()
    mock_model.device = 'cpu'
    
    mock_tokenizer = MagicMock()
    mock_tokenizer.eos_token_id = 50256
    mock_tokenizer.return_value = MagicMock()
    mock_tokenizer.return_value.to.return_value = {'input_ids': torch.tensor([[1, 2, 3]])}
    mock_tokenizer.decode.return_value = "This is a generated docstring."
    
    # Mock model.generate to return dummy output
    mock_output = MagicMock()
    mock_output.__getitem__.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    mock_model.generate.return_value = mock_output
    
    import torch
    with patch('generate.torch', torch):
        results = generate_docstring_batch(mock_model, mock_tokenizer, sample_methods, batch_size=2)
    
    assert len(results) == len(sample_methods)
    assert results[0]['generated_docstring'] == "This is a generated docstring."
    assert results[0]['generation_status'] == 'success'

def test_save_results(temp_output_dir, sample_methods):
    """Test saving results to JSON file."""
    results = [
        {
            'repo_url': 'test',
            'file_path': 'test.py',
            'method_name': 'test',
            'signature': 'def test():',
            'human_docstring': None,
            'generated_docstring': 'Test docstring',
            'generation_status': 'success'
        }
    ]
    
    output_path = temp_output_dir / "results.json"
    save_results(results, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert len(saved_data) == 1
    assert saved_data[0]['generated_docstring'] == 'Test docstring'

def test_main_integration(temp_input_dir, temp_output_dir, sample_methods):
    """Integration test for the main generation pipeline."""
    # Mock dependencies
    with patch('generate.get_config') as mock_config, \
         patch('generate.load_model') as mock_load_model, \
         patch('generate.get_memory_usage_mb', return_value=1000), \
         patch('generate.setup_logger'):
        
        # Setup mocks
        mock_config.return_value.model_name = "test-model"
        
        mock_model = MagicMock()
        mock_model.device = 'cpu'
        mock_tokenizer = MagicMock()
        mock_tokenizer.eos_token_id = 50256
        mock_load_model.return_value = (mock_model, mock_tokenizer)
        
        # Mock model.generate
        import torch
        mock_output = MagicMock()
        mock_output.__getitem__.return_value = torch.tensor([[1, 2, 3, 4, 5]])
        mock_model.generate.return_value = mock_output
        
        # Mock tokenizer
        mock_tokenizer.return_value.to.return_value = {'input_ids': torch.tensor([[1, 2, 3]])}
        mock_tokenizer.decode.return_value = "Generated docstring."
        
        # Run main with modified paths
        original_main = main
        
        def custom_main():
            import generate
            generate.input_dir = temp_input_dir
            generate.output_path = temp_output_dir / "results.json"
            original_main()
        
        try:
            custom_main()
        except SystemExit:
            pass  # Expected after successful completion
        
        # Check output file
        output_file = temp_output_dir / "results.json"
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        assert len(results) == len(sample_methods)
        assert all(r['generation_status'] in ['success', 'error'] for r in results)

def test_memory_limit_exceeded(sample_methods):
    """Test that generation aborts when memory limit is exceeded."""
    mock_model = MagicMock()
    mock_model.device = 'cpu'
    mock_tokenizer = MagicMock()
    
    with patch('generate.get_memory_usage_mb', return_value=8000):  # Above 7GB limit
        with pytest.raises(MemoryLimitException):
            generate_docstring_batch(mock_model, mock_tokenizer, sample_methods)