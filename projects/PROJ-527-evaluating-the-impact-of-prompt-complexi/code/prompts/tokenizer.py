"""
Token counting and threshold validation for prompt variants.

Uses tiktoken's cl100k_base encoder (GPT-4o, GPT-4, etc.) to count tokens
and validate against complexity-specific thresholds.
"""
from __future__ import annotations

import tiktoken
from typing import Dict, List, Tuple, Optional
from models.data_models import PromptVariant, ComplexityLabel
from config import Paths

# Thresholds (inclusive lower bound, exclusive upper bound where applicable)
# simple: <= 50
# moderate: 51-150
# complex: 151-300
# very_complex: 301-500
# degenerate: > 500 (or specific redundant pattern)
THRESHOLDS: Dict[ComplexityLabel, Tuple[int, Optional[int]]] = {
    "simple": (0, 50),
    "moderate": (51, 150),
    "complex": (151, 300),
    "very_complex": (301, 500),
    "degenerate": (501, None),  # No upper bound
}

ENCODER_NAME = "cl100k_base"

def get_token_count(text: str) -> int:
    """
    Count tokens in a string using the cl100k_base encoder.

    Args:
        text: The prompt text to tokenize.

    Returns:
        The number of tokens in the text.
    """
    try:
        encoder = tiktoken.get_encoding(ENCODER_NAME)
        return len(encoder.encode(text))
    except Exception as e:
        raise RuntimeError(f"Failed to tokenize text with {ENCODER_NAME}: {e}")

def validate_thresholds(
    variant: PromptVariant, strict: bool = True
) -> Tuple[bool, str]:
    """
    Validate that a prompt variant's token count falls within its expected complexity range.

    Args:
        variant: The prompt variant to validate.
        strict: If True, raise an error on mismatch. If False, return a warning message.

    Returns:
        A tuple of (is_valid, message).
        If strict=True and invalid, raises ValueError.
    """
    label = variant.complexity_label
    token_count = variant.token_count
    lower, upper = THRESHOLDS[label]

    if upper is None:
        # degenerate case: just needs to be > lower
        if token_count <= lower:
            msg = (
                f"Variant '{label}' has {token_count} tokens, "
                f"expected > {lower} tokens."
            )
            if strict:
                raise ValueError(msg)
            return False, msg
    else:
        if not (lower <= token_count <= upper):
            msg = (
                f"Variant '{label}' has {token_count} tokens, "
                f"expected between {lower} and {upper} tokens."
            )
            if strict:
                raise ValueError(msg)
            return False, msg

    return True, f"Variant '{label}' token count ({token_count}) is within expected range."

def calculate_and_validate_variants(
    variants: List[PromptVariant], strict: bool = True
) -> List[PromptVariant]:
    """
    Calculate token counts for a list of variants and validate thresholds.

    This function updates the `token_count` field on each variant and validates
    against the defined complexity thresholds.

    Args:
        variants: List of prompt variants with text populated.
        strict: If True, raise ValueError on threshold mismatch.

    Returns:
        The same list of variants, updated with token counts.

    Raises:
        ValueError: If a variant's token count does not match its complexity label
                    and strict=True.
    """
    for variant in variants:
        if variant.prompt_text is None:
            raise ValueError(f"Variant {variant.id} has no prompt_text to tokenize.")

        count = get_token_count(variant.prompt_text)
        variant.token_count = count

        # Validate immediately
        is_valid, msg = validate_thresholds(variant, strict=strict)
        if not is_valid:
            # If not strict, we already returned the message above, but we continue
            # to log or handle as needed. In strict mode, the exception is raised.
            pass

    return variants

def main():
    """
    Example usage: Load a single HumanEval problem, generate variants,
    calculate tokens, and print results.
    """
    import sys
    from pathlib import Path

    # Add project root to path if running as script
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from data.fetcher import load_human_eval
    from prompts.generator import generate_prompt_variants
    from models.data_models import ComplexityLabel

    # Load one problem for demonstration
    problems = load_human_eval()
    if not problems:
        print("No HumanEval problems found. Ensure data/raw/human_eval.jsonl exists.")
        return

    problem = problems[0]
    print(f"Processing problem: {problem.task_id}")

    # Generate variants
    variants = generate_prompt_variants(problem)
    print(f"Generated {len(variants)} variants.")

    # Calculate and validate tokens
    try:
        updated_variants = calculate_and_validate_variants(variants, strict=False)
    except ValueError as e:
        print(f"Validation failed: {e}")
        return

    # Print results
    print("\nToken Counts and Validation:")
    for v in updated_variants:
        status = "OK" if v.token_count is not None else "MISSING"
        print(f"  {v.complexity_label:15} | Tokens: {v.token_count:4} | {status}")

    # Check for specific threshold violations
    for v in updated_variants:
        is_valid, msg = validate_thresholds(v, strict=False)
        if not is_valid:
            print(f"  WARNING: {msg}")

    print("\nDone.")

if __name__ == "__main__":
    main()