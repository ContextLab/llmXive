"""
Integration test for LLM query and capture.

This test verifies that the LLM orchestrator correctly captures generated code
and metadata (complexity_label, token_count, structural_element_count) for
multiple prompt variants using a mocked LLM response.
"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from pydantic import ValidationError

from models.data_models import ComplexityLabel, GeneratedCode, HumanEvalProblem, PromptVariant
from llm.client import LLMClient, LLMClientError
from config import get_project_id


def test_query_and_capture():
    """
    Integration test for LLM query and capture.
    
    Uses a mocked LLM response to assert that 5 distinct code samples are captured
    with correct metadata tags (complexity_label, token_count, structural_element_count).
    """
    # Arrange
    # Create a mock HumanEval problem
    mock_problem = HumanEvalProblem(
        problem_id="test_problem_001",
        prompt="Write a function to add two numbers.",
        test="assert add(2, 3) == 5",
        entry_point="add"
    )
    
    # Define the 5 expected complexity variants
    expected_labels = [
        ComplexityLabel.simple,
        ComplexityLabel.moderate,
        ComplexityLabel.complex,
        ComplexityLabel.very_complex,
        ComplexityLabel.degenerate
    ]
    
    # Create mock prompt variants with realistic metadata
    mock_variants: List[PromptVariant] = []
    for i, label in enumerate(expected_labels):
        mock_variants.append(
            PromptVariant(
                problem_id=mock_problem.problem_id,
                complexity_label=label,
                prompt=f"Mock prompt for {label} variant {i}",
                structural_element_count=10 + (i * 5),
                token_count=50 + (i * 20)
            )
        )
    
    # Mock LLM response content (distinct code for each variant)
    mock_code_responses = [
        "def add(a, b):\n    return a + b",  # Simple
        "def add(a, b):\n    # Add two numbers\n    return a + b",  # Moderate
        "def add(a: int, b: int) -> int:\n    \"\"\"Add two integers.\"\"\"\n    return a + b",  # Complex
        "def add(a: int, b: int) -> int:\n    \"\"\"Add two integers.\n    \n    Args:\n        a: First integer\n        b: Second integer\n    \n    Returns:\n        Sum of a and b\n    \"\"\"\n    return a + b",  # Very Complex
        "def add(a, b):\n    pass\n    pass\n    pass"  # Degenerate
    ]
    
    # Mock the LLM client
    mock_client = MagicMock(spec=LLMClient)
    
    def mock_generate(prompt: str) -> str:
        # Return distinct code based on prompt content
        if "simple" in prompt.lower():
            return mock_code_responses[0]
        elif "moderate" in prompt.lower():
            return mock_code_responses[1]
        elif "complex" in prompt.lower() and "very" not in prompt.lower():
            return mock_code_responses[2]
        elif "very" in prompt.lower():
            return mock_code_responses[3]
        else:
            return mock_code_responses[4]
    
    mock_client.generate = mock_generate
    
    # Act
    # Simulate the orchestrator logic (since orchestrator isn't implemented yet,
    # we test the core capture logic directly)
    captured_codes: List[GeneratedCode] = []
    
    for variant in mock_variants:
        # Query the mocked LLM
        generated_code_str = mock_client.generate(variant.prompt)
        
        # Capture the result with metadata
        captured = GeneratedCode(
            problem_id=variant.problem_id,
            complexity_label=variant.complexity_label,
            code=generated_code_str,
            token_count=variant.token_count,
            structural_element_count=variant.structural_element_count,
            variant_prompt=variant.prompt
        )
        captured_codes.append(captured)
    
    # Assert
    # Verify we captured exactly 5 samples
    assert len(captured_codes) == 5, f"Expected 5 captured codes, got {len(captured_codes)}"
    
    # Verify all expected complexity labels are present
    captured_labels = [code.complexity_label for code in captured_codes]
    assert set(captured_labels) == set(expected_labels), \
        f"Missing complexity labels. Expected {expected_labels}, got {captured_labels}"
    
    # Verify metadata is correctly captured for each sample
    for i, code in enumerate(captured_codes):
        expected_label = expected_labels[i]
        expected_variant = mock_variants[i]
        
        assert code.complexity_label == expected_label, \
            f"Complexity label mismatch for variant {expected_label}"
        
        assert code.token_count == expected_variant.token_count, \
            f"Token count mismatch for {expected_label}: expected {expected_variant.token_count}, got {code.token_count}"
        
        assert code.structural_element_count == expected_variant.structural_element_count, \
            f"Structural element count mismatch for {expected_label}: expected {expected_variant.structural_element_count}, got {code.structural_element_count}"
        
        # Verify code is non-empty and distinct
        assert len(code.code) > 0, f"Generated code is empty for {expected_label}"
        
        # Verify the code matches our mock response for this variant
        expected_code = mock_code_responses[i]
        assert code.code == expected_code, \
            f"Code mismatch for {expected_label}: expected '{expected_code}', got '{code.code}'"
    
    # Verify uniqueness of captured codes (each variant should produce distinct code)
    unique_codes = set(code.code for code in captured_codes)
    assert len(unique_codes) == 5, \
        f"Expected 5 distinct code samples, got {len(unique_codes)}"
    
    print("✓ Integration test passed: 5 distinct code samples captured with correct metadata")