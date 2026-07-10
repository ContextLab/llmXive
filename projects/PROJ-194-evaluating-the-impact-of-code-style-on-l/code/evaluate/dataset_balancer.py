import json
import csv
import os
import random
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

# Constants for file paths relative to project root
BASELINE_PATH = "data/derived/baseline.json"
MUTATED_PATH = "data/derived/mutated.json"
OUTPUT_PATH = "data/derived/balanced_dataset.csv"

def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        List of dictionaries representing the JSON data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure we always return a list
    if isinstance(data, dict):
        return [data]
    return data

def determine_ground_truth(sample: Dict[str, Any]) -> bool:
    """
    Determine if a sample is buggy based on the presence of mutation metadata.
    
    Logic:
        - If the sample has a 'mutation_type' key (from T022), it is buggy.
        - Otherwise, it is considered clean.
        
    Args:
        sample: A dictionary representing a code variant.
        
    Returns:
        True if the sample is buggy, False otherwise.
    """
    return 'mutation_type' in sample and sample['mutation_type'] is not None

def build_balanced_dataset(clean_samples: List[Dict[str, Any]], 
                           buggy_samples: List[Dict[str, Any]], 
                           seed: int = 42) -> List[Dict[str, Any]]:
    """
    Construct a balanced dataset with 50/50 clean and buggy samples.
    
    Args:
        clean_samples: List of clean (non-mutated) variants.
        buggy_samples: List of mutated variants.
        seed: Random seed for reproducibility.
        
    Returns:
        A list of dictionaries containing the balanced dataset.
        Each entry includes a 'is_buggy' flag.
    """
    random.seed(seed)
    
    # Determine the target size (min of the two groups)
    target_size = min(len(clean_samples), len(buggy_samples))
    
    if target_size == 0:
        # If one group is empty, return the other group (or empty if both are)
        # In a strict 50/50 scenario, this might be an error condition, 
        # but we proceed with available data.
        pass
    
    # Randomly sample from each group
    sampled_clean = random.sample(clean_samples, target_size) if clean_samples else []
    sampled_buggy = random.sample(buggy_samples, target_size) if buggy_samples else []
    
    # Annotate samples
    for sample in sampled_clean:
        sample['is_buggy'] = False
        
    for sample in sampled_buggy:
        sample['is_buggy'] = True
        
    # Combine and shuffle
    balanced = sampled_clean + sampled_buggy
    random.shuffle(balanced)
    
    return balanced

def save_balanced_dataset(dataset: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the balanced dataset to a CSV file.
    
    Args:
        dataset: The list of balanced sample dictionaries.
        output_path: Path to the output CSV file.
    """
    if not dataset:
        # Write empty file with headers if dataset is empty
        headers = ['id', 'original_code', 'variant_id', 'is_buggy', 'mutation_type']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return

    # Determine headers dynamically based on keys found in the first item
    # Ensure standard columns are prioritized
    first_item = dataset[0]
    standard_keys = ['id', 'original_code', 'variant_id', 'is_buggy', 'mutation_type', 'style_flags']
    
    # Collect all unique keys
    all_keys = set()
    for item in dataset:
        all_keys.update(item.keys())
    
    # Order keys: standard first, then others
    ordered_headers = []
    for key in standard_keys:
        if key in all_keys:
            ordered_headers.append(key)
            all_keys.discard(key)
    
    ordered_headers.extend(sorted(list(all_keys)))
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=ordered_headers)
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)

def run_dataset_balancing(baseline_path: str = BASELINE_PATH, 
                          mutated_path: str = MUTATED_PATH, 
                          output_path: str = OUTPUT_PATH, 
                          seed: int = 42) -> Tuple[int, int, int]:
    """
    Main orchestration function to load, balance, and save the dataset.
    
    Args:
        baseline_path: Path to the clean baseline JSON.
        mutated_path: Path to the mutated JSON.
        output_path: Path to save the balanced CSV.
        seed: Random seed.
        
    Returns:
        Tuple of (clean_count, buggy_count, total_count)
    """
    print(f"Loading baseline data from {baseline_path}...")
    clean_data = load_json_data(baseline_path)
    
    print(f"Loading mutated data from {mutated_path}...")
    mutated_data = load_json_data(mutated_path)
    
    # Filter and categorize
    clean_samples = []
    buggy_samples = []
    
    # Process baseline (should all be clean)
    for item in clean_data:
        if not determine_ground_truth(item):
            clean_samples.append(item)
        else:
            # Unexpected: baseline has mutation metadata? Treat as buggy if so, 
            # though logically baseline should be clean.
            buggy_samples.append(item)
    
    # Process mutated (should all be buggy)
    for item in mutated_data:
        if determine_ground_truth(item):
            buggy_samples.append(item)
        else:
            # Unexpected: mutated data lacks mutation metadata? Treat as clean.
            clean_samples.append(item)
    
    print(f"Found {len(clean_samples)} clean samples and {len(buggy_samples)} buggy samples.")
    
    # Build balanced dataset
    balanced = build_balanced_dataset(clean_samples, buggy_samples, seed)
    
    # Save
    save_balanced_dataset(balanced, output_path)
    
    print(f"Balanced dataset saved to {output_path} with {len(balanced)} samples.")
    
    return len(clean_samples), len(buggy_samples), len(balanced)

def main():
    """Entry point for running the dataset balancer."""
    try:
        clean_count, buggy_count, total = run_dataset_balancing()
        print(f"Success: Created balanced dataset with {total} samples (Clean: {min(clean_count, buggy_count)}, Buggy: {min(clean_count, buggy_count)})")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure T022 (mutated.json) and the baseline generation step have completed.")
        raise
    except Exception as e:
        print(f"Error during balancing: {e}")
        raise

if __name__ == "__main__":
    main()