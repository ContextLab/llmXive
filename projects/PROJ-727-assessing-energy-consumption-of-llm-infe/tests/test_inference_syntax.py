import pytest
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_inference_imports():
    """Verify code/inference.py imports and basic structure without loading models."""
    try:
        from code.inference import (
            load_problems_from_jsonl,
            unload_model,
            count_tokens,
            run_inference_for_model,
            write_results_to_csv,
            run_inference_per_problem,
            main
        )
        assert callable(load_problems_from_jsonl)
        assert callable(unload_model)
        assert callable(count_tokens)
        assert callable(run_inference_for_model)
        assert callable(write_results_to_csv)
        assert callable(run_inference_per_problem)
        assert callable(main)
    except ImportError as e:
        pytest.fail(f"Import error in code/inference.py: {e}")

def test_config_imports():
    """Verify config imports work."""
    from code.config import DATA_RAW_DIR, DATA_PROCESSED_DIR
    assert DATA_RAW_DIR is not None
    assert DATA_PROCESSED_DIR is not None

def test_tokenizer_logic():
    """Test count_tokens function with a mock tokenizer."""
    from code.inference import count_tokens
    # Mock tokenizer
    class MockTokenizer:
        def encode(self, text, add_special_tokens=False):
            return [1, 2, 3] # Mock 3 tokens
        def decode(self, ids, skip_special_tokens=False):
            return "mock text"

    tokenizer = MockTokenizer()
    assert count_tokens("hello world", tokenizer) == 3
    assert count_tokens("", tokenizer) == 0
    assert count_tokens(None, tokenizer) == 0