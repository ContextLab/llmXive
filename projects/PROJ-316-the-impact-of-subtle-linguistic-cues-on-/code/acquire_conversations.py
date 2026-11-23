import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Attempt to import datasets; if missing, the script will fail loudly as per constraints
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' library is required. Install it via: pip install datasets")
    sys.exit(1)

def setup_output_directory(output_path: Path) -> None:
    """Ensure the output directory exists."""
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {output_path}")

def fetch_conversations() -> List[Dict[str, Any]]:
    """
    Fetches conversation data from HuggingFace datasets.
    Priority:
    1. convai2 (checked first)
    2. cornell-movie-dialogs (fallback if convai2 fails or is empty)

    Returns a list of dictionaries containing the 'text' or 'dialogue' fields.
    """
    print("Attempting to fetch 'convai2' dataset...")
    try:
        # Load convai2 dataset (splits: train, validation, test)
        # We select the 'validation' split for a manageable size, or 'train' if validation is too small
        ds = load_dataset("convai2", split="validation", trust_remote_code=True)
        if len(ds) > 0:
            print(f"Successfully loaded {len(ds)} conversations from 'convai2'.")
            return ds
    except Exception as e:
        print(f"Failed to load 'convai2': {e}")

    print("Attempting to fetch 'cornell-movie-dialogs' dataset as fallback...")
    try:
        # Load Cornell Movie-Dialogs Corpus
        # The dataset name might vary; trying common variants
        ds = load_dataset("Cornell_MovieDialogue_Corpus", split="train", trust_remote_code=True)
        if len(ds) > 0:
            print(f"Successfully loaded {len(ds)} conversations from 'Cornell_MovieDialogue_Corpus'.")
            return ds
    except Exception as e:
        print(f"Failed to load 'Cornell_MovieDialogue_Corpus': {e}")

    # If all attempts fail, raise an error to prevent silent failure
    raise RuntimeError(
        "CRITICAL: Could not fetch any conversation dataset from HuggingFace. "
        "Both 'convai2' and 'cornell-movie-dialogs' attempts failed. "
        "The pipeline requires real data and cannot proceed without it."
    )

def save_conversations_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the conversation data to a JSONL file.
    Extracts 'text' or 'dialogue' fields. If neither exists, stores the whole record.
    """
    records = []
    processed_count = 0

    for idx, item in enumerate(data):
        record = {}
        # Assign a unique ID
        record['conversation_id'] = f"conv_{idx:06d}"

        # Extract text content
        text_content = None
        if 'text' in item:
            text_content = str(item['text'])
        elif 'dialogue' in item:
            text_content = str(item['dialogue'])
        elif 'utterance' in item:
            text_content = str(item['utterance'])
        elif 'context' in item and 'response' in item:
            # Some datasets have context/response split
            text_content = f"{item['context']} {item['response']}"
        
        if text_content is not None:
            record['text_content'] = text_content
            # Explicitly note that authenticity_score is MISSING (expected for raw fetch)
            # We do NOT set it to None or 0 to avoid confusion with real ratings later.
            # The downstream T001g will detect the absence of this key.
            records.append(record)
            processed_count += 1
        else:
            # If no text field found, skip or log
            if idx < 5:
                print(f"Warning: Item {idx} has no recognizable text field. Keys: {list(item.keys())}")

    print(f"Processed {processed_count} valid conversation records.")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"Saved {len(records)} records to {output_path}")

def main() -> None:
    """
    Main entry point for T001f.
    Fetches data and saves to data/raw/conversations.jsonl.
    """
    # Define paths relative to project root (assuming script is run from project root or code/)
    # The task requires output at data/raw/conversations.jsonl
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "conversations.jsonl"

    print(f"Target output: {output_file}")
    setup_output_directory(output_dir)

    try:
        data = fetch_conversations()
        save_conversations_jsonl(data, output_file)
        
        # Verify the file exists and is not empty
        if output_file.exists() and output_file.stat().st_size > 0:
            print("SUCCESS: Data acquisition complete. File created.")
        else:
            raise RuntimeError("Data acquisition failed: Output file is empty or missing.")
            
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
