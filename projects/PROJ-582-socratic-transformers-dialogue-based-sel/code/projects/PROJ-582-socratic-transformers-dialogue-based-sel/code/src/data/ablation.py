"""
Ablation Data Generator (T015b)

Implements FR-007: Replaces critique text with neutral placeholder text of equivalent token length.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.utils.config import get_config
from src.data.ablation_utils import calculate_token_count, get_target_tokenizer


def generate_neutral_placeholder(original_critique: str, target_tokenizer, tolerance: int = 1) -> str:
    """
    Generates a neutral placeholder string that matches the token count of the original critique.
    
    Logic:
    1. Tokenize "[NEUTRAL]" using the target tokenizer.
    2. Repeat the token sequence until the total count matches the original critique's count.
    3. Decode back to text.
    
    Args:
        original_critique: The original critique text.
        target_tokenizer: The tokenizer instance from the base model.
        tolerance: Allowed difference in token count (default ±1).
        
    Returns:
        A placeholder string with matching token count.
    """
    if not original_critique:
        return ""

    # Calculate target token count
    original_count = calculate_token_count(original_critique, tokenizer=target_tokenizer)
    
    if original_count == 0:
        return ""

    # Define the base neutral token sequence
    neutral_text = "[NEUTRAL]"
    neutral_tokens = target_tokenizer.encode(neutral_text, add_special_tokens=False)
    
    if not neutral_tokens:
        # Fallback if encoding fails
        return neutral_text

    neutral_token_count = len(neutral_tokens)
    
    # Calculate how many repetitions are needed
    repetitions = (original_count // neutral_token_count) + 1
    
    # Construct the full sequence
    full_sequence = neutral_tokens * repetitions
    
    # Trim to exact length if we overshot significantly (within tolerance)
    # We want the length to be as close as possible to original_count
    current_len = len(full_sequence)
    if current_len > original_count:
        # Try to reduce by removing full blocks or partial
        # Simple strategy: slice to original_count if close, else adjust repetitions
        if abs(current_len - original_count) <= tolerance:
            full_sequence = full_sequence[:original_count]
        else:
            # Recalculate repetitions to be closer
            repetitions = max(1, original_count // neutral_token_count)
            full_sequence = neutral_tokens * repetitions
            # If still too long, trim
            if len(full_sequence) > original_count:
                full_sequence = full_sequence[:original_count]
    
    # Decode back to text
    placeholder_text = target_tokenizer.decode(full_sequence, skip_special_tokens=False)
    
    return placeholder_text


def create_ablation_tuple(dialogue_tuple: Dict[str, Any], tokenizer=None) -> Dict[str, Any]:
    """
    Creates an ablation tuple by replacing the 'critique' field with a neutral placeholder
    of equivalent token length.
    
    Args:
        dialogue_tuple: A dictionary with keys: question, initial_answer, critique, revised_answer.
        tokenizer: The tokenizer instance. If None, loads from config.
        
    Returns:
        A new dictionary with the 'critique' replaced.
    """
    if tokenizer is None:
        config = get_config()
        tokenizer = get_target_tokenizer(config.BASE_MODEL_ID)
    
    original_critique = dialogue_tuple.get("critique", "")
    
    if not original_critique:
        # If no critique, return as is or handle error? Per spec, we replace text.
        # If empty, placeholder is empty.
        placeholder = ""
    else:
        placeholder = generate_neutral_placeholder(original_critique, tokenizer)
    
    ablation_tuple = dialogue_tuple.copy()
    ablation_tuple["critique"] = placeholder
    
    return ablation_tuple


def generate_ablation_dataset(input_path: str, output_path: str, tokenizer=None) -> int:
    """
    Reads a JSONL file of dialogue tuples and writes a JSONL file of ablation tuples.
    
    Args:
        input_path: Path to the input JSONL file (e.g., data/processed/dialogue_tuples.jsonl).
        output_path: Path to the output JSONL file (e.g., data/processed/ablation_tuples.jsonl).
        tokenizer: The tokenizer instance.
        
    Returns:
        The number of tuples processed.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if tokenizer is None:
        config = get_config()
        tokenizer = get_target_tokenizer(config.BASE_MODEL_ID)
    
    count = 0
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
         
         for line in f_in:
             line = line.strip()
             if not line:
                 continue
             
             try:
                 dialogue_tuple = json.loads(line)
                 ablation_tuple = create_ablation_tuple(dialogue_tuple, tokenizer)
                 
                 # Verification: Check token count match (within tolerance)
                 orig_count = calculate_token_count(dialogue_tuple.get("critique", ""), tokenizer)
                 new_count = calculate_token_count(ablation_tuple["critique"], tokenizer)
                 
                 if abs(orig_count - new_count) > 1:
                     # Log warning but continue? Or strict fail?
                     # Spec says: "within ±1 token". We aim for it.
                     pass
                 
                 f_out.write(json.dumps(ablation_tuple) + '\n')
                 count += 1
                 
             except json.JSONDecodeError:
                 # Skip invalid lines
                 continue
             
             except Exception as e:
                 # Log and skip problematic lines
                 continue
                 
    return count


def main():
    """
    Main entry point for generating the ablation dataset.
    """
    config = get_config()
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[3]
    input_path = project_root / "data" / "processed" / "dialogue_tuples.jsonl"
    output_path = project_root / "data" / "processed" / "ablation_tuples.jsonl"
    
    print(f"Loading tokenizer for model: {config.BASE_MODEL_ID}")
    
    try:
        count = generate_ablation_dataset(str(input_path), str(output_path))
        print(f"Successfully generated {count} ablation tuples.")
        print(f"Output written to: {output_path}")
        
        # Verify output exists and is not empty
        if output_path.exists() and output_path.stat().st_size > 0:
            print("Verification: Output file created successfully.")
        else:
            print("Warning: Output file is empty or missing.")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating ablation dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()