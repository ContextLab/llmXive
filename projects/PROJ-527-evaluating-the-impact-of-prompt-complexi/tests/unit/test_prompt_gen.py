"""
Unit tests for prompt generation logic (User Story 1).

This module contains contract tests to verify that the prompt generation
logic produces exactly 5 complexity variants with correct labels.
"""
import pytest
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.data_models import HumanEvalProblem
from prompts.generator import generate_prompt_variants


def test_generates_5_variants():
    """
    Contract test: Verify that generate_prompt_variants produces exactly 5
    variants with the correct complexity labels.
    
    Uses a single HumanEval problem JSON as input.
    """
    # Sample HumanEval problem (minimal valid structure)
    sample_problem = {
        "problem_id": "test_problem_001",
        "prompt": "Write a function that adds two numbers.",
        "code": "def add(a, b):\n    return a + b",
        "test": "assert add(1, 2) == 3",
        "entry_point": "add"
    }
    
    # Convert to HumanEvalProblem model
    problem = HumanEvalProblem(**sample_problem)
    
    # Generate variants
    variants = generate_prompt_variants(problem)
    
    # Assert we have exactly 5 variants
    assert len(variants) == 5, f"Expected 5 variants, got {len(variants)}"
    
    # Extract labels
    labels = [v.complexity_label for v in variants]
    
    # Assert all labels are in the expected set
    expected_labels = {'simple', 'moderate', 'complex', 'very_complex', 'degenerate'}
    assert set(labels) == expected_labels, (
        f"Expected labels {expected_labels}, got {set(labels)}"
    )
    
    # Assert each variant has the correct structure
    for variant in variants:
        assert variant.problem_id == problem.problem_id
        assert variant.prompt_text is not None
        assert len(variant.prompt_text) > 0
        assert variant.complexity_label in expected_labels
        assert variant.token_count > 0
        assert variant.structural_element_count >= 0