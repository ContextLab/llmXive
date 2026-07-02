"""
Prompt generation logic for creating complexity variants.

This module implements the generation of multiple prompt variants based on
structural composition: problem only, +1 example, +constraints, +multi-step,
+redundant.
"""
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.data_models import HumanEvalProblem, PromptVariant, ComplexityLabel
from prompts.parser import count_structural_elements
from prompts.tokenizer import count_tokens


def generate_prompt_variants(problem: HumanEvalProblem) -> List[PromptVariant]:
    """
    Generate 5 complexity variants for a given HumanEval problem.
    
    Variants:
    1. simple: Problem description only
    2. moderate: Problem + 1 example
    3. complex: Problem + example + constraints
    4. very_complex: Problem + example + constraints + multi-step instructions
    5. degenerate: Problem + excessive redundant instructions (intentionally bloated)
    
    Args:
        problem: HumanEvalProblem instance containing the base problem data
        
    Returns:
        List of 5 PromptVariant instances with different complexity levels
    """
    base_prompt = problem.prompt
    code_snippet = problem.code
    test_snippet = problem.test
    
    variants = []
    
    # 1. Simple: Problem only
    simple_prompt = f"Implement the following:\n\n{base_prompt}\n\nProvide only the function implementation."
    variants.append(_create_variant(
        problem, simple_prompt, "simple"
    ))
    
    # 2. Moderate: Problem + 1 example
    moderate_prompt = f"""Implement the following:

{base_prompt}

Example:
{code_snippet}
assert {test_snippet}

Provide the function implementation following the example pattern."""
    variants.append(_create_variant(
        problem, moderate_prompt, "moderate"
    ))
    
    # 3. Complex: Problem + example + constraints
    complex_prompt = f"""Implement the following:

{base_prompt}

Example:
{code_snippet}
assert {test_snippet}

Constraints:
- Use only standard library functions
- Ensure O(n) time complexity where applicable
- Handle edge cases (empty input, None values)
- Include type hints

Provide a complete, production-ready implementation."""
    variants.append(_create_variant(
        problem, complex_prompt, "complex"
    ))
    
    # 4. Very Complex: Problem + example + constraints + multi-step
    very_complex_prompt = f"""Task: Implement the following function.

Problem Description:
{base_prompt}

Reference Implementation:
{code_snippet}

Test Case:
assert {test_snippet}

Detailed Requirements:
1. Function Signature:
   - Use proper type hints for all parameters and return values
   - Follow PEP 8 naming conventions
   
2. Implementation Constraints:
   - Time complexity: O(n) or better
   - Space complexity: O(1) where possible
   - No external dependencies (standard library only)
   
3. Edge Case Handling:
   - Empty inputs
   - None values
   - Negative numbers
   - Large inputs (performance consideration)
   
4. Documentation:
   - Include docstring with description, parameters, and return value
   - Add inline comments for complex logic
   
5. Testing:
   - Ensure the implementation passes the provided test case
   - Consider additional test cases for robustness

Step-by-step approach:
1. Analyze the problem requirements
2. Design the function signature
3. Implement the core logic
4. Add error handling
5. Include documentation
6. Verify against test cases

Provide the complete implementation."""
    variants.append(_create_variant(
        problem, very_complex_prompt, "very_complex"
    ))
    
    # 5. Degenerate: Problem + excessive redundant instructions
    degenerate_prompt = f"""
    TASK: IMPLEMENT THE FOLLOWING FUNCTION.
    
    IMPORTANT: READ THIS CAREFULLY BEFORE BEGINNING.
    
    Problem Description (repeated for clarity):
    {base_prompt}
    
    Problem Description (again, to ensure understanding):
    {base_prompt}
    
    Reference Implementation (provided for your reference):
    {code_snippet}
    
    Reference Implementation (repeated for emphasis):
    {code_snippet}
    
    Test Case (to verify correctness):
    assert {test_snippet}
    
    Test Case (repeated for verification):
    assert {test_snippet}
    
    CRITICAL INSTRUCTIONS:
    1. You must implement the function.
    2. You must implement the function correctly.
    3. You must ensure the function passes the test.
    4. You must use proper coding practices.
    5. You must follow best practices.
    6. You must include type hints.
    7. You must include docstrings.
    8. You must handle edge cases.
    9. You must optimize for performance.
    10. You must ensure code quality.
    
    REMINDER: Implement the function: {base_prompt}
    REMINDER: Use the example: {code_snippet}
    REMINDER: Pass the test: assert {test_snippet}
    
    ADDITIONAL CONTEXT (redundant but required):
    - The function should be efficient.
    - The function should be readable.
    - The function should be maintainable.
    - The function should be testable.
    - The function should be documented.
    - The function should be optimized.
    - The function should be robust.
    - The function should be correct.
    - The function should be complete.
    - The function should be professional.
    
    FINAL INSTRUCTION: Implement the function: {base_prompt}
    """
    variants.append(_create_variant(
        problem, degenerate_prompt, "degenerate"
    ))
    
    return variants


def _create_variant(problem: HumanEvalProblem, prompt_text: str, label: str) -> PromptVariant:
    """
    Create a PromptVariant instance with computed metrics.
    
    Args:
        problem: The source HumanEvalProblem
        prompt_text: The generated prompt text
        label: The complexity label (simple, moderate, etc.)
        
    Returns:
        PromptVariant instance with all required fields
    """
    token_count = count_tokens(prompt_text)
    structural_count = count_structural_elements(prompt_text)
    
    return PromptVariant(
        problem_id=problem.problem_id,
        prompt_text=prompt_text,
        complexity_label=ComplexityLabel(label),
        token_count=token_count,
        structural_element_count=structural_count
    )