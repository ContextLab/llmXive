import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Importing from the project's config utility as per existing API
from src.utils.config import get_config
from src.utils.logging import get_logger

# Initialize logger for the module
logger = get_logger(__name__)


def count_tokens(text: str, tokenizer: Optional[Any] = None) -> int:
    """
    Count the number of tokens in a given text string.
    
    If a tokenizer is provided, use its encode method. Otherwise, approximate
    token count by splitting on whitespace (1 token ~= 1 word).
    
    Args:
        text: The input text string.
        tokenizer: An optional HuggingFace tokenizer instance.
        
    Returns:
        The estimated number of tokens.
    """
    if not text:
        return 0
    
    if tokenizer is not None:
        # Use the tokenizer's encoding if available
        try:
            return len(tokenizer.encode(text, add_special_tokens=False))
        except Exception as e:
            logger.warning(f"Tokenizer encoding failed: {e}. Falling back to word count.")
    
    # Fallback: simple whitespace split
    return len(text.split())


def generate_neutral_placeholder(token_count: int, target_text: str) -> str:
    """
    Generate a neutral placeholder string with approximately the same token length
    as the target text.
    
    The placeholder is a repetitive, semantically neutral phrase designed to
    occupy similar context space without conveying specific critique information.
    This satisfies the ablation requirement of replacing critique with 'neutral
    placeholder text of equivalent token length' (FR-007).
    
    Args:
        token_count: The target number of tokens to match.
        target_text: The original text (used only for context if tokenizer fails).
        
    Returns:
        A string of neutral text approximating the token count.
    """
    if token_count <= 0:
        return ""
    
    # Base neutral phrase: "The analysis proceeds without specific critique."
    # This is semantically empty regarding the specific logic but structurally sound.
    base_phrase = "The reasoning process continues without specific adversarial critique."
    
    # Estimate tokens in base phrase (approx 10-12 tokens)
    base_tokens = count_tokens(base_phrase)
    if base_tokens == 0:
        base_tokens = 1
        
    repeats = max(1, token_count // base_tokens)
    remainder = token_count % base_tokens
    
    # Construct the repeated string
    placeholder = base_phrase * repeats
    
    # Pad or trim to get closer to exact count if needed (simple whitespace adjustment)
    current_tokens = count_tokens(placeholder)
    
    if current_tokens < token_count:
        # Add filler words to approximate the remainder
        filler = " additional " * (token_count - current_tokens)
        placeholder += filler
    elif current_tokens > token_count:
        # Truncate by removing words (simple approach)
        words = placeholder.split()
        if len(words) > token_count:
            placeholder = " ".join(words[:token_count])
    
    return placeholder


def create_ablation_tuple(dialogue_tuple: Dict[str, Any], tokenizer: Optional[Any] = None) -> Dict[str, Any]:
    """
    Create an ablation variant of a dialogue tuple by replacing the critique
    text with a neutral placeholder of equivalent token length.
    
    Args:
        dialogue_tuple: A dictionary containing 'question', 'initial_answer', 
                        'critique', and 'revised_answer'.
        tokenizer: Optional tokenizer for precise token counting.
        
    Returns:
        A new dictionary with 'critique' replaced by 'ablated_critique' (placeholder),
        and 'original_critique' preserved for reference if needed.
    """
    if 'critique' not in dialogue_tuple:
        logger.warning("Input tuple missing 'critique' field. Returning copy.")
        return dialogue_tuple.copy()
    
    original_critique = dialogue_tuple['critique']
    
    # Determine token count of original critique
    token_count = count_tokens(original_critique, tokenizer)
    
    # Generate neutral placeholder
    neutral_text = generate_neutral_placeholder(token_count, original_critique)
    
    # Create the ablated tuple
    ablated_tuple = dialogue_tuple.copy()
    ablated_tuple['original_critique'] = original_critique  # Keep reference
    ablated_tuple['critique'] = neutral_text  # Replace with placeholder
    
    logger.debug(f"Ablated critique: {len(original_critique)} chars -> {len(neutral_text)} chars (approx {token_count} tokens)")
    
    return ablated_tuple


def generate_ablation_dataset(
    input_path: str,
    output_path: str,
    tokenizer: Optional[Any] = None,
    sample_size: Optional[int] = None
) -> int:
    """
    Generate an ablated dataset from a JSONL file of dialogue tuples.
    
    This function reads the input file, processes each record to replace the
    critique with a neutral placeholder, and writes the result to the output path.
    
    Args:
        input_path: Path to the input JSONL file (generated by T014).
        output_path: Path to the output JSONL file for the ablated dataset.
        tokenizer: Optional tokenizer for precise token counting.
        sample_size: Optional limit on the number of records to process.
        
    Returns:
        The number of records processed.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    
    logger.info(f"Starting ablation generation from {input_path} to {output_path}")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
         
         for line_num, line in enumerate(infile, 1):
             if not line.strip():
                 continue
             
             try:
                 record = json.loads(line)
                 ablated_record = create_ablation_tuple(record, tokenizer)
                 outfile.write(json.dumps(ablated_record) + '\n')
                 processed_count += 1
                 
                 if sample_size and processed_count >= sample_size:
                     break
                     
             except json.JSONDecodeError as e:
                 logger.error(f"JSON decode error at line {line_num}: {e}")
                 continue
             except Exception as e:
                 logger.error(f"Error processing line {line_num}: {e}")
                 continue
    
    logger.info(f"Ablation generation complete. Processed {processed_count} records.")
    return processed_count


def main():
    """
    Main entry point for the ablation data generator script.
    Reads the generated dialogue dataset, replaces critiques with neutral placeholders,
    and writes the ablated dataset.
    """
    config = get_config()
    
    # Define paths relative to the project structure
    # Assuming the dialogue generation output is in data/processed/dialogue.jsonl
    input_path = config.data_dir / "processed" / "dialogue.jsonl"
    output_path = config.data_dir / "processed" / "dialogue_ablated.jsonl"
    
    # Allow override via environment variables
    env_input = os.getenv("ABLATION_INPUT_PATH")
    env_output = os.getenv("ABLATION_OUTPUT_PATH")
    
    if env_input:
        input_path = Path(env_input)
    if env_output:
        output_path = Path(env_output)
        
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. "
                     "Please ensure T014 (generate_dialogue.py) has run successfully.")
        sys.exit(1)
        
    logger.info(f"Running ablation generator. Input: {input_path}, Output: {output_path}")
    
    try:
        count = generate_ablation_dataset(str(input_path), str(output_path))
        logger.info(f"Successfully generated {count} ablated records.")
    except Exception as e:
        logger.error(f"Failed to generate ablation dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()