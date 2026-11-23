import os
import sys
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from inference import load_problems_from_jsonl, count_tokens, write_results_to_csv
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR

def test_load_problems_from_jsonl():
    """Test loading problems from JSONL file."""
    # Create a temporary test file
    test_file = Path(DATA_RAW_DIR) / "test_problems.jsonl"
    test_data = [
        '{"task_id": "test1", "prompt": "def add(a, b):\\n    return a + b"}',
        '{"task_id": "test2", "prompt": "def multiply(a, b):\\n    return a * b"}'
    ]
    
    test_file.parent.mkdir(parents=True, exist_ok=True)
    with open(test_file, 'w') as f:
        f.write('\n'.join(test_data))
    
    problems = load_problems_from_jsonl(str(test_file))
    
    assert len(problems) == 2
    assert problems[0]['task_id'] == 'test1'
    assert problems[1]['task_id'] == 'test2'
    
    # Cleanup
    test_file.unlink()

def test_count_tokens():
    """Test token counting function."""
    # We can't test with a real tokenizer without loading the model,
    # but we can test the function signature and basic logic
    # by mocking or using a simple tokenizer if available.
    # For now, we'll just test that the function exists and returns an integer.
    from transformers import AutoTokenizer
    
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    text = "Hello world"
    tokens = count_tokens(tokenizer, text)
    
    assert isinstance(tokens, int)
    assert tokens > 0

def test_write_results_to_csv():
    """Test writing results to CSV."""
    test_results = [
        {'model_id': 'test', 'problem_id': '1', 'tokens_generated': 10, 'energy_kwh': 0.001, 'runtime_seconds': 1.0},
        {'model_id': 'test', 'problem_id': '2', 'tokens_generated': 20, 'energy_kwh': 0.002, 'runtime_seconds': 2.0}
    ]
    
    output_file = Path(DATA_PROCESSED_DIR) / "test_results.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    write_results_to_csv(test_results, str(output_file))
    
    assert output_file.exists()
    
    # Read back and verify
    with open(output_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 3  # Header + 2 data rows
    assert 'model_id' in lines[0]
    
    # Cleanup
    output_file.unlink()

def test_inference_module_imports():
    """Test that the inference module can be imported."""
    try:
        import inference
        assert hasattr(inference, 'load_problems_from_jsonl')
        assert hasattr(inference, 'count_tokens')
        assert hasattr(inference, 'write_results_to_csv')
        assert hasattr(inference, 'main')
    except ImportError as e:
        pytest.fail(f"Failed to import inference module: {e}")
