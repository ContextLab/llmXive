"""
Ablation data generator for Socratic Transformers project.

This module implements FR-007: replacing critique text with neutral placeholder
text of equivalent token length to isolate the effect of the critique signal.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.config import get_config
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def count_tokens(text: str, tokenizer: Optional[Any] = None) -> int:
    """
    Count tokens in a text string.

    If a tokenizer is provided, use it for accurate token counting.
    Otherwise, fall back to a simple whitespace-based estimate.

    Args:
        text: The text to count tokens for.
        tokenizer: Optional HuggingFace tokenizer instance.

    Returns:
        Estimated token count.
    """
    if tokenizer is not None:
        try:
            return len(tokenizer.encode(text, add_special_tokens=False))
        except Exception as e:
            logger.warning(f"Tokenizer encoding failed, falling back to estimate: {e}")

    # Fallback: whitespace-based estimate (rough approximation)
    return len(text.split())


def generate_neutral_placeholder(original_text: str, target_token_count: int, tokenizer: Optional[Any] = None) -> str:
    """
    Generate a neutral placeholder text with approximately the same token length
    as the original critique text.

    The placeholder consists of neutral, non-informative text that maintains
    the structural presence of a critique without providing actual reasoning
    content. This isolates the effect of the critique signal from the presence
    of text itself.

    Args:
        original_text: The original critique text to match length against.
        target_token_count: The target number of tokens (from original text).
        tokenizer: Optional tokenizer for accurate length matching.

    Returns:
        A neutral placeholder string with approximately target_token_count tokens.
    """
    # Neutral template phrases (non-informative, structurally similar)
    neutral_phrases = [
        "The reasoning provided here requires further examination.",
        "This analysis may benefit from additional consideration.",
        "The argument presented warrants a closer review of assumptions.",
        "Further verification of the underlying logic is recommended.",
        "This perspective could be strengthened with more evidence.",
    ]

    # Calculate tokens per phrase
    if tokenizer is not None:
        phrase_tokens = [len(tokenizer.encode(p, add_special_tokens=False)) for p in neutral_phrases]
        avg_tokens_per_phrase = sum(phrase_tokens) / len(phrase_tokens)
    else:
        avg_tokens_per_phrase = 8  # Rough estimate

    # Calculate how many phrases we need
    num_phrases = max(1, int(target_token_count / avg_tokens_per_phrase))

    # Build placeholder by cycling through neutral phrases
    placeholder_parts = []
    for i in range(num_phrases):
        phrase = neutral_phrases[i % len(neutral_phrases)]
        placeholder_parts.append(phrase)

    # Join with spaces
    placeholder = " ".join(placeholder_parts)

    # Fine-tune length if we have a tokenizer
    if tokenizer is not None:
        current_tokens = len(tokenizer.encode(placeholder, add_special_tokens=False))
        diff = target_token_count - current_tokens

        # Adjust by adding/removing neutral filler
        filler = " further consideration is necessary. "
        filler_tokens = len(tokenizer.encode(filler, add_special_tokens=False))

        if diff > 0:
            # Add filler phrases
            repeats = diff // filler_tokens
            placeholder += filler * repeats
        elif diff < 0:
            # Remove trailing filler if possible
            while current_tokens > target_token_count and placeholder.endswith(filler):
                placeholder = placeholder[:-len(filler)]
                current_tokens -= filler_tokens

    return placeholder


def create_ablation_tuple(dialogue_tuple: Dict[str, Any], tokenizer: Optional[Any] = None) -> Dict[str, Any]:
    """
    Create an ablated version of a dialogue tuple by replacing the critique
    with a neutral placeholder of equivalent token length.

    Args:
        dialogue_tuple: A dictionary containing the dialogue tuple with keys:
            - question: str
            - initial_answer: str
            - critique: dict with 'confidence_score', 'reasoning_snippet'
            - revised_answer: str
        tokenizer: Optional tokenizer for accurate token counting.

    Returns:
        A new dictionary with the critique's reasoning_snippet replaced by
        a neutral placeholder.
    """
    if "critique" not in dialogue_tuple:
        logger.warning("Dialogue tuple missing critique field, returning unchanged")
        return dialogue_tuple

    critique = dialogue_tuple["critique"]
    original_reasoning = critique.get("reasoning_snippet", "")

    if not original_reasoning:
        logger.warning("Critique reasoning_snippet is empty, returning unchanged")
        return dialogue_tuple

    # Count tokens in original reasoning
    target_tokens = count_tokens(original_reasoning, tokenizer)

    # Generate neutral placeholder
    neutral_placeholder = generate_neutral_placeholder(original_reasoning, target_tokens, tokenizer)

    # Create ablated tuple
    ablated_tuple = dialogue_tuple.copy()
    ablated_tuple["critique"] = critique.copy()
    ablated_tuple["critique"]["reasoning_snippet"] = neutral_placeholder
    ablated_tuple["critique"]["is_ablated"] = True
    ablated_tuple["critique"]["original_token_count"] = target_tokens

    logger.info(f"Created ablated tuple: original={len(original_reasoning)} chars, "
               f"ablated={len(neutral_placeholder)} chars, tokens={target_tokens}")

    return ablated_tuple


def generate_ablation_dataset(
    input_path: str,
    output_path: str,
    tokenizer: Optional[Any] = None,
    sample_size: Optional[int] = None
) -> Dict[str, int]:
    """
    Generate an ablated dataset from dialogue tuples.

    This function reads dialogue tuples from a JSONL file, replaces each
    critique's reasoning_snippet with a neutral placeholder of equivalent
    token length, and writes the result to a new JSONL file.

    Args:
        input_path: Path to input JSONL file containing dialogue tuples.
        output_path: Path to output JSONL file for ablated tuples.
        tokenizer: Optional tokenizer for accurate token counting.
        sample_size: Optional limit on number of tuples to process.

    Returns:
        A dictionary with processing statistics:
            - total_processed: Number of tuples processed
            - successful_ablations: Number of successful ablations
            - skipped_empty: Number of tuples with empty critiques
            - file_size_bytes: Size of output file in bytes
    """
    stats = {
        "total_processed": 0,
        "successful_ablations": 0,
        "skipped_empty": 0,
        "file_size_bytes": 0
    }

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting ablation dataset generation from {input_path}")
    logger.info(f"Output will be written to {output_path}")

    processed_count = 0

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue

            try:
                dialogue_tuple = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON at line {line_num}: {e}")
                continue

            stats["total_processed"] += 1
            processed_count += 1

            # Check sample size limit
            if sample_size is not None and processed_count > sample_size:
                logger.info(f"Reached sample_size limit ({sample_size}), stopping")
                break

            # Create ablated tuple
            ablated = create_ablation_tuple(dialogue_tuple, tokenizer)

            # Write to output
            outfile.write(json.dumps(ablated, ensure_ascii=False) + '\n')
            stats["successful_ablations"] += 1

            # Log progress every 100 items
            if line_num % 100 == 0:
                logger.info(f"Processed {line_num} lines...")

    # Get output file size
    stats["file_size_bytes"] = Path(output_path).stat().st_size

    logger.info(f"Ablation dataset generation complete:")
    logger.info(f"  Total processed: {stats['total_processed']}")
    logger.info(f"  Successful ablations: {stats['successful_ablations']}")
    logger.info(f"  Output file size: {stats['file_size_bytes']} bytes")

    return stats


def main():
    """
    Main entry point for ablation dataset generation.

    Reads dialogue tuples from data/processed/dialogue_tuples.jsonl,
    generates ablated versions, and writes to data/processed/ablation_tuples.jsonl.
    """
    config = get_config()

    # Determine paths
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "processed" / "dialogue_tuples.jsonl"
    output_path = project_root / "data" / "processed" / "ablation_tuples.jsonl"

    # Check if input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T014 (generate_dialogue.py) first to create dialogue tuples.")
        sys.exit(1)

    # Load tokenizer if configured
    tokenizer = None
    if config.model_path:
        try:
            from transformers import AutoTokenizer
            logger.info(f"Loading tokenizer from {config.model_path}")
            tokenizer = AutoTokenizer.from_pretrained(config.model_path, trust_remote_code=True)
        except Exception as e:
            logger.warning(f"Failed to load tokenizer: {e}. Using whitespace-based token counting.")
            tokenizer = None

    # Generate ablation dataset
    # Process first 1000 tuples for the ablation study (or all if fewer)
    sample_limit = config.get("ablation_sample_size", 1000)

    stats = generate_ablation_dataset(
        input_path=str(input_path),
        output_path=str(output_path),
        tokenizer=tokenizer,
        sample_size=sample_limit
    )

    # Print summary
    print("\n" + "="*60)
    print("ABLATION DATASET GENERATION COMPLETE")
    print("="*60)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Processed: {stats['total_processed']} tuples")
    print(f"Generated: {stats['successful_ablations']} ablated tuples")
    print(f"Output size: {stats['file_size_bytes']} bytes")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
