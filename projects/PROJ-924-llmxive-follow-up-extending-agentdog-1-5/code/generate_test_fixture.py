"""
Module to generate static test fixtures from real data sources (AdvBench/HF4).
This script fetches real data and writes a static JSONL file for US-01 testing.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import hashlib

# Import real data fetchers from the data_loader module
from data_loader import fetch_advbench, fetch_hf4
from config import get_path, ensure_directories
from utils import save_json_file


def generate_static_fixture(output_path: str, sample_size_advbench: int = 50, sample_size_hf4: int = 50) -> str:
    """
    Generates a static test fixture file containing logs from AdvBench and HF4.
    
    The output file is a JSONL file where each line is a JSON object with:
    - log_id: Unique identifier (string)
    - text: The log text (string)
    - label: The label (string: 'benign' or 'attack')
    
    Args:
        output_path: Path to the output JSONL file.
        sample_size_advbench: Number of samples to take from AdvBench (default 50).
        sample_size_hf4: Number of samples to take from HF4 (default 50).
        
    Returns:
        The path to the generated file.
        
    Raises:
        RuntimeError: If the real data fetch fails or data sources are unavailable.
    """
    ensure_directories()
    
    # Fetch real data from AdvBench (Attack logs)
    # AdvBench is a dataset of adversarial prompts, so these are 'attack' labeled
    try:
        advbench_data = fetch_advbench(streaming=True)
        # Take a sample to keep the fixture size manageable but representative
        advbench_samples = []
        count = 0
        for item in advbench_data:
            if count >= sample_size_advbench:
                break
            # AdvBench typically has 'text' or 'prompt' fields. 
            # We assume the dataset structure from HuggingFace `llm-attack/advbench`
            # which usually has a 'prompt' column. We map it to 'text'.
            # If the dataset structure varies, we adapt.
            text_val = item.get('text') or item.get('prompt')
            if text_val:
                advbench_samples.append({
                    'text': text_val,
                    'label': 'attack'
                })
                count += 1
    except Exception as e:
        raise RuntimeError(f"Failed to fetch AdvBench real data: {e}") from e

    if not advbench_samples:
        raise RuntimeError("AdvBench fetch returned no data samples.")

    # Fetch real data from HF4 (Benign logs)
    # Assuming HF4 is a dataset of benign conversations or logs.
    # We use the `fetch_hf4` function which should point to a specific dataset.
    # If `fetch_hf4` is designed to return benign data, we use it directly.
    try:
        hf4_data = fetch_hf4(streaming=True)
        hf4_samples = []
        count = 0
        for item in hf4_data:
            if count >= sample_size_hf4:
                break
            text_val = item.get('text') or item.get('prompt') or item.get('conversation')
            if text_val:
                hf4_samples.append({
                    'text': text_val,
                    'label': 'benign'
                })
                count += 1
    except Exception as e:
        raise RuntimeError(f"Failed to fetch HF4 real data: {e}") from e

    if not hf4_samples:
        raise RuntimeError("HF4 fetch returned no data samples.")

    # Combine and assign log_ids
    all_logs = []
    
    # Process AdvBench samples
    for i, sample in enumerate(advbench_samples):
        log_id = f"advbench_{i:04d}"
        all_logs.append({
            'log_id': log_id,
            'text': sample['text'],
            'label': sample['label']
        })

    # Process HF4 samples
    for i, sample in enumerate(hf4_samples):
        log_id = f"hf4_{i:04d}"
        all_logs.append({
            'log_id': log_id,
            'text': sample['text'],
            'label': sample['label']
        })

    # Write to file
    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for log in all_logs:
            f.write(json.dumps(log, ensure_ascii=False) + '\n')

    return output_path


def main():
    """Main entry point for generating the static test fixture."""
    # Define the output path relative to the project root
    # The task requires: data/test_static_logs.json
    # Based on plan.md, data directory is `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/`
    # We use the config helper to get the correct path
    try:
        # Ensure the data directory exists
        data_dir = get_path('data')
        ensure_directories() # This should create data/test if needed, but we need data/test_static_logs.json
        
        output_path = os.path.join(data_dir, 'test_static_logs.json')
        
        print(f"Generating static test fixture at: {output_path}")
        result_path = generate_static_fixture(output_path)
        print(f"Successfully generated fixture: {result_path}")
        
    except Exception as e:
        print(f"Error generating fixture: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()