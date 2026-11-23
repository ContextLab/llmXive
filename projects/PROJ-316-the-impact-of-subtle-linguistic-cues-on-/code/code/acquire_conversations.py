import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' package is required. Please install it via: pip install datasets")
    sys.exit(1)

def setup_output_directory(output_path: Path) -> None:
    """Creates the output directory if it does not exist."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not output_path.exists():
        output_path.touch()

def fetch_conversations(dataset_name: str = "convai2", split: str = "train") -> List[Dict[str, Any]]:
    """
    Fetches conversations from a HuggingFace dataset.
    Attempts to extract text content from common fields: 'text', 'dialogue', 'utterances'.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace (e.g., 'convai2').
        split: The dataset split to load (default: 'train').
        
    Returns:
        A list of dictionaries, each containing a 'conversation_id' and 'text_content'.
        
    Raises:
        RuntimeError: If the dataset cannot be found or no text fields are detected.
    """
    print(f"Fetching dataset: {dataset_name} (split: {split})...")
    try:
        dataset = load_dataset(dataset_name, split=split, streaming=False)
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset '{dataset_name}': {e}")

    conversations = []
    conversation_id = 0

    # Attempt to identify the text field
    # Common fields in dialogue datasets: 'text', 'dialogue', 'utterances', 'messages'
    # We will iterate and try to find a suitable field dynamically
    sample_item = dataset[0]
    potential_text_fields = ['text', 'dialogue', 'utterances', 'messages', 'conversation']
    
    text_field = None
    for field in potential_text_fields:
        if field in sample_item:
            text_field = field
            break
    
    # If not found in common fields, look for any string field that isn't an ID
    if text_field is None:
        for key, value in sample_item.items():
            if isinstance(value, str) and key not in ['id', 'conversation_id', 'speaker_id']:
                text_field = key
                break

    if text_field is None:
        # Fallback: try to construct text from 'dialogue' if it's a list of turns
        # This is common in convai2 where the text might be a formatted string or a list
        if 'dialogue' in sample_item and isinstance(sample_item['dialogue'], list):
            text_field = 'dialogue'
        elif 'text' in sample_item:
            text_field = 'text'
        else:
            raise RuntimeError(f"Could not identify a text field in dataset '{dataset_name}'. Available keys: {list(sample_item.keys())}")

    print(f"Identified text field: '{text_field}'")

    for idx, item in enumerate(dataset):
        raw_text = item.get(text_field, "")
        
        # Handle different data types for text
        if isinstance(raw_text, list):
            # Join list items (e.g., turns) into a single string
            # Sometimes lists contain dicts like {'role': 'user', 'content': '...'}
            processed_text = []
            for turn in raw_text:
                if isinstance(turn, dict):
                    processed_text.append(turn.get('content', turn.get('text', str(turn))))
                else:
                    processed_text.append(str(turn))
            final_text = " ".join(processed_text)
        elif isinstance(raw_text, str):
            final_text = raw_text
        else:
            final_text = str(raw_text)

        if final_text.strip():
            conversations.append({
                "conversation_id": f"{dataset_name}_{conversation_id}",
                "text_content": final_text
            })
            conversation_id += 1
        
        # Limit to first 10,000 for initial run if dataset is massive, 
        # but tasks.md implies we need the raw dataset. 
        # We will process the full split unless memory error occurs (handled by runner).
        # To be safe with memory on large splits, we can stream if needed, 
        # but load_dataset(..., streaming=False) loads into memory.
        # Given the task is "Acquire raw dataset", we assume the runner has capacity.

    print(f"Successfully extracted {len(conversations)} conversations.")
    return conversations

def save_conversations_jsonl(conversations: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the list of conversations to a JSONL file.
    
    Args:
        conversations: List of conversation dictionaries.
        output_path: Path to the output .jsonl file.
    """
    if not conversations:
        raise ValueError("No conversations to save.")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for conv in conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + '\n')
    print(f"Saved {len(conversations)} conversations to {output_path}")

def main():
    """Main entry point for the script."""
    # Define paths relative to project root
    # The task requires output at data/raw/conversations.jsonl
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "conversations.jsonl"

    setup_output_directory(output_file)

    # Try 'convai2' first as suggested in tasks.md
    # If that fails or is too small, we could fallback to 'cornell-movie-dialogs'
    # but tasks.md says "Fetch the 'convai2' or 'cornell-movie-dialogs'".
    # We will try convai2 first.
    dataset_name = "convai2"
    
    try:
        conversations = fetch_conversations(dataset_name, split="train")
        if not conversations:
            # Fallback if convai2 is empty or problematic
            print(f"No data found in {dataset_name}. Trying cornell-movie-dialogs...")
            dataset_name = "cornell-movie-dialogs"
            conversations = fetch_conversations(dataset_name, split="train")
        
        if not conversations:
            raise RuntimeError("Could not fetch data from either convai2 or cornell-movie-dialogs.")

        save_conversations_jsonl(conversations, output_file)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
