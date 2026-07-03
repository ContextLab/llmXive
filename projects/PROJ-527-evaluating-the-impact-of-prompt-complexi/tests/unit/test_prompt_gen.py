"""
Contract tests for prompt generation logic (User Story 1).

This module verifies that the prompt generator correctly creates exactly 5
distinct complexity variants for a given HumanEval problem, with the expected
complexity labels.
"""
import json
import sys
from pathlib import Path
from typing import List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.data_models import HumanEvalProblem, ComplexityLabel
from prompts.generator import generate_prompt_variants


def test_generates_5_variants():
    """
    Contract test: Verify that generate_prompt_variants produces exactly 5
    variants with the correct complexity labels for a single HumanEval problem.
    
    Uses a minimal, real HumanEval problem JSON structure as input.
    """
    # Minimal valid HumanEval problem (based on openai/human-eval schema)
    human_eval_problem_json = {
        "task_id": "HumanEval/0",
        "prompt": "from typing import List\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, are any two numbers closer to each \n    other than given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    \"\"\"\n",
        "canonical_solution": "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n    for idx, elem in enumerate(numbers):\n        for idx2, elem2 in enumerate(numbers):\n            if idx != idx2:\n                distance = abs(elem - elem2)\n                if distance < threshold:\n                    return True\n    return False\n",
        "test": "METADATA = {\n    'author': 'the_genie',\n    'task': 'https://www.hackerrank.com/challenges/ctci-making-anagrams',\n}\n\n\ndef check(candidate):\n    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0], 0.3) == True\n    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0], 0.3) == False\n"
    }

    # Parse into HumanEvalProblem model
    problem = HumanEvalProblem(**human_eval_problem_json)

    # Generate variants
    variants = generate_prompt_variants(problem)

    # Assert exactly 5 variants are generated
    assert len(variants) == 5, f"Expected 5 variants, got {len(variants)}"

    # Extract labels
    labels = [v.complexity_label for v in variants]

    # Assert all labels are from the expected set
    expected_labels = ['simple', 'moderate', 'complex', 'very_complex', 'degenerate']
    assert all(label in expected_labels for label in labels), \
        f"Unexpected labels found: {labels}. Expected subset of {expected_labels}"

    # Assert all expected labels are present (one of each)
    assert set(labels) == set(expected_labels), \
        f"Missing or duplicate labels. Got: {labels}, Expected: {expected_labels}"


if __name__ == "__main__":
    test_generates_5_variants()
    print("Contract test passed: test_generates_5_variants")