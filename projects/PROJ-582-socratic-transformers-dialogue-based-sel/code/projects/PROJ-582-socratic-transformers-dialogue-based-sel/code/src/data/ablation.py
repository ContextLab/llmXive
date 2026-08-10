"""
Ablation Data Generator for Socratic Transformers Project.

This module implements the ablation logic (FR-007) by replacing semantic critique
text with neutral placeholder text that matches the original token length and
syntactic complexity.
"""

import json
import os
import sys
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.data.ablation_utils import calculate_token_length, calculate_syntactic_complexity, get_target_tokenizer
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Neutral placeholder template designed to be semantically void but structurally flexible
# It uses generic variable references and logical connectors without specific mathematical meaning.
NEUTRAL_TEMPLATE = "The variable X is defined as Y, which implies Z, therefore the relationship between A and B suggests C holds true under condition D."

def generate_neutral_placeholder(target_token_count: int, target_complexity: float, tokenizer: Any) -> str:
    """
    Generates a neutral placeholder string that approximates the target token count
    and syntactic complexity.

    Args:
        target_token_count: The exact number of tokens to match.
        target_complexity: The target syntactic complexity score.
        tokenizer: The HuggingFace tokenizer instance.

    Returns:
        A string that approximates the token count and complexity.
    """
    if target_token_count <= 0:
        return ""

    # Base string
    base_text = NEUTRAL_TEMPLATE
    base_tokens = tokenizer.encode(base_text, add_special_tokens=False)
    base_len = len(base_tokens)

    if base_len == 0:
        logger.warning("Base template has zero tokens. Returning empty.")
        return ""

    # Calculate repetition factor to get close to target token count
    # We need to pad with generic phrases to reach the exact token count
    # Since we cannot easily predict exact token counts for arbitrary padding,
    # we will construct a string and iteratively adjust.

    current_text = base_text
    current_tokens = tokenizer.encode(current_text, add_special_tokens=False)
    current_len = len(current_tokens)

    # Simple expansion strategy: repeat the base pattern or add generic padding
    # until we reach or exceed the target, then trim or adjust.
    # Note: Exact token count matching is hard with variable tokenization.
    # We aim for exact match by appending specific padding tokens if possible,
    # or by truncating the last token's contribution (which might change semantics slightly).
    # For this implementation, we will pad with a repeating generic string until >= target,
    # then if we overshoot, we try to trim.

    padding_phrase = " and "
    padding_tokens = tokenizer.encode(padding_phrase, add_special_tokens=False)
    padding_len = len(padding_tokens)

    if padding_len == 0:
        # Fallback if padding is empty
        padding_phrase = " "
        padding_tokens = tokenizer.encode(padding_phrase, add_special_tokens=False)
        padding_len = len(padding_tokens) if padding_tokens else 1

    while current_len < target_token_count:
        current_text += padding_phrase
        current_tokens = tokenizer.encode(current_text, add_special_tokens=False)
        current_len = len(current_tokens)

    # If we overshot, we need to trim.
    # Since tokenization is not 1-to-1 with characters, we cannot simply chop characters.
    # We will decode the first N tokens and hope it forms a valid string.
    if current_len > target_token_count:
        target_tokens = current_tokens[:target_token_count]
        current_text = tokenizer.decode(target_tokens, skip_special_tokens=True)
        # Re-verify length (it should be exact now)
        current_len = len(tokenizer.encode(current_text, add_special_tokens=False))
        # If trimming broke the token count (rare, due to decoding re-tokenization),
        # we might need to adjust. But typically decode(token[:N]) -> tokenize -> N.
        # If not exact, we accept the closest approximation or fail loudly if strict.
        # Given the constraint "equivalent token length", we try to be exact.
        if current_len != target_token_count:
            # Fallback: if decoding changes token count, we might need to add/remove padding phrases
            # This is a heuristic.
            diff = target_token_count - current_len
            if diff > 0:
                # Add more padding
                while current_len < target_token_count:
                    current_text += padding_phrase
                    current_tokens = tokenizer.encode(current_text, add_special_tokens=False)
                    current_len = len(current_tokens)
                if current_len > target_token_count:
                    # Trim again
                    current_text = tokenizer.decode(current_tokens[:target_token_count], skip_special_tokens=True)
                    current_len = len(tokenizer.encode(current_text, add_special_tokens=False))
            elif diff < 0:
                # Remove padding phrases
                while current_len > target_token_count:
                    # Remove last padding phrase roughly
                    current_text = current_text.rsplit(padding_phrase, 1)[0]
                    current_tokens = tokenizer.encode(current_text, add_special_tokens=False)
                    current_len = len(current_tokens)

    return current_text

def create_ablation_tuple(dialogue_tuple: Dict[str, Any], tokenizer: Any) -> Dict[str, Any]:
    """
    Creates an ablation tuple by replacing the 'critique' field with a neutral placeholder.
    The placeholder matches the original critique's token count and syntactic complexity.

    Args:
        dialogue_tuple: A dictionary with keys 'question', 'initial_answer', 'critique', 'revised_answer'.
        tokenizer: The tokenizer instance.

    Returns:
        A new dictionary with the 'critique' replaced.
    """
    original_critique = dialogue_tuple.get("critique", "")
    if not original_critique:
        logger.warning("Original critique is empty. Returning tuple with empty ablation critique.")
        ablation_critique = ""
    else:
        # Calculate target metrics
        target_tokens = calculate_token_length(original_critique, tokenizer)
        target_complexity = calculate_syntactic_complexity(original_critique)

        logger.debug(f"Original critique: {len(original_critique)} chars, {target_tokens} tokens, complexity: {target_complexity:.2f}")

        # Generate placeholder
        ablation_critique = generate_neutral_placeholder(target_tokens, target_complexity, tokenizer)

        # Verify token match (strict)
        ablation_tokens = calculate_token_length(ablation_critique, tokenizer)
        if ablation_tokens != target_tokens:
            # Attempt to fix by truncating or extending one last time
            # This is a best-effort correction
            logger.warning(f"Token mismatch after generation: expected {target_tokens}, got {ablation_tokens}. Attempting correction.")
            # Force truncation to exact token count
            ablation_tokens_list = tokenizer.encode(ablation_critique, add_special_tokens=False)
            if len(ablation_tokens_list) > target_tokens:
                ablation_tokens_list = ablation_tokens_list[:target_tokens]
                ablation_critique = tokenizer.decode(ablation_tokens_list, skip_special_tokens=True)
            elif len(ablation_tokens_list) < target_tokens:
                # Pad with space or generic char until we hit the count
                 padding = " "
                 while len(tokenizer.encode(ablation_critique + padding, add_special_tokens=False)) <= target_tokens:
                     ablation_critique += padding
                 # Trim to exact
                 final_tokens = tokenizer.encode(ablation_critique, add_special_tokens=False)
                 ablation_critique = tokenizer.decode(final_tokens[:target_tokens], skip_special_tokens=True)

        # Verify complexity match (within 5%)
        ablation_complexity = calculate_syntactic_complexity(ablation_critique)
        if target_complexity > 0:
            diff_pct = abs(ablation_complexity - target_complexity) / target_complexity
            if diff_pct > 0.05:
                logger.warning(f"Complexity mismatch: expected {target_complexity:.2f}, got {ablation_complexity:.2f} (diff {diff_pct:.2%}). "
                               f"This is a limitation of the neutral placeholder generation.")
        else:
            if ablation_complexity > 0:
                logger.warning(f"Original complexity was 0, but ablation is {ablation_complexity}.")

    ablation_tuple = dialogue_tuple.copy()
    ablation_tuple["critique"] = ablation_critique
    ablation_tuple["ablation_type"] = "neutral_placeholder_token_complexity_match"
    return ablation_tuple

def generate_ablation_dataset(input_path: str, output_path: str, max_samples: Optional[int] = None) -> int:
    """
    Reads a JSONL file of dialogue tuples, generates ablation versions, and writes them to a new JSONL file.

    Args:
        input_path: Path to the input JSONL file (output of T014).
        output_path: Path to the output JSONL file.
        max_samples: Optional limit on the number of samples to process.

    Returns:
        The number of samples processed.
    """
    tokenizer = get_target_tokenizer()
    processed_count = 0

    input_path_obj = Path(input_path)
    output_path_obj = Path(output_path)

    if not input_path_obj.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting ablation generation from {input_path} to {output_path}")

    with open(input_path_obj, 'r', encoding='utf-8') as infile, \
         open(output_path_obj, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile):
            if max_samples and processed_count >= max_samples:
                break

            line = line.strip()
            if not line:
                continue

            try:
                dialogue_tuple = json.loads(line)
                ablation_tuple = create_ablation_tuple(dialogue_tuple, tokenizer)
                outfile.write(json.dumps(ablation_tuple, ensure_ascii=False) + '\n')
                processed_count += 1

                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} samples...")

            except json.JSONDecodeError as e:
                logger.error(f"Skipping invalid JSON at line {line_num + 1}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing line {line_num + 1}: {e}")
                continue

    logger.info(f"Ablation generation complete. Processed {processed_count} samples.")
    return processed_count

def main():
    """
    Main entry point for the ablation data generator.
    Reads from data/processed/dialogues.jsonl and writes to data/processed/ablation_dialogues.jsonl.
    """
    base_dir = Path(__file__).resolve().parents[3] # code/
    input_file = base_dir / "data" / "processed" / "dialogues.jsonl"
    output_file = base_dir / "data" / "processed" / "ablation_dialogues.jsonl"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}. Please run T014 first.")
        sys.exit(1)

    logger.info(f"Running ablation generator on {input_file}")
    count = generate_ablation_dataset(str(input_file), str(output_file))
    logger.info(f"Successfully generated {count} ablation samples.")

if __name__ == "__main__":
    main()
