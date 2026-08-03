"""
T012c: Generate static test fixture from real data (AdvBench/HF4).
Produces data/test_static_logs.json with log_id, text, and label columns.
"""
import json
import os
import sys
import hashlib
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from config import get_path, ensure_directories


def fetch_advbench_sample(n_samples: int = 500) -> List[Dict[str, Any]]:
    """
    Fetch a sample of jailbreak logs from AdvBench.
    Returns list of dicts with 'text' and 'label'='novel'.
    """
    try:
        # Load AdvBench dataset
        # AdvBench typically has 'prompt' and 'goal' columns, but we look for the standard structure
        # The dataset 'llm-attack/advbench' or similar. We will use the standard HuggingFace path.
        # Using streaming to avoid loading full dataset into memory if not needed, though sample is small.
        dataset = load_dataset("llm-attack/advbench", split="train", streaming=True)
        
        samples = []
        count = 0
        for item in dataset:
            if count >= n_samples:
                break
            # AdvBench usually has 'goal' as the attack prompt
            text = item.get("goal") or item.get("prompt")
            if text and len(str(text).strip()) > 0:
                samples.append({
                    "text": str(text),
                    "label": "novel"  # Mapping jailbreak/attack to novel
                })
                count += 1
        
        return samples
    except Exception as e:
        raise RuntimeError(f"Failed to fetch AdvBench sample: {e}")


def fetch_hf4_sample(n_samples: int = 500) -> List[Dict[str, Any]]:
    """
    Fetch a sample of safe logs from HF4 (or similar benign dataset).
    Returns list of dicts with 'text' and 'label'='benign'.
    Note: 'hf4' usually refers to a specific safety benchmark. 
    Using 'big-bench' or a generic safe prompt dataset if 'hf4' is not a standard HF name.
    Based on task T012a context, we assume a dataset exists that provides safe prompts.
    If 'hf4' is a specific custom dataset, we might need a specific ID. 
    Assuming 'HuggingFaceH4/ultrachat_200k' or similar safe conversational data as a proxy for 'benign' 
    if a specific 'hf4' dataset ID isn't standard. 
    However, the task description says 'fetch_hf4'. Let's try to load a known safe dataset 
    often used in these contexts, e.g., 'HuggingFaceH4/ultrachat_200k' (safe responses) 
    or a specific safety dataset like 'allenai/dolma' (filtered).
    
    Given the ambiguity of 'hf4' as a direct dataset name on HF hub without a specific org, 
    and the context of 'safe' logs, we will use 'HuggingFaceH4/ultrachat_200k' 
    which contains safe, helpful conversations. We will sample the 'prompt' or 'messages'.
    """
    try:
        # Attempt to load a representative safe dataset
        # Using ultrachat as a proxy for 'benign' user inputs if 'hf4' is not a direct ID.
        # If the project expects a specific 'hf4' dataset, the user should have defined it.
        # We'll try 'HuggingFaceH4/ultrachat_200k'
        dataset = load_dataset("HuggingFaceH4/ultrachat_200k", split="train", streaming=True)
        
        samples = []
        count = 0
        for item in dataset:
            if count >= n_samples:
                break
            
            # ultrachat has 'messages' list. We take the first user message.
            messages = item.get("messages", [])
            if messages and len(messages) > 0:
                # First message is usually user
                text = messages[0].get("content")
                if text and len(str(text).strip()) > 0:
                    samples.append({
                        "text": str(text),
                        "label": "benign"
                    })
                    count += 1
        
        if not samples:
            # Fallback if ultrachat structure is different or empty
            raise RuntimeError("No samples found in the dataset.")
            
        return samples
    except Exception as e:
        raise RuntimeError(f"Failed to fetch HF4 (benign) sample: {e}")


def generate_log_id(text: str, label: str) -> str:
    """
    Generate a deterministic UUID based on text and label.
    """
    data_str = f"{text}:{label}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, data_str))


def generate_static_fixture() -> str:
    """
    Main logic to generate the static test fixture.
    Returns the path to the generated JSON file.
    """
    ensure_directories()
    output_path = get_path("data/test_static_logs.json")
    
    print("Fetching AdvBench (novel) samples...")
    novel_samples = fetch_advbench_sample(n_samples=500)
    
    print("Fetching HF4 (benign) samples...")
    benign_samples = fetch_hf4_sample(n_samples=500)
    
    all_logs = []
    
    # Process novel samples
    for item in novel_samples:
        log_id = generate_log_id(item["text"], item["label"])
        all_logs.append({
            "log_id": log_id,
            "text": item["text"],
            "label": item["label"]
        })
    
    # Process benign samples
    for item in benign_samples:
        log_id = generate_log_id(item["text"], item["label"])
        all_logs.append({
            "log_id": log_id,
            "text": item["text"],
            "label": item["label"]
        })
    
    # Write to file
    print(f"Writing {len(all_logs)} logs to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_logs, f, indent=2, ensure_ascii=False)
    
    print(f"Static fixture generated successfully at {output_path}")
    return output_path


def main():
    """Entry point for script execution."""
    try:
        output_path = generate_static_fixture()
        # Verify file exists and is valid JSON
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file not created: {output_path}")
        
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Generated fixture is empty or not a list.")
        
        # Check schema
        required_keys = {"log_id", "text", "label"}
        if not required_keys.issubset(set(data[0].keys())):
            raise ValueError(f"Missing required keys. Found: {data[0].keys()}, Expected: {required_keys}")
        
        print("Validation passed.")
    except Exception as e:
        print(f"Error generating fixture: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
