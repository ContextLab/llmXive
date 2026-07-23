"""
Annotation Tool CLI for Perceived Authenticity and Hedge Identification.

This tool reads raw conversation data and annotation instructions,
presents turns to a rater, and saves the results to a log file.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import get_seed, set_seed

def load_raw_conversations(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads conversation turns from a JSONL file.

    Args:
        input_path: Path to the JSONL file containing raw conversations.

    Returns:
        List of dictionaries, each representing a conversation turn.
    """
    turns = []
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Ensure required fields exist
                if 'text' not in data and 'text_content' not in data:
                    print(f"Warning: Skipping line {line_num} missing 'text' or 'text_content'.")
                    continue
                turns.append(data)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line {line_num}: {e}")
                continue

    if not turns:
        raise ValueError("No valid conversation turns found in the input file.")

    return turns

def parse_instructions(instructions_path: str) -> str:
    """
    Reads and returns the content of the annotation instructions file.

    Args:
        instructions_path: Path to the markdown instructions file.

    Returns:
        The full text of the instructions.
    """
    path = Path(instructions_path)
    if not path.exists():
        raise FileNotFoundError(f"Instructions file not found: {instructions_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def get_rater_input_authenticity(turn_index: int, total: int) -> int:
    """
    Prompts the user for an authenticity rating (1-5).

    Args:
        turn_index: Current turn number (0-based).
        total: Total number of turns.

    Returns:
        Integer rating from 1 to 5.
    """
    while True:
        try:
            user_input = input(
                f"Turn {turn_index + 1}/{total}\n"
                f"Rate Authenticity (1-5): "
            ).strip()
            rating = int(user_input)
            if 1 <= rating <= 5:
                return rating
            else:
                print("Error: Please enter a number between 1 and 5.")
        except ValueError:
            print("Error: Invalid input. Please enter an integer.")

def get_rater_input_hedges(turn_index: int, text: str) -> List[int]:
    """
    Prompts the user for hedge indices.

    Args:
        turn_index: Current turn number.
        text: The text of the turn (for reference).

    Returns:
        List of integer indices representing hedge positions.
    """
    # Display text for reference
    print(f"\nText: {text}\n")
    print("Enter hedge word indices (0-based, comma-separated).")
    print("Example: 'I think it is' -> 'think' is index 1. Enter: 1")
    print("If no hedges, enter 0 or leave blank.\n")

    while True:
        try:
            user_input = input("Hedge indices: ").strip()
            if not user_input or user_input == '0':
                return []

            indices = [int(x.strip()) for x in user_input.split(',')]
            # Basic validation: indices should be non-negative
            if any(i < 0 for i in indices):
                print("Error: Indices must be non-negative.")
                continue

            # Optional: check against text length?
            # We trust the rater's count for now, but we could warn if out of bounds.
            words = text.split()
            max_idx = len(words) - 1
            invalid = [i for i in indices if i > max_idx]
            if invalid:
                print(f"Warning: Indices {invalid} exceed text length ({len(words)} words). Proceeding anyway.")

            return indices
        except ValueError:
            print("Error: Invalid input. Please enter comma-separated integers.")

def save_rater_log(log_path: str, rater_id: str, results: List[Dict[str, Any]]) -> None:
    """
    Saves the annotation results to a CSV log file.

    Args:
        log_path: Path to the output CSV file.
        rater_id: Unique identifier for the rater.
        results: List of dictionaries containing turn data and ratings.
    """
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'timestamp', 'rater_id', 'conversation_id', 'text_content',
        'authenticity_score', 'hedge_indices'
    ]

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            row = {
                'timestamp': result['timestamp'],
                'rater_id': rater_id,
                'conversation_id': result['conversation_id'],
                'text_content': result['text_content'],
                'authenticity_score': result['authenticity_score'],
                'hedge_indices': json.dumps(result['hedge_indices'])
            }
            writer.writerow(row)

    print(f"\nAnnotation session complete. Saved {len(results)} entries to {log_path}")

def generate_gold_standard(input_path: str, output_path: str, sample_size: int = 50) -> List[Dict[str, Any]]:
    """
    (Placeholder logic for T001c integration)
    Selects a random sample of turns from the input file for annotation.
    In a real workflow, this would be driven by the task scheduler.
    """
    turns = load_raw_conversations(input_path)
    # Simple random sample without replacement
    import random
    if len(turns) < sample_size:
        sample = turns
    else:
        sample = random.sample(turns, sample_size)
    return sample

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for annotating conversation turns for authenticity and hedges."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to the input JSONL file (raw conversations)."
    )
    parser.add_argument(
        "--instructions", "-ins",
        type=str,
        required=True,
        help="Path to the annotation instructions markdown file."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Path to the output CSV log file."
    )
    parser.add_argument(
        "--rater-id",
        type=str,
        default="rater_001",
        help="Unique identifier for the current rater."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="If provided, only annotate this many randomly sampled turns."
    )

    args = parser.parse_args()

    # 1. Load Instructions
    try:
        instructions = parse_instructions(args.instructions)
        print("--- Annotation Instructions ---")
        print(instructions)
        print("\n--- Press Enter to begin ---")
        input()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 2. Load Data
    try:
        all_turns = load_raw_conversations(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    # 3. Determine turns to annotate
    if args.sample_size:
        print(f"Sampling {args.sample_size} turns from {len(all_turns)} total.")
        import random
        random.seed(get_seed())
        turns_to_annotate = random.sample(all_turns, min(args.sample_size, len(all_turns)))
    else:
        turns_to_annotate = all_turns

    print(f"Starting annotation for {len(turns_to_annotate)} turns.")

    # 4. Interactive Loop
    results = []
    for idx, turn in enumerate(turns_to_annotate):
        # Extract text
        text = turn.get('text', turn.get('text_content', ''))
        conv_id = turn.get('conversation_id', f"turn_{idx}")

        # Get Ratings
        auth_score = get_rater_input_authenticity(idx, len(turns_to_annotate))
        hedge_indices = get_rater_input_hedges(idx, text)

        # Record
        results.append({
            'timestamp': datetime.now().isoformat(),
            'conversation_id': conv_id,
            'text_content': text,
            'authenticity_score': auth_score,
            'hedge_indices': hedge_indices
        })

        print("-" * 20)

    # 5. Save Results
    save_rater_log(args.output, args.rater_id, results)

if __name__ == "__main__":
    main()
