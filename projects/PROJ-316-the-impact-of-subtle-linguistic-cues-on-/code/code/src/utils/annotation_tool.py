"""
Annotation Tool for Human Hedge Labeling (T001e) and Authenticity Rating (T001c).

This module implements the CLI tool required by T002 and used by T001c/T001e.
It loads raw conversations, parses instructions, collects rater input for
authenticity scores and hedge indices, and generates the gold standard CSVs.

The tool is designed to be run interactively. It reads instructions from
`data/raw/annotation_instructions.md` and raw data from `data/raw/conversations.jsonl`.
It outputs `data/processed/gold_standard_50.csv` (authenticity) and
`data/processed/gold_standard_hedges.csv` (hedge flags).
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure imports work whether run as module or script in project context
try:
    from code.src.config import get_seed, set_seed
except ImportError:
    # Fallback for direct execution context if src is not in path
    import random
    def get_seed():
        return 42
    def set_seed(s):
        random.seed(s)


def load_raw_conversations(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw conversations from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of conversation dictionaries.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw conversations file not found: {file_path}")
    
    conversations = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                conversations.append(data)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Invalid JSON at line {line_num}: {e.msg}", e.doc, e.pos)
    
    return conversations


def parse_instructions(file_path: Path) -> str:
    """
    Read and return the annotation instructions content.
    
    Args:
        file_path: Path to the instructions markdown file.
        
    Returns:
        String content of the instructions.
        
    Raises:
        FileNotFoundError: If the instructions file is missing.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Annotation instructions not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_rater_input_authenticity(turn_text: str, turn_id: int, instructions: str) -> int:
    """
    Prompt the rater for an authenticity score (1-5) for a specific turn.
    
    Args:
        turn_text: The text content of the turn.
        turn_id: Unique identifier for the turn.
        instructions: The full instruction text (displayed for context).
        
    Returns:
        Integer score from 1 to 5.
    """
    print("\n" + "="*60)
    print(f"Turn ID: {turn_id}")
    print("-" * 60)
    print(f"Text:\n{turn_text}")
    print("-" * 60)
    print("INSTRUCTIONS:")
    print(instructions)
    print("-" * 60)
    print("Please rate the PERCEIVED AUTHENTICITY of this turn.")
    print("Scale: 1 (Not Authentic) to 5 (Very Authentic)")
    
    while True:
        try:
            user_input = input("Enter score (1-5): ").strip()
            score = int(user_input)
            if 1 <= score <= 5:
                return score
            else:
                print("Error: Score must be between 1 and 5.")
        except ValueError:
            print("Error: Please enter a valid integer.")


def get_rater_input_hedges(turn_text: str, turn_id: int, instructions: str) -> List[int]:
    """
    Prompt the rater to identify hedge word indices in a specific turn.
    
    The user is asked to provide space-separated word indices (0-based)
    where they identify uncertainty markers/hedges.
    
    Args:
        turn_text: The text content of the turn.
        turn_id: Unique identifier for the turn.
        instructions: The full instruction text.
        
    Returns:
        List of integer indices representing hedge positions.
    """
    print("\n" + "="*60)
    print(f"Turn ID: {turn_id} (Hedge Identification)")
    print("-" * 60)
    print(f"Text:\n{turn_text}")
    print("-" * 60)
    # Tokenize simply by whitespace for indexing display
    tokens = turn_text.split()
    print("Word Indices (0-based):")
    for i, token in enumerate(tokens):
        print(f"[{i}] {token}", end="  ")
        if (i + 1) % 10 == 0:
            print() # Newline every 10 tokens
    print()
    print("-" * 60)
    print("Please identify indices of 'uncertainty markers' or 'hedges'.")
    print("Example: 'maybe' is at index 0, 'think' at index 5.")
    print("Enter space-separated indices (e.g., '0 5 12'). Enter 'none' if no hedges.")
    
    while True:
        user_input = input("Indices: ").strip().lower()
        if user_input == 'none' or user_input == '':
            return []
        
        try:
            indices = [int(x) for x in user_input.split()]
            # Validate indices are within bounds
            max_idx = len(tokens) - 1
            valid = True
            for idx in indices:
                if idx < 0 or idx > max_idx:
                    print(f"Error: Index {idx} is out of bounds (0-{max_idx}).")
                    valid = False
                    break
            if valid:
                return sorted(list(set(indices))) # Remove duplicates and sort
        except ValueError:
            print("Error: Please enter valid integers separated by spaces.")


def save_rater_log(log_path: Path, rater_id: str, ratings: List[Dict[str, Any]], hedges: List[Dict[str, Any]]) -> None:
    """
    Save the intermediate rater logs to a JSON file for auditability.
    
    Args:
        log_path: Path to the output log file.
        rater_id: Unique identifier for the rater.
        ratings: List of authenticity rating records.
        hedges: List of hedge identification records.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_data = {
        "rater_id": rater_id,
        "timestamp": datetime.now().isoformat(),
        "ratings": ratings,
        "hedges": hedges
    }
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    print(f"\nRater log saved to: {log_path}")


def generate_gold_standard(ratings: List[Dict[str, Any]], hedges: List[Dict[str, Any]], 
                           output_auth_path: Path, output_hedge_path: Path) -> None:
    """
    Aggregate rater logs into the final Gold Standard CSV files.
    
    For this implementation (single rater pass for T001c/T001e), we assume
    the input lists are the finalized set of 50 items.
    
    Args:
        ratings: List of dicts with conversation_id, text_content, authenticity_score.
        hedges: List of dicts with conversation_id, text_content, hedge_flags.
        output_auth_path: Path for the authenticity CSV.
        output_hedge_path: Path for the hedge CSV.
    """
    # Ensure output directories exist
    output_auth_path.parent.mkdir(parents=True, exist_ok=True)
    output_hedge_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write Authenticity Gold Standard
    auth_headers = ["conversation_id", "text_content", "authenticity_score", "rater_id", "timestamp"]
    with open(output_auth_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=auth_headers)
        writer.writeheader()
        for item in ratings:
            writer.writerow({
                "conversation_id": item.get("conversation_id", ""),
                "text_content": item.get("text_content", ""),
                "authenticity_score": item.get("authenticity_score", ""),
                "rater_id": item.get("rater_id", ""),
                "timestamp": item.get("timestamp", "")
            })
    print(f"Authenticity Gold Standard saved to: {output_auth_path}")
    
    # Write Hedge Gold Standard
    hedge_headers = ["conversation_id", "text_content", "hedge_flags"]
    with open(output_hedge_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=hedge_headers)
        writer.writeheader()
        for item in hedges:
            # Convert list to JSON string for CSV cell
            hedge_flags_str = json.dumps(item.get("hedge_flags", []))
            writer.writerow({
                "conversation_id": item.get("conversation_id", ""),
                "text_content": item.get("text_content", ""),
                "hedge_flags": hedge_flags_str
            })
    print(f"Hedge Gold Standard saved to: {output_hedge_path}")


def main():
    """
    Main entry point for the annotation tool CLI.
    
    Usage:
      python -m code.src.utils.annotation_tool \
        --instructions data/raw/annotation_instructions.md \
        --conversations data/raw/conversations.jsonl \
        --rater-id RATER_001 \
        --output-dir data/processed
    """
    parser = argparse.ArgumentParser(description="Annotation Tool for Authenticity and Hedge Labeling")
    parser.add_argument("--instructions", type=Path, required=True, 
                        help="Path to annotation_instructions.md")
    parser.add_argument("--conversations", type=Path, required=True, 
                        help="Path to conversations.jsonl")
    parser.add_argument("--rater-id", type=str, required=True, 
                        help="Unique ID for the current rater")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"),
                        help="Directory to save output CSVs and logs")
    parser.add_argument("--sample-size", type=int, default=50,
                        help="Number of turns to annotate (default: 50)")
    
    args = parser.parse_args()
    
    # 1. Load Instructions
    try:
        instructions_text = parse_instructions(args.instructions)
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    
    # 2. Load Conversations
    try:
        all_conversations = load_raw_conversations(args.conversations)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    
    if not all_conversations:
        print("CRITICAL ERROR: No conversations found in the input file.")
        sys.exit(1)
    
    # 3. Sample turns (Random selection with seed for reproducibility)
    set_seed(42) # Fixed seed for the sampling process
    sample_size = min(args.sample_size, len(all_conversations))
    sampled_turns = random.sample(all_conversations, sample_size)
    
    print(f"Loaded {len(all_conversations)} conversations.")
    print(f"Sampling {sample_size} turns for annotation.")
    print(f"Rater ID: {args.rater_id}")
    
    ratings_data = []
    hedges_data = []
    
    # 4. Interactive Annotation Loop
    for idx, turn in enumerate(sampled_turns):
        # Extract text and ID
        # Handle potential variations in JSON structure
        text_content = turn.get("text", turn.get("text_content", turn.get("dialogue", "")))
        conv_id = turn.get("conversation_id", turn.get("id", f"turn_{idx}"))
        
        if not text_content:
            print(f"Skipping turn {idx}: No text content found.")
            continue
        
        # A. Authenticity Rating
        auth_score = get_rater_input_authenticity(text_content, idx, instructions_text)
        
        ratings_data.append({
            "conversation_id": conv_id,
            "text_content": text_content,
            "authenticity_score": auth_score,
            "rater_id": args.rater_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # B. Hedge Identification
        hedge_indices = get_rater_input_hedges(text_content, idx, instructions_text)
        
        hedges_data.append({
            "conversation_id": conv_id,
            "text_content": text_content,
            "hedge_flags": hedge_indices
        })
        
        print(f"Completed turn {idx + 1}/{sample_size}")
    
    # 5. Save Outputs
    log_path = args.output_dir / f"rater_log_{args.rater_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_rater_log(log_path, args.rater_id, ratings_data, hedges_data)
    
    output_auth = args.output_dir / "gold_standard_50.csv"
    output_hedge = args.output_dir / "gold_standard_hedges.csv"
    
    generate_gold_standard(ratings_data, hedges_data, output_auth, output_hedge)
    
    print("\nAnnotation session complete.")


if __name__ == "__main__":
    main()
