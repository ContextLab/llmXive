"""
Unit tests for curation logic, specifically complexity labeling and model fallback.
Tasks: T009 (Complexity Labeling), T010 (Model Fallback).

T009: Asserts that the complexity_label is in ['low', 'medium', 'high'].
T010: Asserts that model_loaded == True when CodeLlama fails and TinyLlama is used.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock, PropertyMock

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import the function we are testing.
# T013 (implementation) is now complete, so this import should succeed.
from code.curation_utils import calculate_complexity_label, label_complexity, calculate_cyclomatic_complexity


def test_complexity_labeling():
    """
    Test that the complexity label is one of the valid categories:
    'low', 'medium', or 'high'.
    
    This test verifies T009: the function must return a valid label.
    """
    test_snippets = [
        "x = 1",  # Simple: complexity 1 -> 'low'
        "if x > 0:\n    for i in range(x):\n        print(i)",  # Medium: complexity 3 (if, for) -> 'low' (<=5)
        "def complex_func(a, b):\n    if a:\n        if b:\n            return a + b\n        else:\n            return a - b\n    else:\n        return 0"  # High: multiple ifs
    ]

    for snippet in test_snippets:
        label = calculate_complexity_label(snippet)
        
        # Assert the constraint: label must be in valid set
        assert label in ['low', 'medium', 'high'], (
            f"Invalid complexity label '{label}' returned for snippet. "
            "Expected one of ['low', 'medium', 'high']."
        )
        
        # Additional check: ensure the label matches the calculated score
        score = calculate_cyclomatic_complexity(snippet)
        expected_label = label_complexity(score)
        assert label == expected_label, (
            f"Label mismatch for snippet. Score: {score}, Got: {label}, Expected: {expected_label}"
        )


def test_model_fallback():
    """
    Integration test for model loading fallback logic.
    
    Asserts that model_loaded == True when CodeLlama fails (simulated by exception)
    and TinyLlama is used as a fallback.
    
    This test verifies T010: the fallback logic must work.
    """
    # Import the function we are testing.
    # We expect this to succeed now that T014 is complete.
    from code.curation_utils import load_model_with_fallback

    # Simulate the scenario: CodeLlama fails, TinyLlama succeeds.
    # We mock torch and transformers to simulate the failure of the primary model
    # and success of the fallback.
    
    with patch('code.curation_utils.transformers') as mock_transformers, \
         patch('code.curation_utils.torch') as mock_torch, \
         patch('code.curation_utils.logging') as mock_logging:
        
        # Configure mocks
        mock_torch.cuda.is_available.return_value = False
        # Simulate low memory or just not available
        type(mock_torch.cuda).mem_get_info = PropertyMock(return_value=(0, 0))
        
        # Simulate CodeLlama loading failure on the first call
        # Return a MagicMock for the fallback (TinyLlama) on the second call
        mock_transformers.AutoModelForCausalLM.from_pretrained.side_effect = [
            Exception("MemoryError: CodeLlama failed to load"), # First call (CodeLlama)
            MagicMock() # Second call (TinyLlama) - returns a mock model
        ]
        
        mock_transformers.AutoTokenizer.from_pretrained.return_value = MagicMock()

        # Call the function
        result_model = load_model_with_fallback(
            primary_model_id="codellama/CodeLlama-7b-hf",
            fallback_model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        )
        
        # Assert that a model was successfully loaded (the fallback)
        assert result_model is not None, "Model fallback failed: result_model is None."
        
        # Verify that the function attempted to load the primary model first
        assert mock_transformers.AutoModelForCausalLM.from_pretrained.call_count == 2, (
            "Expected from_pretrained to be called twice (primary then fallback)."
        )
        
        # Verify the second call was for the fallback model
        second_call_args = mock_transformers.AutoModelForCausalLM.from_pretrained.call_args_list[1]
        assert second_call_args[0][0] == "TinyLlama/TinyLlama-1.1B-Chat-v1.0", (
            "Fallback model ID mismatch."
        )