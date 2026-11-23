"""
T001f: Acquire and format the raw conversation dataset.

Fetches the 'convai2' dataset from HuggingFace, extracts the 'text' field,
and saves it as a JSONL file at data/raw/conversations.jsonl.

Constraint: No synthetic data. If the real fetch fails, the script MUST
raise an exception (fail loudly).
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure we can import from the project root if needed, though standard
# imports are sufficient for this standalone script.
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' library is required. Install it via: pip install datasets")
    sys.exit(1)

# Configuration
DATASET_NAME = "convai2"
DATASET_SPLIT = "validation"  # Use validation set to ensure manageable size for initial run
OUTPUT_FILE = Path("data/raw/conversations.jsonl")
TEXT_FIELD = "text"

def setup_output_directory(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def fetch_conversations(dataset_name: str, split: str) -> List[Dict[str, Any]]:
    """
    Fetch the dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace.
        split: The split to load (e.g., 'train', 'validation').
        
    Returns:
        List of conversation dictionaries.
        
    Raises:
        Exception: If the dataset cannot be fetched or loaded.
    """
    print(f"Fetching dataset: {dataset_name} (split: {split})...")
    try:
        # Load the dataset
        # Using streaming=False to ensure we get the full split for processing,
        # though we will iterate carefully.
        dataset = load_dataset(dataset_name, split=split)
        
        # Check if the required field exists
        if TEXT_FIELD not in dataset.column_names:
            available_cols = ", ".join(dataset.column_names)
            raise ValueError(
                f"Field '{TEXT_FIELD}' not found in dataset columns. "
                f"Available columns: {available_cols}"
            )
        
        conversations = []
        total_rows = len(dataset)
        print(f"Dataset loaded. Total rows: {total_rows}")
        
        for i, row in enumerate(dataset):
            # Extract the text content
            text_content = row.get(TEXT_FIELD, "")
            if text_content and isinstance(text_content, str) and len(text_content.strip()) > 0:
                conversations.append({
                    "conversation_id": f"conv_{i}",
                    "text_content": text_content.strip()
                })
            
            # Progress logging every 1000 items
            if (i + 1) % 1000 == 0:
                print(f"  Processed {i + 1}/{total_rows} rows...")
        
        print(f"Successfully extracted {len(conversations)} valid conversations.")
        return conversations
        
    except Exception as e:
        # Fail loudly: do not catch and return empty or synthetic data
        raise RuntimeError(f"Failed to fetch or process dataset '{dataset_name}': {e}") from e

def save_conversations_jsonl(conversations: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save conversations to a JSONL file.
    
    Args:
        conversations: List of conversation dictionaries.
        output_path: Path to the output file.
    """
    print(f"Saving {len(conversations)} conversations to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for conv in conversations:
            json.dump(conv, f, ensure_ascii=False)
            f.write('\n')
    print(f"Saved successfully to {output_path}")

def main():
    """Main entry point for T001f."""
    print("Starting T001f: Acquire and format raw conversation dataset.")
    
    # Setup
    setup_output_directory(OUTPUT_FILE)
    
    # Fetch
    try:
        conversations = fetch_conversations(DATASET_NAME, DATASET_SPLIT)
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        sys.exit(1)
        
    if not conversations:
        # Fail loudly if no data was extracted
        raise RuntimeError("No valid conversations were extracted from the dataset.")
    
    # Save
    save_conversations_jsonl(conversations, OUTPUT_FILE)
    
    print("T001f completed successfully.")

if __name__ == "__main__":
    main()