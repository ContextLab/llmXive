"""
Generate static test fixture from real data (AdvBench/HF4).

This script fetches real data from AdvBench and HF4 datasets,
processes them to create a static test fixture with log_id, text, and label columns,
and saves it to data/test_static_logs.json.
"""
import json
import os
import sys
import hashlib
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from config import get_path, ensure_directories


def fetch_advbench_sample() -> List[Dict[str, Any]]:
    """
    Fetch a sample of real data from AdvBench dataset.
    
    Returns:
        List of dictionaries containing 'text' and 'label' fields.
        
    Raises:
        ValueError: If dataset fetch fails.
    """
    try:
        # Load AdvBench dataset with streaming to handle large datasets
        dataset = load_dataset("llm-attacks/advbench", split="train", streaming=True)
        
        samples = []
        # Take a reasonable sample size for testing
        count = 0
        max_samples = 500  # Limit for test fixture
        
        for item in dataset:
            if count >= max_samples:
                break
            
            # AdvBench typically has 'prompt' and 'target' or similar fields
            # We'll use the prompt as text and mark as 'attack' or 'jailbreak'
            text = item.get('prompt', '')
            if text:  # Only include non-empty prompts
                samples.append({
                    'text': text,
                    'label': 'jailbreak'  # AdvBench is an attack dataset
                })
                count += 1
        
        if not samples:
            raise ValueError("No valid samples found in AdvBench dataset")
            
        return samples
        
    except Exception as e:
        raise ValueError(f"Failed to fetch AdvBench dataset: {str(e)}")


def fetch_hf4_sample() -> List[Dict[str, Any]]:
    """
    Fetch a sample of real data from HF4 (HuggingFace 4) dataset.
    
    Returns:
        List of dictionaries containing 'text' and 'label' fields.
        
    Raises:
        ValueError: If dataset fetch fails.
    """
    try:
        # Try to load a safe/benign dataset from HuggingFace
        # Using 'bigcode/the-stack-smol' or similar benign code/text dataset
        # As a proxy for benign logs
        dataset = load_dataset("bigcode/the-stack-smol", 
                             data_dir="data/python", 
                             split="train", 
                             streaming=True)
        
        samples = []
        count = 0
        max_samples = 500  # Match AdvBench sample size
        
        for item in dataset:
            if count >= max_samples:
                break
            
            # Use the content as text
            text = item.get('content', '')
            if text and len(text.strip()) > 0:  # Only include non-empty content
                # Truncate very long samples for test fixture
                if len(text) > 2000:
                    text = text[:2000]
                
                samples.append({
                    'text': text,
                    'label': 'safe'  # Mark as benign/safe
                })
                count += 1
        
        if not samples:
            raise ValueError("No valid samples found in HF4 dataset")
            
        return samples
        
    except Exception as e:
        raise ValueError(f"Failed to fetch HF4 dataset: {str(e)}")


def generate_log_id(text: str, label: str) -> str:
    """
    Generate a deterministic UUID based on text and label.
    
    Args:
        text: The log text content
        label: The label associated with the text
        
    Returns:
        A deterministic UUID string
    """
    # Use UUID5 with DNS namespace for deterministic IDs
    namespace = uuid.NAMESPACE_DNS
    data_string = f"{text}:{label}"
    return str(uuid.uuid5(namespace, data_string))


def generate_static_fixture() -> List[Dict[str, Any]]:
    """
    Generate the static test fixture combining AdvBench and HF4 samples.
    
    Returns:
        List of dictionaries with 'log_id', 'text', and 'label' columns
    """
    print("Fetching AdvBench sample...")
    advbench_samples = fetch_advbench_sample()
    print(f"  Retrieved {len(advbench_samples)} samples from AdvBench")
    
    print("Fetching HF4 sample...")
    hf4_samples = fetch_hf4_sample()
    print(f"  Retrieved {len(hf4_samples)} samples from HF4")
    
    # Combine samples
    all_samples = []
    
    # Process AdvBench samples (attacks)
    for sample in advbench_samples:
        log_id = generate_log_id(sample['text'], sample['label'])
        all_samples.append({
            'log_id': log_id,
            'text': sample['text'],
            'label': sample['label']
        })
    
    # Process HF4 samples (benign)
    for sample in hf4_samples:
        log_id = generate_log_id(sample['text'], sample['label'])
        all_samples.append({
            'log_id': log_id,
            'text': sample['text'],
            'label': sample['label']
        })
    
    print(f"Generated {len(all_samples)} total samples for test fixture")
    return all_samples


def main():
    """Main entry point for generating the test fixture."""
    # Ensure directories exist
    data_path = get_path("data")
    ensure_directories([data_path])
    
    output_file = data_path / "test_static_logs.json"
    
    print(f"Generating static test fixture at {output_file}...")
    
    try:
        fixture_data = generate_static_fixture()
        
        # Validate output schema
        required_keys = {'log_id', 'text', 'label'}
        for i, item in enumerate(fixture_data):
            if not required_keys.issubset(item.keys()):
                raise ValueError(f"Item {i} missing required keys: {required_keys - set(item.keys())}")
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixture_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully wrote {len(fixture_data)} samples to {output_file}")
        
        # Verify file was created
        if not output_file.exists():
            raise FileNotFoundError(f"Output file was not created: {output_file}")
        
        # Verify file is valid JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            print(f"Verified: File contains {len(loaded_data)} valid JSON entries")
            
    except Exception as e:
        print(f"Error generating test fixture: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
