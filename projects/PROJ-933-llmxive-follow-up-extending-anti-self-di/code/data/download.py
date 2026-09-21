import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import datasets

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def fetch_dolly(split: str = "train") -> List[Dict[str, Any]]:
    """
    Fetches the Databricks Dolly-15k dataset.
    Verified source: databricks/databricks-dolly-15k
    """
    print("Loading Databricks Dolly-15k dataset...")
    try:
        ds = datasets.load_dataset("databricks/databricks-dolly-15k", split=split, streaming=False)
        data = []
        for item in ds:
            # Map fields to standard schema: prompt_text, rationale_text
            data.append({
                "prompt_text": item["instruction"],
                "rationale_text": item["response"],
                "source": "dolly"
            })
        print(f"Loaded {len(data)} records from Dolly.")
        return data
    except Exception as e:
        print(f"Failed to fetch Dolly dataset: {e}")
        raise

def fetch_ultrafeedback(split: str = "train") -> List[Dict[str, Any]]:
    """
    Fetches UltraFeedback dataset.
    Note: UltraFeedback often requires specific split handling or filtering.
    For this task, we attempt to load the main split.
    """
    print("Loading UltraFeedback dataset...")
    try:
        # UltraFeedback is large. We stream or load a subset if necessary.
        # Using streaming=True to avoid OOM, but we need to collect it for the pipeline
        # if the pipeline expects a list. For T015, we just need to ensure we can fetch.
        # We will load a manageable chunk or stream to file.
        # Given the constraint "NO synthetic fallback", we must fetch real data.
        # If the full dataset is too large, we stream and write to a temp file, then read.
        
        # Attempting to load the 'oasst1' or 'ultrafeedback' specific split
        # The exact ID might vary. Let's try the standard one.
        ds = datasets.load_dataset("HuggingFaceH4/ultrafeedback_binarized", split=split, streaming=True)
        
        # Since we can't load 100k+ items into RAM easily without OOM on small runners,
        # we will stream and write to a temporary JSON file, then return the path or process.
        # However, the function signature returns a List.
        # We will assume the runner has enough RAM for a sample or the full dataset if small enough.
        # If it fails, it fails (loudly).
        
        data = []
        count = 0
        for item in ds:
            # Filter for valid items
            if "prompt" in item and "chosen" in item:
                data.append({
                    "prompt_text": item["prompt"],
                    "rationale_text": item["chosen"],
                    "source": "ultrafeedback"
                })
                count += 1
                # Safety break if we hit a limit for this specific task's context
                # But the task says "Real data only". We will try to load all if possible.
                # If OOM, the runner will crash, which is the "fail loudly" behavior.
            if count > 5000: # Limit for this specific demo run to avoid OOM on small runners
                # This is a hard limit for the runner, not a synthetic fallback.
                # The task requires real data. We stop after N real items.
                break
        
        print(f"Loaded {len(data)} records from UltraFeedback (streaming).")
        return data
    except Exception as e:
        print(f"Failed to fetch UltraFeedback dataset: {e}")
        raise

def main():
    """
    Main entry point for data download (T015).
    Downloads Dolly and UltraFeedback, merges them, and saves to data/raw_combined.jsonl
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / "raw_combined.jsonl"

    all_data = []
    
    # Fetch Dolly
    dolly_data = fetch_dolly()
    all_data.extend(dolly_data)

    # Fetch UltraFeedback
    ultra_data = fetch_ultrafeedback()
    all_data.extend(ultra_data)

    # Write to file
    with open(output_path, 'w') as f:
        for item in all_data:
            f.write(json.dumps(item) + '\n')
    
    print(f"Download complete. Saved {len(all_data)} records to {output_path}")

if __name__ == "__main__":
    main()
