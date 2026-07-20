"""
Tests for the inference module.
"""
import os
import sys
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.inference import (
    load_problems_from_jsonl,
    count_tokens,
    write_results_to_csv,
    run_inference_for_model
)
from code.config import get_model_hf_id

def test_load_problems_from_jsonl():
    """Test loading problems from JSONL file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"task_id": "test1", "prompt": "def hello(): pass"}\n')
        f.write('{"task_id": "test2", "prompt": "def world(): pass"}\n')
        temp_path = f.name

    try:
        problems = load_problems_from_jsonl(temp_path)
        assert len(problems) == 2
        assert problems[0]['task_id'] == 'test1'
        assert problems[1]['task_id'] == 'test2'
    finally:
        os.unlink(temp_path)

def test_count_tokens():
    """Test token counting with a mock tokenizer."""
    # Create a simple mock tokenizer
    class MockTokenizer:
        def encode(self, text, add_special_tokens=False):
            # Simple space-based tokenization for testing
            return text.split()

    tokenizer = MockTokenizer()
    
    assert count_tokens("hello world", tokenizer) == 2
    assert count_tokens("", tokenizer) == 0
    assert count_tokens("one", tokenizer) == 1

def test_write_results_to_csv():
    """Test writing results to CSV."""
    results = [
        {
            'model_id': 'test-model',
            'problem_id': 'p1',
            'tokens_generated': 10,
            'energy_kwh': 0.001,
            'runtime_seconds': 1.5
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name

    try:
        write_results_to_csv(results, temp_path)
        
        with open(temp_path, 'r') as f:
            content = f.read()
            assert 'model_id' in content
            assert 'test-model' in content
            assert 'p1' in content
            assert '10' in content
            assert '0.001' in content
            assert '1.5' in content
    finally:
        os.unlink(temp_path)

@patch('code.inference.AutoTokenizer.from_pretrained')
@patch('code.inference.AutoModelForCausalLM.from_pretrained')
@patch('code.inference.EmissionsTracker')
@patch('code.inference.torch.manual_seed')
def test_run_inference_for_model_structure(
    mock_seed,
    mock_tracker,
    mock_model_load,
    mock_tokenizer_load
):
    """
    Test the structure of run_inference_for_model without actually loading models.
    This verifies the function logic and output structure.
    """
    # Setup mocks
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = None
    mock_tokenizer.eos_token = ""
    mock_tokenizer.encode.return_value = [1, 2, 3]
    mock_tokenizer.decode.return_value = "test generation"
    mock_tokenizer_load.return_value = mock_tokenizer

    mock_model = MagicMock()
    mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    mock_model_load.return_value = mock_model

    # Mock tracker
    mock_tracker_instance = MagicMock()
    mock_tracker_instance.finalize.return_value = 0.0005
    mock_tracker.return_value.__enter__ = MagicMock(return_value=mock_tracker_instance)
    mock_tracker.return_value.__exit__ = MagicMock(return_value=None)

    # Create test problems
    problems = [
        {'task_id': 'p1', 'prompt': 'def test(): pass'}
    ]

    # Run inference
    results = run_inference_for_model('test-model', problems)

    # Verify results structure
    assert len(results) == 1
    result = results[0]
    assert result['model_id'] == 'test-model'
    assert result['problem_id'] == 'p1'
    assert 'tokens_generated' in result
    assert 'energy_kwh' in result
    assert 'runtime_seconds' in result
    
    # Verify values are populated (not None)
    assert result['tokens_generated'] is not None
    assert result['energy_kwh'] is not None
    assert result['runtime_seconds'] is not None

def test_model_ids_from_config():
    """Verify that model IDs are correctly defined in config."""
    from code.config import MODEL_IDS
    assert 'gpt2-small' in MODEL_IDS
    assert 'codebert' in MODEL_IDS
    assert 'starcoder-1b' in MODEL_IDS

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
