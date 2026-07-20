"""
Ablation data generator for Socratic Transformers project.

This module implements the ablation condition (FR-007) by replacing critique text
with neutral placeholder text of equivalent token length. This allows for
isolating the effect of the critique signal in the dialogue-based self-teaching
process.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.config import get_config


def count_tokens(text: str, tokenizer: Optional[Any] = None) -> int:
    """
    Count the number of tokens in a text string.

    If a tokenizer is provided, it uses the tokenizer's encoding.
    Otherwise, it falls back to a simple whitespace-based approximation.

    Args:
        text: The input text string.
        tokenizer: Optional HuggingFace tokenizer.

    Returns:
        The estimated token count.
    """
    if tokenizer is not None:
        try:
            return len(tokenizer.encode(text, add_special_tokens=False))
        except Exception:
            # Fallback if tokenizer fails
            pass

    # Simple whitespace-based approximation
    return len(text.split())


def generate_neutral_placeholder(target_token_count: int, base_text: str = "The model considers the previous answer and generates a revised response based on a neutral evaluation of the logical consistency and factual accuracy of the statement.") -> str:
    """
    Generate a neutral placeholder text with approximately the same token count
    as the original critique.

    This implements the ablation condition where the semantic content of the
    critique is removed but the structural length is preserved.

    Args:
        target_token_count: The target number of tokens to match.
        base_text: The base neutral text to repeat/modify.

    Returns:
        A neutral placeholder string with token count approximating the target.
    """
    if target_token_count <= 0:
        return ""

    # Calculate how many times we need to repeat the base text
    base_tokens = count_tokens(base_text)
    if base_tokens == 0:
        base_tokens = 1  # Avoid division by zero

    repetitions = max(1, (target_token_count // base_tokens) + 1)
    full_text = (base_text + " ") * repetitions

    # Trim to approximate target token count
    tokens = full_text.split()
    if len(tokens) > target_token_count:
        tokens = tokens[:target_token_count]

    return " ".join(tokens)


def create_ablation_tuple(dialogue_tuple: Dict[str, Any], tokenizer: Optional[Any] = None) -> Dict[str, Any]:
    """
    Create an ablation tuple from a dialogue tuple by replacing the critique
    with a neutral placeholder of equivalent token length.

    Args:
        dialogue_tuple: A dictionary containing the dialogue tuple with keys:
            - question: The original question
            - initial_answer: The initial answer generated
            - critique: The self-generated critique (to be ablated)
            - revised_answer: The revised answer
            - (optional) metadata fields
        tokenizer: Optional tokenizer for accurate token counting.

    Returns:
        A new dictionary with the critique replaced by a neutral placeholder.
        The structure remains identical to the input for direct comparison.
    """
    if "critique" not in dialogue_tuple:
        raise ValueError("Input dialogue tuple must contain a 'critique' field")

    original_critique = dialogue_tuple["critique"]
    original_token_count = count_tokens(original_critique, tokenizer)

    # Generate neutral placeholder
    neutral_placeholder = generate_neutral_placeholder(original_token_count)

    # Create ablated tuple
    ablated_tuple = dialogue_tuple.copy()
    ablated_tuple["critique"] = neutral_placeholder
    ablated_tuple["ablation_type"] = "neutral_placeholder"
    ablated_tuple["original_critique_token_count"] = original_token_count
    ablated_tuple["ablated_critique_token_count"] = count_tokens(neutral_placeholder, tokenizer)

    return ablated_tuple


def generate_ablation_dataset(
    dialogue_dataset_path: str,
    output_path: str,
    tokenizer: Optional[Any] = None,
    sample_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate an ablation dataset from a dialogue dataset.

    This function reads dialogue tuples from a JSONL file, applies the ablation
    transformation (replacing critiques with neutral placeholders), and writes
    the result to a new JSONL file.

    Args:
        dialogue_dataset_path: Path to the input JSONL file containing dialogue tuples.
        output_path: Path to write the output JSONL file.
        tokenizer: Optional tokenizer for accurate token counting.
        sample_size: Optional number of samples to process (for testing).

    Returns:
        A list of ablated dialogue tuples.
    """
    config = get_config()
    logger = config.logger

    if not Path(dialogue_dataset_path).exists():
        raise FileNotFoundError(f"Input dialogue dataset not found: {dialogue_dataset_path}")

    ablated_tuples = []

    logger.info(f"Reading dialogue dataset from {dialogue_dataset_path}")
    with open(dialogue_dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if sample_size:
        lines = lines[:sample_size]

    logger.info(f"Processing {len(lines)} dialogue tuples")

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        try:
            dialogue_tuple = json.loads(line)
            ablated_tuple = create_ablation_tuple(dialogue_tuple, tokenizer)
            ablated_tuples.append(ablated_tuple)

            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(lines)} samples")

        except json.JSONDecodeError as e:
            logger.warning(f"Skipping invalid JSON at line {i + 1}: {e}")
            continue
        except ValueError as e:
            logger.warning(f"Skipping invalid tuple at line {i + 1}: {e}")
            continue

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing ablated dataset to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for tuple_data in ablated_tuples:
            f.write(json.dumps(tuple_data, ensure_ascii=False) + '\n')

    logger.info(f"Generated {len(ablated_tuples)} ablated tuples")
    return ablated_tuples


def main():
    """
    Main entry point for the ablation data generator.

    This script reads the dialogue dataset generated by T014 and produces
    the ablated dataset for comparative analysis in T031.
    """
    config = get_config()
    logger = config.logger

    # Default paths - can be overridden via config or command line
    dialogue_dataset_path = config.data_paths.get("dialogue_dataset", "data/processed/dialogue_dataset.jsonl")
    ablation_dataset_path = config.data_paths.get("ablation_dataset", "data/processed/ablation_dataset.jsonl")

    logger.info("Starting ablation data generation")
    logger.info(f"Input: {dialogue_dataset_path}")
    logger.info(f"Output: {ablation_dataset_path}")

    try:
        # Generate ablation dataset
        ablated_data = generate_ablation_dataset(
            dialogue_dataset_path=dialogue_dataset_path,
            output_path=ablation_dataset_path
        )

        logger.info(f"Successfully generated {len(ablated_data)} ablated tuples")
        logger.info(f"Ablation dataset saved to: {ablation_dataset_path}")

        # Print summary statistics
        if ablated_data:
            total_tokens = sum(t.get("original_critique_token_count", 0) for t in ablated_data)
            avg_tokens = total_tokens / len(ablated_data)
            logger.info(f"Average critique token count: {avg_tokens:.2f}")

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.error("Please ensure the dialogue dataset has been generated by T014 first.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during ablation generation: {e}")
        raise


if __name__ == "__main__":
    main()
