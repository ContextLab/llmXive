from __future__ import annotations

import tiktoken
from typing import Dict, List, Tuple, Optional

from models.data_models import PromptVariant, ComplexityLabel
from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)

# Token thresholds per complexity level (secondary indicators)
# Note: These are for validation/alerting only. Primary complexity definition is structural element count.
THRESHOLDS: Dict[ComplexityLabel, int] = {
    "simple": 50,
    "moderate": 150,
    "complex": 300,
    "very_complex": 600,
    "degenerate": 1000,
}

def get_token_count(text: str) -> int:
    """
    Count tokens using tiktoken's cl100k_base (standard for most LLMs).
    This function is the primary mechanism for token counting across the project.
    """
    try:
        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except Exception as e:
        logger.error(f"Error encoding text: {e}")
        raise

def validate_thresholds(variants: List[PromptVariant]) -> List[Tuple[PromptVariant, str]]:
    """
    Validate that token counts roughly align with complexity labels.
    Returns a list of (variant, warning_message) for mismatches.
    
    NOTE: Token thresholds are SECONDARY. A mismatch here does not invalidate
    the complexity label if the structural element count is correct.
    """
    warnings = []
    for variant in variants:
        label = variant.complexity_label
        count = variant.token_count
        threshold = THRESHOLDS.get(label, float("inf"))

        # Allow some tolerance (e.g., 20%) to account for natural variation
        tolerance = int(threshold * 0.2)
        if count > threshold + tolerance:
            warnings.append(
                (variant, f"Token count {count} exceeds expected threshold {threshold} by >20%")
            )
        elif count < threshold - tolerance and label != "simple":
            # Simple is allowed to be low
            warnings.append(
                (variant, f"Token count {count} is below expected threshold {threshold} by >20%")
            )

    return warnings

def calculate_and_validate_variants(variants: List[PromptVariant]) -> List[PromptVariant]:
    """
    Recalculate token counts for all variants and validate thresholds.
    Updates variant.token_count in place.
    
    This is the main entry point for ensuring all prompt variants have accurate
    token counts before storage or analysis.
    """
    for variant in variants:
        variant.token_count = get_token_count(variant.prompt_text)

    warnings = validate_thresholds(variants)
    for variant, msg in warnings:
        logger.warning(f"{variant.variant_id}: {msg}")

    return variants

def main():
    """
    Standalone runner to test token counting on sample text.
    Useful for verifying the tokenizer works correctly in isolation.
    """
    sample_texts = {
        "simple": "Write a function to add two numbers.",
        "moderate": "Write a function to add two numbers.\nExample: add(1, 2) -> 3.",
        "complex": "Write a function to add two numbers.\nExample: add(1, 2) -> 3.\nConstraint: Handle negative numbers.",
        "very_complex": "Write a function to add two numbers.\nExample: add(1, 2) -> 3.\nConstraint: Handle negative numbers.\nStep 1: Parse input. Step 2: Compute sum.",
        "degenerate": "Write a function to add two numbers.\nExample: add(1, 2) -> 3.\nConstraint: Handle negative numbers.\nStep 1: Parse input. Step 2: Compute sum.\n" + "Note: Be careful. " * 50,
    }

    print("Token counts for sample prompts:")
    for label, text in sample_texts.items():
        count = get_token_count(text)
        expected = THRESHOLDS.get(label, "N/A")
        print(f"  {label}: {count} tokens (expected threshold: ~{expected})")

if __name__ == "__main__":
    main()