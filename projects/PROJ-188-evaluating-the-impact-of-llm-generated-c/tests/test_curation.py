"""
Unit tests for curation logic, specifically complexity labeling and model fallback.
Tasks: T009 (Complexity Labeling), T010 (Model Fallback).

T009: Asserts that the complexity_label is in ['low', 'medium', 'high'].
T010: Asserts that model_loaded == True when CodeLlama fails and TinyLlama is used.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import the function we are testing.
# Since T013 (implementation) is not done yet, this import will fail
# or the function will not exist, causing the test to fail as required.
try:
    from code.curation_utils import calculate_complexity_label
except ImportError:
    # If the module doesn't exist yet, we define a stub that raises
    # to ensure the test fails as expected for T009.
    def calculate_complexity_label(code_snippet: str) -> str:
        raise NotImplementedError("Complexity labeling logic not implemented yet (T013).")


def test_complexity_labeling():
    """
    Test that the complexity label is one of the valid categories:
    'low', 'medium', or 'high'.
    
    This test currently fails because the implementation is not present.
    """
    test_snippets = [
        "x = 1",  # Simple
        "if x > 0:\n    for i in range(x):\n        print(i)",  # Medium
        "def complex_func(a, b):\n    if a:\n        if b:\n            return a + b\n        else:\n            return a - b\n    else:\n        return 0"  # High
    ]

    for snippet in test_snippets:
        # This call will raise NotImplementedError or fail logic checks
        # because the function is not implemented (per T009 requirement).
        label = calculate_complexity_label(snippet)
        
        # Assert the constraint: label must be in valid set
        assert label in ['low', 'medium', 'high'], (
            f"Invalid complexity label '{label}' returned for snippet. "
            "Expected one of ['low', 'medium', 'high']."
        )


def test_model_fallback():
    """
    Integration test for model loading fallback logic.
    
    Asserts that model_loaded == True when CodeLlama fails (simulated by exception)
    and TinyLlama is used as a fallback.
    
    This test currently fails because the fallback logic is not implemented in
    code.curation_utils (T014 is not done yet).
    """
    # Import the function we are testing.
    # We expect this to fail or the function to not exist yet.
    try:
        from code.curation_utils import load_model_with_fallback
    except ImportError:
        # Define a stub that raises to ensure the test fails as expected for T010.
        def load_model_with_fallback(primary_model_id: str, fallback_model_id: str):
            raise NotImplementedError(
                "Model fallback logic not implemented yet (T014). "
                "Expected to attempt loading CodeLlama and fall back to TinyLlama."
            )

    # Simulate the scenario: CodeLlama fails, TinyLlama succeeds.
    # We mock torch and transformers to simulate the failure of the primary model
    # and success of the fallback.
    
    with patch('code.curation_utils.transformers') as mock_transformers, \
         patch('code.curation_utils.torch') as mock_torch, \
         patch('code.curation_utils.logging') as mock_logging:
        
        # Configure mocks
        mock_torch.cuda.is_available.return_value = False
        mock_torch.cuda.mem_get_info.return_value = (0, 0) # Simulate low memory or just not available
        
        # Simulate CodeLlama loading failure
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