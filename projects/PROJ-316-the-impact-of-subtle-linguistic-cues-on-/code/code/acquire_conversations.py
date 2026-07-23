"""
Acquire and format the raw conversation dataset for T001f.
Fetches the 'convai2' dataset from HuggingFace, extracts dialogue text,
and saves it as data/raw/conversations.jsonl.
"""
import json
import os
import sys
from pathlib import Path

# Ensure we can import from the project root if needed, though standard lib is sufficient here
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' library is required. Install it via: pip install datasets")
    sys.exit(1)

def setup_output_directory(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not output_path.parent.exists():
        raise FileNotFoundError(f"Failed to create directory: {output_path.parent}")

def fetch_conversations(dataset_name: str = "convai2", split: str = "train") -> list:
    """
    Fetch the convai2 dataset from HuggingFace.
    Returns a list of dictionaries containing the dialogue text.
    """
    print(f"Loading dataset: {dataset_name} (split: {split})...")
    try:
        # Load the dataset. The 'convai2' dataset has 'dialogue' or 'text' fields.
        # We stream to avoid loading everything into memory at once if possible,
        # but for this specific task we need to iterate and save.
        dataset = load_dataset(dataset_name, split=split, trust_remote_code=True)
        
        conversations = []
        count = 0
        
        # Iterate through the dataset
        for item in dataset:
            # The convai2 dataset structure varies by version, but typically has 'dialogue'
            # or 'text' or 'speaker_utterance' fields.
            # We look for a field that contains the full dialogue or a turn.
            # Based on standard convai2 HF repo: it has 'dialogue' which is a list of strings,
            # or 'text' which is the full conversation.
            
            dialogue_text = None
            
            if 'dialogue' in item and isinstance(item['dialogue'], list):
                # Join the list of utterances into a single text block for feature extraction
                dialogue_text = " ".join(item['dialogue'])
            elif 'text' in item and isinstance(item['text'], str):
                dialogue_text = item['text']
            elif 'utterances' in item and isinstance(item['utterances'], list):
                dialogue_text = " ".join(item['utterances'])
            
            if dialogue_text and len(dialogue_text.strip()) > 0:
                conversations.append({
                    "conversation_id": f"conv_{count}",
                    "text_content": dialogue_text.strip()
                })
                count += 1
                
                # Log progress every 10k rows
                if count % 10000 == 0:
                    print(f"  Processed {count} conversations...")

        print(f"Successfully fetched {count} conversations.")
        return conversations
        
    except Exception as e:
        print(f"ERROR: Failed to fetch dataset '{dataset_name}': {e}")
        raise

def save_conversations_jsonl(conversations: list, output_path: Path) -> None:
    """
    Save the list of conversations to a JSONL file.
    """
    print(f"Saving {len(conversations)} conversations to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for conv in conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + '\n')
    print(f"Saved successfully to {output_path}")

def main():
    """Main entry point for T001f."""
    # Define paths relative to project root
    # Assuming the script is run from the project root or code/ directory
    # We use a robust path resolution relative to the script location or project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent if script_dir.name == 'code' else script_dir.parent
    
    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "conversations.jsonl"
    
    setup_output_directory(output_file)
    
    # Fetch the dataset
    # We use 'convai2' as the primary source. If it fails, we could try 'cornell_movie_dialogs'
    # but the task specifies 'convai2' or 'cornell'. We start with convai2.
    try:
        conversations = fetch_conversations(dataset_name="convai2", split="train")
    except Exception:
        print("Attempting fallback to cornell_movie_dialogs...")
        try:
            conversations = fetch_conversations(dataset_name="cornell_movie_dialogs", split="train")
        except Exception as e2:
            print(f"CRITICAL: Both primary and fallback datasets failed. Cannot proceed without real data.")
            raise e2

    if not conversations:
        raise ValueError("No conversations were extracted from the dataset.")

    # Save to JSONL
    save_conversations_jsonl(conversations, output_file)
    
    print("T001f completed successfully.")

if __name__ == "__main__":
    main()
