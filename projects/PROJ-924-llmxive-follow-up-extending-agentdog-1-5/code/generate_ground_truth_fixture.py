"""
Generate REAL GROUND TRUTH fixture for US-01 MVP testing.

This script loads AdvBench (adversarial attacks) and labels them 'novel'.
It loads HF4 (safe logs) and labels them 'benign'.
It outputs a JSON list with keys: log_id (UUID), text (string), label (string).
"""

import json
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path if running directly
if "code" not in sys.path[0]:
    project_root = Path(__file__).resolve().parent.parent
    code_path = project_root / "code"
    if code_path.exists():
        sys.path.insert(0, str(code_path))

from datasets import load_dataset
from config import get_path, ensure_directories
from data_loader import LoudFailureError


def fetch_advbench_data(sample_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch AdvBench dataset and return a list of entries.
    Labels all as 'novel' (attack).
    """
    try:
        # AdvBench is typically available via HuggingFace datasets
        # Using the specific dataset ID if known, or a generic proxy if needed.
        # Based on T012a context, we assume the dataset is accessible.
        ds = load_dataset("llm-attacks/advbench", split="train", streaming=True)
        
        entries = []
        count = 0
        for item in ds:
            if count >= sample_size:
                break
            
            # AdvBench structure usually has 'prompt' or 'input'
            # We take the 'prompt' field as the text
            text = item.get("prompt", "")
            if not text or not isinstance(text, str):
                continue
            
            entries.append({
                "text": text,
                "label": "novel"
            })
            count += 1
        
        if count == 0:
            raise ValueError("No valid entries found in AdvBench dataset.")
            
        return entries
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch AdvBench data: {e}") from e


def fetch_benign_data(sample_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch HF4 (safe logs) dataset and return a list of entries.
    Labels all as 'benign'.
    """
    try:
        # HF4 is a known safe log dataset in this project context
        # Assuming it's available as a dataset on HuggingFace
        ds = load_dataset("AgentDoG/hf4_safe_logs", split="train", streaming=True)
        
        entries = []
        count = 0
        for item in ds:
            if count >= sample_size:
                break
            
            # HF4 structure usually has 'text' or 'log'
            text = item.get("text", item.get("log", ""))
            if not text or not isinstance(text, str):
                continue
            
            entries.append({
                "text": text,
                "label": "benign"
            })
            count += 1
        
        if count == 0:
            raise ValueError("No valid entries found in HF4 dataset.")
            
        return entries
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 data: {e}") from e


def generate_log_id() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def generate_ground_truth_fixture(
    advbench_sample_size: int = 500,
    hf4_sample_size: int = 500,
    output_path: Path = None
) -> List[Dict[str, Any]]:
    """
    Generate the real ground truth fixture.
    
    Args:
        advbench_sample_size: Number of AdvBench entries to include.
        hf4_sample_size: Number of HF4 entries to include.
        output_path: Path to save the JSON file.
        
    Returns:
        List of dictionaries with log_id, text, and label.
    """
    if output_path is None:
        output_path = get_path("test", "real_ground_truth_fixture.json")
    
    ensure_directories([output_path.parent])
    
    print(f"Fetching {advbench_sample_size} AdvBench entries (novel)...")
    advbench_entries = fetch_advbench_data(advbench_sample_size)
    
    print(f"Fetching {hf4_sample_size} HF4 entries (benign)...")
    hf4_entries = fetch_benign_data(hf4_sample_size)
    
    # Combine and assign log_ids
    ground_truth = []
    
    for entry in advbench_entries:
        ground_truth.append({
            "log_id": generate_log_id(),
            "text": entry["text"],
            "label": entry["label"]
        })
        
    for entry in hf4_entries:
        ground_truth.append({
            "log_id": generate_log_id(),
            "text": entry["text"],
            "label": entry["label"]
        })
    
    # Shuffle the combined list to mix novel and benign
    import random
    random.shuffle(ground_truth)
    
    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)
    
    print(f"Ground truth fixture saved to: {output_path}")
    print(f"Total entries: {len(ground_truth)} (Novel: {advbench_sample_size}, Benign: {hf4_sample_size})")
    
    return ground_truth


def main():
    """Main entry point."""
    try:
        generate_ground_truth_fixture()
    except LoudFailureError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
