"""
Ablation Data Generator for Socratic Transformers Project.

This module implements FR-007: replacing critique text with neutral placeholder
text of equivalent token length to isolate the effect of the critique signal.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import tiktoken for accurate token counting as per existing API surface
try:
    import tiktoken
except ImportError:
    print("Error: tiktoken is required. Install with: pip install tiktoken", file=sys.stderr)
    sys.exit(1)

# Import config from existing API surface
from src.utils.config import get_config


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Count the number of tokens in a string using the specified encoding.

    Args:
        text: The input string to tokenize.
        encoding_name: The name of the tiktoken encoding to use (default: cl100k_base).

    Returns:
        The number of tokens in the text.
    """
    if not text:
        return 0
    try:
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))
    except Exception as e:
        raise RuntimeError(f"Failed to encode text with {encoding_name}: {e}")


def generate_neutral_placeholder(target_token_count: int, encoding_name: str = "cl100k_base") -> str:
    """
    Generate a neutral placeholder string that matches the target token count.

    The placeholder consists of repeated neutral phrases designed to be semantically
    inert while matching the token length of the original critique.

    Args:
        target_token_count: The number of tokens the placeholder should approximate.
        encoding_name: The tiktoken encoding name.

    Returns:
        A string of neutral text with approximately target_token_count tokens.
    """
    if target_token_count <= 0:
        return ""

    # Neutral phrases that are semantically empty but token-dense enough
    # "The analysis proceeds without specific critique." is roughly 8-9 tokens
    base_phrase = "The analysis proceeds without specific critique."
    enc = tiktoken.get_encoding(encoding_name)
    base_tokens = len(enc.encode(base_phrase))

    if base_tokens == 0:
        base_tokens = 1

    # Calculate how many full phrases we need
    num_phrases = target_token_count // base_tokens
    remainder = target_token_count % base_tokens

    # Build the base placeholder
    placeholder_parts = [base_phrase] * num_phrases

    # Add a filler to match the remainder if necessary
    if remainder > 0:
        # Use a simple filler that we can approximate
        filler = " " * remainder  # Approximation; spaces are tokens
        # To be more precise, we could try to find a word sequence, but spaces
        # usually work as token separators or single tokens depending on the model.
        # A safer bet for exactness in a placeholder context is just repeating
        # a neutral token-like string. Let's use a simple repetition.
        # We need 'remainder' tokens. Let's try to find a short sequence.
        # "neutral" is 1 token. " " is 1 token.
        # Let's just append spaces or a simple word repeated.
        # Since exact token matching is hard without iterative search,
        # we will approximate with a string of spaces or simple words.
        # For the purpose of FR-007 (equivalent token length), an approximation
        # is acceptable, but let's try to be closer.
        filler_text = "neutral " * remainder
        placeholder_parts.append(filler_text)

    return " ".join(placeholder_parts)


def create_ablation_tuple(dialogue_tuple: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an ablated version of a dialogue tuple.

    Replaces the 'critique' field with a neutral placeholder of equivalent
    token length, while keeping all other fields (question, initial_answer,
    revised_answer) intact.

    Args:
        dialogue_tuple: A dictionary with keys:
            - 'question'
            - 'initial_answer'
            - 'critique'
            - 'revised_answer'

    Returns:
        A new dictionary with the 'critique' field replaced by the placeholder.
    """
    required_keys = {'question', 'initial_answer', 'critique', 'revised_answer'}
    if not required_keys.issubset(dialogue_tuple.keys()):
        raise ValueError(f"Dialogue tuple missing required keys: {required_keys - dialogue_tuple.keys()}")

    original_critique = dialogue_tuple['critique']
    if not isinstance(original_critique, str):
        original_critique = str(original_critique)

    token_count = count_tokens(original_critique)
    placeholder = generate_neutral_placeholder(token_count)

    ablated_tuple = dialogue_tuple.copy()
    ablated_tuple['critique'] = placeholder
    ablated_tuple['condition'] = 'ablation'  # Tag for downstream analysis
    ablated_tuple['original_critique_length'] = token_count

    return ablated_tuple


def generate_ablation_dataset(
    input_path: str,
    output_path: str,
    encoding_name: str = "cl100k_base"
) -> int:
    """
    Generate an ablation dataset from a JSONL file of dialogue tuples.

    Reads the input file line by line, creates an ablated version of each record,
    and writes the results to the output file.

    Args:
        input_path: Path to the input JSONL file containing dialogue tuples.
        output_path: Path to the output JSONL file for ablated tuples.
        encoding_name: The tiktoken encoding name to use.

    Returns:
        The number of records processed.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    processed_count = 0

    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:

        for line_num, line in enumerate(f_in, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
                ablated_record = create_ablation_tuple(record)
                f_out.write(json.dumps(ablated_record) + '\n')
                processed_count += 1
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON at line {line_num}: {e}", file=sys.stderr)
            except ValueError as e:
                print(f"Warning: Skipping record at line {line_num} due to schema error: {e}", file=sys.stderr)

    return processed_count


def main():
    """
    Main entry point for the ablation data generator.

    Reads configuration from environment or defaults, processes the dialogue dataset,
    and outputs the ablated dataset.
    """
    config = get_config()

    # Determine paths
    # Default to data/processed/dialogues.jsonl for input if not specified
    input_path = os.environ.get('ABLATION_INPUT', config.get('data', {}).get('processed_dialogues', 'data/processed/dialogues.jsonl'))
    output_path = os.environ.get('ABLATION_OUTPUT', config.get('data', {}).get('ablated_dialogues', 'data/processed/ablated_dialogues.jsonl'))

    print(f"Generating ablation dataset...")
    print(f"  Input: {input_path}")
    print(f"  Output: {output_path}")

    try:
        count = generate_ablation_dataset(input_path, output_path)
        print(f"Successfully processed {count} records.")
        print(f"Ablated dataset written to: {output_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating ablation dataset: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()