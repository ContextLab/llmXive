"""
Annotation Tool for Perceived Authenticity and Hedge Identification.

This CLI tool allows raters to input scores for a list of turns based on
instructions provided in `data/raw/annotation_instructions.md`.
It supports two modes:
1. `authenticity`: Rate perceived authenticity on a 1-5 Likert scale.
2. `hedges`: Identify indices of words that function as uncertainty markers.

Output is saved as intermediate rater logs in `data/processed/rater_logs/`.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure we can import from the project root if run as a module
# But primarily designed to be run as a script from the project root
# or via `python -m src.utils.annotation_tool`

def load_raw_conversations(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load raw conversations from a JSONL file.

    Args:
        filepath: Path to the JSONL file.

    Returns:
        List of dictionaries containing conversation data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Conversations file not found: {filepath}")

    conversations = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                conversations.append(data)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Invalid JSON at line {line_num}", e.doc, e.pos)

    return conversations

def parse_instructions(filepath: Path) -> Dict[str, Any]:
    """
    Parse the annotation instructions file to extract key definitions.

    This is a simple parser that looks for specific sections in the markdown
    file. It does not need to be a full Markdown parser, just extract the
    Likert scale definitions and any specific hedge examples.

    Args:
        filepath: Path to the annotation instructions markdown file.

    Returns:
        Dictionary containing parsed instruction data.

    Raises:
        FileNotFoundError: If the instructions file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Instructions file not found: {filepath}")

    instructions = {
        "raw_content": "",
        "likert_scale": {},
        "hedge_examples": []
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        instructions["raw_content"] = content

        # Simple heuristic parsing for Likert scale
        # Looking for patterns like "1: Not Authentic" or "1 - Not Authentic"
        lines = content.split('\n')
        in_scale_section = False
        for line in lines:
            line = line.strip()
            if 'Likert' in line or 'Scale' in line:
                in_scale_section = True
                continue
            if in_scale_section:
                if line.startswith('#') or (line and not line[0].isdigit() and not line[0] == '-'):
                    if not line.startswith('1') and not line.startswith('2') and not line.startswith('3') and not line.startswith('4') and not line.startswith('5'):
                        # End of scale section if we hit a new header or unrelated text
                        # But keep looking for specific patterns
                        pass
                # Try to match "N: Description" or "N - Description"
                parts = line.replace('-', ':').split(':')
                if len(parts) >= 2 and parts[0].strip().isdigit():
                    try:
                        key = int(parts[0].strip())
                        val = ':'.join(parts[1:]).strip()
                        instructions["likert_scale"][key] = val
                    except ValueError:
                        pass

        # Heuristic for hedge examples if needed, but for now just return raw content
        # The tool will display the raw content to the rater to ensure they read it.

    return instructions

def get_rater_input_authenticity(
    item: Dict[str, Any],
    rater_id: str,
    instructions: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Interactively prompt the rater for an authenticity score.

    Args:
        item: The conversation turn data.
        rater_id: Unique identifier for the rater.
        instructions: Parsed instructions to display.

    Returns:
        Dictionary with rating data, or None if skipped.
    """
    print("\n" + "="*60)
    print(f"Rater: {rater_id}")
    print("="*60)

    # Display instructions summary if available
    if instructions.get("likert_scale"):
        print("\n--- Likert Scale Definitions ---")
        for k, v in sorted(instructions["likert_scale"].items()):
            print(f"{k}: {v}")
        print("-" * 30)

    # Display the text to rate
    text_content = item.get('text', item.get('text_content', 'N/A'))
    conv_id = item.get('conversation_id', item.get('id', 'unknown'))

    print(f"\nConversation ID: {conv_id}")
    print(f"Text:\n{text_content}\n")

    while True:
        try:
            response = input("Enter authenticity score (1-5) or 'q' to quit: ").strip()
            if response.lower() == 'q':
                return None
            score = int(response)
            if 1 <= score <= 5:
                return {
                    "conversation_id": conv_id,
                    "text_content": text_content,
                    "authenticity_score": score,
                    "rater_id": rater_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_rater_input_hedges(
    item: Dict[str, Any],
    rater_id: str,
    instructions: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Interactively prompt the rater to identify hedge word indices.

    Args:
        item: The conversation turn data.
        rater_id: Unique identifier for the rater.
        instructions: Parsed instructions to display.

    Returns:
        Dictionary with hedge flags, or None if skipped.
    """
    print("\n" + "="*60)
    print(f"Rater: {rater_id} - Hedge Identification")
    print("="*60)

    text_content = item.get('text', item.get('text_content', 'N/A'))
    conv_id = item.get('conversation_id', item.get('id', 'unknown'))

    # Tokenize simply by splitting on whitespace for index mapping
    # This assumes the rater can identify words by position visually or by copy-paste
    # A more robust tool might highlight words, but for CLI we provide indices.
    tokens = text_content.split()

    print(f"\nConversation ID: {conv_id}")
    print(f"Text: {text_content}")
    print("\nWord Indices (0-based):")
    for i, word in enumerate(tokens):
        print(f"[{i}] {word}")
    print("-" * 30)
    print("Enter indices of words that are uncertainty markers (hedges), separated by spaces.")
    print("Example: '3 7 12' means words at index 3, 7, and 12 are hedges.")
    print("Enter 'q' to quit, 'skip' to skip this item.")

    while True:
        try:
            response = input("Indices: ").strip()
            if response.lower() == 'q':
                return None
            if response.lower() == 'skip':
                return {
                    "conversation_id": conv_id,
                    "text_content": text_content,
                    "hedge_flags": [],
                    "rater_id": rater_id,
                    "timestamp": datetime.now().isoformat(),
                    "skipped": True
                }

            indices = []
            if response:
                parts = response.split()
                for p in parts:
                    idx = int(p)
                    if 0 <= idx < len(tokens):
                        indices.append(idx)
                    else:
                        print(f"Warning: Index {idx} out of range (0-{len(tokens)-1}). Ignoring.")

            return {
                "conversation_id": conv_id,
                "text_content": text_content,
                "hedge_flags": indices,
                "rater_id": rater_id,
                "timestamp": datetime.now().isoformat()
            }
        except ValueError:
            print("Invalid input. Please enter space-separated integers.")

def save_rater_log(
    logs: List[Dict[str, Any]],
    output_dir: Path,
    mode: str,
    rater_id: str
) -> Path:
    """
    Save rater logs to a CSV file.

    Args:
        logs: List of rating dictionaries.
        output_dir: Directory to save the log.
        mode: 'authenticity' or 'hedges'.
        rater_id: ID of the rater.

    Returns:
        Path to the saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rater_{rater_id}_{mode}_{timestamp}.csv"
    filepath = output_dir / filename

    if not logs:
        # Create empty file with headers
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["conversation_id", "text_content", "rater_id", "timestamp"])
            writer.writeheader()
        return filepath

    # Determine fieldnames dynamically based on the first log entry
    fieldnames = ["conversation_id", "text_content", "rater_id", "timestamp"]
    if mode == "authenticity":
        fieldnames.append("authenticity_score")
    elif mode == "hedges":
        fieldnames.append("hedge_flags")
        # Handle skipped items if any
        if any(log.get("skipped") for log in logs):
            fieldnames.append("skipped")

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log in logs:
            # Ensure hedge_flags are stored as a string representation for CSV
            if "hedge_flags" in log:
                log["hedge_flags"] = json.dumps(log["hedge_flags"])
            writer.writerow(log)

    return filepath

def generate_gold_standard(
    logs: List[Dict[str, Any]],
    mode: str
) -> List[Dict[str, Any]]:
    """
    Aggregate logs into a gold standard format (simplified for single rater or initial pass).
    In a multi-rater scenario, this would aggregate scores (mean) and flags (consensus).
    For this CLI tool, it primarily formats the data for downstream processing.

    Args:
        logs: List of rating dictionaries.
        mode: 'authenticity' or 'hedges'.

    Returns:
        List of standardized dictionaries.
    """
    gold_standard = []
    for log in logs:
        if log.get("skipped"):
            continue

        entry = {
            "conversation_id": log["conversation_id"],
            "text_content": log["text_content"],
            "rater_id": log["rater_id"],
            "timestamp": log["timestamp"]
        }

        if mode == "authenticity":
            entry["authenticity_score"] = log["authenticity_score"]
        elif mode == "hedges":
            # Parse back from string if saved as string
            flags = log["hedge_flags"]
            if isinstance(flags, str):
                flags = json.loads(flags)
            entry["hedge_flags"] = flags

        gold_standard.append(entry)

    return gold_standard

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for annotating conversation turns for authenticity and hedges."
    )
    parser.add_argument(
        "--conversations",
        type=Path,
        default=Path("data/raw/conversations.jsonl"),
        help="Path to the raw conversations JSONL file."
    )
    parser.add_argument(
        "--instructions",
        type=Path,
        default=Path("data/raw/annotation_instructions.md"),
        help="Path to the annotation instructions markdown file."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/rater_logs"),
        help="Directory to save rater logs."
    )
    parser.add_argument(
        "--rater-id",
        type=str,
        default="rater_01",
        help="Unique identifier for the current rater."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["authenticity", "hedges"],
        default="authenticity",
        help="Annotation mode: 'authenticity' for Likert scoring, 'hedges' for word identification."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of items to annotate (for testing or partial runs)."
    )

    args = parser.parse_args()

    # Load instructions
    try:
        instructions = parse_instructions(args.instructions)
        print(f"Loaded instructions from {args.instructions}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Load conversations
    try:
        conversations = load_raw_conversations(args.conversations)
        print(f"Loaded {len(conversations)} conversations from {args.conversations}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading conversations: {e}")
        sys.exit(1)

    if args.limit:
        conversations = conversations[:args.limit]
        print(f"Limiting to {args.limit} items.")

    logs = []
    total = len(conversations)
    print(f"Starting annotation session. Mode: {args.mode}, Rater: {args.rater_id}")

    for i, item in enumerate(conversations):
        print(f"\nProcessing item {i+1}/{total}...")
        if args.mode == "authenticity":
            result = get_rater_input_authenticity(item, args.rater_id, instructions)
        elif args.mode == "hedges":
            result = get_rater_input_hedges(item, args.rater_id, instructions)
        else:
            raise ValueError(f"Unknown mode: {args.mode}")

        if result is None:
            print("Session terminated by user.")
            break

        logs.append(result)
        print("Saved.")

    if logs:
        output_path = save_rater_log(logs, args.output_dir, args.mode, args.rater_id)
        print(f"\nAnnotation session complete. Logs saved to: {output_path}")

        # Optionally generate a gold standard preview
        gold = generate_gold_standard(logs, args.mode)
        print(f"Generated {len(gold)} gold standard entries.")
    else:
        print("\nNo annotations recorded.")

if __name__ == "__main__":
    main()
